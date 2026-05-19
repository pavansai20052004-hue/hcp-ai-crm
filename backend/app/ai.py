from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from typing import Any, Literal, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq
from langgraph.graph import END, StateGraph
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import HCP, Interaction


ToolName = Literal[
    "log_interaction",
    "edit_interaction",
    "get_hcp_profile",
    "suggest_next_best_action",
    "draft_follow_up",
    "compliance_review",
]


class AgentState(TypedDict, total=False):
    message: str
    tool_name: ToolName
    hcp_id: int | None
    interaction_id: int | None
    payload: dict[str, Any]
    result: dict[str, Any]


TOOL_DESCRIPTIONS: dict[str, str] = {
    "log_interaction": "Create an HCP interaction from structured fields or natural language notes.",
    "edit_interaction": "Modify an existing interaction after the representative corrects details.",
    "get_hcp_profile": "Retrieve profile context and recent interaction history for an HCP.",
    "suggest_next_best_action": "Recommend the next commercial action for the representative.",
    "draft_follow_up": "Draft a compliant follow-up email based on the latest interaction.",
    "compliance_review": "Check the latest interaction for off-label, adverse event, and follow-up risk signals.",
}


def _llm() -> ChatGroq | None:
    settings = get_settings()
    if not settings.groq_api_key or settings.groq_api_key.startswith("replace-"):
        return None
    return ChatGroq(
        model=settings.groq_model,
        api_key=settings.groq_api_key,
        temperature=0.2,
        max_tokens=700,
    )


def _clean_json(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    cleaned = re.sub(r"^```json\s*", "", cleaned)
    cleaned = re.sub(r"^```\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    return json.loads(cleaned)


def _invoke_json(system: str, user: str, fallback: dict[str, Any]) -> dict[str, Any]:
    model = _llm()
    if model is None:
        return fallback
    try:
        response = model.invoke([SystemMessage(content=system), HumanMessage(content=user)])
        return _clean_json(str(response.content))
    except Exception:
        return fallback


def _invoke_text(system: str, user: str, fallback: str) -> str:
    model = _llm()
    if model is None:
        return fallback
    try:
        response = model.invoke([SystemMessage(content=system), HumanMessage(content=user)])
        return str(response.content).strip()
    except Exception:
        return fallback


def _interaction_to_dict(interaction: Interaction) -> dict[str, Any]:
    return {
        "id": interaction.id,
        "hcp_id": interaction.hcp_id,
        "occurred_at": interaction.occurred_at.isoformat(),
        "channel": interaction.channel,
        "interaction_type": interaction.interaction_type,
        "summary": interaction.summary,
        "raw_notes": interaction.raw_notes,
        "sentiment": interaction.sentiment,
        "topics": interaction.topics or [],
        "products": interaction.products or [],
        "objections": interaction.objections or [],
        "commitments": interaction.commitments or [],
        "compliance_flags": interaction.compliance_flags or [],
        "call_quality_score": interaction.call_quality_score,
        "ai_confidence": interaction.ai_confidence,
        "follow_up_date": interaction.follow_up_date,
        "follow_up_owner": interaction.follow_up_owner,
        "next_best_action": interaction.next_best_action,
        "created_at": interaction.created_at.isoformat(),
        "updated_at": interaction.updated_at.isoformat(),
    }


def _hcp_to_dict(hcp: HCP) -> dict[str, Any]:
    return {
        "id": hcp.id,
        "full_name": hcp.full_name,
        "specialty": hcp.specialty,
        "tier": hcp.tier,
        "territory": hcp.territory,
        "organization": hcp.organization,
        "email": hcp.email,
        "preferred_channel": hcp.preferred_channel,
        "persona_notes": hcp.persona_notes,
    }


def _get_hcp(db: Session, hcp_id: int | None) -> HCP:
    if hcp_id is None:
        hcp = db.query(HCP).order_by(HCP.id).first()
    else:
        hcp = db.get(HCP, hcp_id)
    if not hcp:
        raise ValueError("HCP not found")
    return hcp


def _latest_interaction(db: Session, hcp_id: int | None) -> Interaction | None:
    query = db.query(Interaction).order_by(Interaction.occurred_at.desc())
    if hcp_id:
        query = query.filter(Interaction.hcp_id == hcp_id)
    return query.first()


def _extract_payload(message: str, hcp_id: int | None) -> dict[str, Any]:
    lowered = message.lower()
    fallback_tool: ToolName = "log_interaction"
    if "edit" in lowered or "change" in lowered or "correct" in lowered:
        fallback_tool = "edit_interaction"
    elif "profile" in lowered or "history" in lowered:
        fallback_tool = "get_hcp_profile"
    elif "compliance" in lowered or "off-label" in lowered or "adverse" in lowered:
        fallback_tool = "compliance_review"
    elif "next" in lowered or "recommend" in lowered or "action" in lowered:
        fallback_tool = "suggest_next_best_action"
    elif "email" in lowered or "follow-up" in lowered or "follow up" in lowered:
        fallback_tool = "draft_follow_up"

    fallback = {
        "tool_name": fallback_tool,
        "hcp_id": hcp_id,
        "payload": {"raw_notes": message, "channel": "In person", "interaction_type": "Detailing"},
    }

    system = (
        "You route CRM field representative messages to tools. Return only JSON with keys "
        "tool_name, hcp_id, interaction_id, and payload. Valid tool names are: "
        f"{', '.join(TOOL_DESCRIPTIONS)}."
    )
    user = f"Current hcp_id: {hcp_id}\nMessage: {message}"
    parsed = _invoke_json(system, user, fallback)
    parsed.setdefault("hcp_id", hcp_id)
    parsed.setdefault("payload", {})
    return parsed


def _enrich_interaction(hcp: HCP, payload: dict[str, Any]) -> dict[str, Any]:
    notes = payload.get("raw_notes") or payload.get("notes") or payload.get("summary") or ""
    fallback_summary = payload.get("summary") or (notes[:180] if notes else "Interaction logged.")
    fallback = {
        "summary": fallback_summary,
        "sentiment": payload.get("sentiment") or "Neutral",
        "topics": payload.get("topics") or ["clinical discussion"],
        "products": payload.get("products") or [],
        "objections": payload.get("objections") or _simple_list_extract(notes, ["concern", "objection", "barrier", "asked"]),
        "commitments": payload.get("commitments") or _simple_commitments(notes),
        "compliance_flags": payload.get("compliance_flags") or _detect_compliance_flags(notes),
        "call_quality_score": payload.get("call_quality_score") or _score_interaction(notes, payload),
        "ai_confidence": payload.get("ai_confidence") or 78,
        "next_best_action": payload.get("next_best_action")
        or "Send relevant resources and schedule the next HCP touchpoint.",
    }
    system = (
        "You are an AI assistant inside a life-sciences CRM. Extract concise, compliant CRM data. "
        "Return only JSON with summary, sentiment, topics, products, objections, commitments, "
        "compliance_flags, call_quality_score, ai_confidence, and next_best_action. "
        "Do not invent claims, dosage, or off-label statements. Flag adverse events, off-label requests, "
        "samples, and patient-identifiable information."
    )
    user = (
        f"HCP: {hcp.full_name}, {hcp.specialty}, tier {hcp.tier}. "
        f"Persona notes: {hcp.persona_notes}\nInteraction payload: {json.dumps(payload)}"
    )
    enriched = _invoke_json(system, user, fallback)
    return {**fallback, **enriched}


def _simple_list_extract(notes: str, cues: list[str]) -> list[str]:
    if not notes:
        return []
    sentences = re.split(r"(?<=[.!?])\s+", notes)
    return [sentence.strip() for sentence in sentences if any(cue in sentence.lower() for cue in cues)][:3]


def _simple_commitments(notes: str) -> list[str]:
    if not notes:
        return []
    cues = ["send", "share", "schedule", "follow", "provide", "confirm"]
    sentences = re.split(r"(?<=[.!?])\s+", notes)
    return [sentence.strip() for sentence in sentences if any(cue in sentence.lower() for cue in cues)][:3]


def _detect_compliance_flags(notes: str) -> list[str]:
    lowered = notes.lower()
    flags: list[str] = []
    off_label_mentioned = "off-label" in lowered or "off label" in lowered
    off_label_negated = "no off-label" in lowered or "no off label" in lowered or "not off-label" in lowered
    if off_label_mentioned and not off_label_negated:
        flags.append("Potential off-label request")
    if "adverse event" in lowered or "side effect" in lowered or "reaction" in lowered:
        flags.append("Potential adverse event follow-up needed")
    if "sample" in lowered:
        flags.append("Sample request requires policy check")
    pii_terms = ["mrn", "phone number", "aadhaar", "patient name", "patient address", "patient phone"]
    if any(term in lowered for term in pii_terms):
        flags.append("Possible patient-identifiable information")
    return flags


def _score_interaction(notes: str, payload: dict[str, Any]) -> int:
    score = 52
    if len(notes) > 80:
        score += 12
    if payload.get("products"):
        score += 8
    if payload.get("topics"):
        score += 8
    if payload.get("follow_up_date"):
        score += 10
    if _simple_commitments(notes):
        score += 8
    if _detect_compliance_flags(notes):
        score -= 12
    return max(1, min(100, score))


def _as_score(value: Any, fallback: int) -> int:
    try:
        if isinstance(value, str):
            value = re.sub(r"[^0-9]", "", value)
        return max(1, min(100, int(value)))
    except (TypeError, ValueError):
        return fallback


def log_interaction_tool(db: Session, state: AgentState) -> dict[str, Any]:
    payload = state.get("payload", {})
    hcp = _get_hcp(db, payload.get("hcp_id") or state.get("hcp_id"))
    enriched = _enrich_interaction(hcp, payload)

    occurred_at = payload.get("occurred_at")
    if isinstance(occurred_at, str):
        occurred_at_dt = datetime.fromisoformat(occurred_at.replace("Z", "+00:00"))
    else:
        occurred_at_dt = occurred_at or datetime.now(UTC)

    interaction = Interaction(
        hcp_id=hcp.id,
        occurred_at=occurred_at_dt,
        channel=payload.get("channel") or "In person",
        interaction_type=payload.get("interaction_type") or "Detailing",
        summary=enriched["summary"],
        raw_notes=payload.get("raw_notes") or payload.get("notes") or enriched["summary"],
        sentiment=enriched["sentiment"],
        topics=enriched.get("topics") or [],
        products=enriched.get("products") or payload.get("products") or [],
        objections=enriched.get("objections") or [],
        commitments=enriched.get("commitments") or [],
        compliance_flags=enriched.get("compliance_flags") or [],
        call_quality_score=_as_score(enriched.get("call_quality_score"), 70),
        ai_confidence=_as_score(enriched.get("ai_confidence"), 75),
        follow_up_date=payload.get("follow_up_date"),
        follow_up_owner=payload.get("follow_up_owner") or "Field Rep",
        next_best_action=enriched["next_best_action"],
    )
    db.add(interaction)
    db.commit()
    db.refresh(interaction)
    return {
        "message": "Interaction logged",
        "interaction": _interaction_to_dict(interaction),
        "ai_enrichment": enriched,
    }


def edit_interaction_tool(db: Session, state: AgentState) -> dict[str, Any]:
    payload = state.get("payload", {})
    interaction_id = state.get("interaction_id") or payload.get("interaction_id")
    interaction = db.get(Interaction, interaction_id) if interaction_id else _latest_interaction(db, state.get("hcp_id"))
    if not interaction:
        raise ValueError("Interaction not found")

    allowed = {
        "occurred_at",
        "channel",
        "interaction_type",
        "summary",
        "raw_notes",
        "sentiment",
        "topics",
        "products",
        "objections",
        "commitments",
        "compliance_flags",
        "call_quality_score",
        "ai_confidence",
        "follow_up_date",
        "follow_up_owner",
        "next_best_action",
    }
    for key, value in payload.items():
        if key not in allowed or value is None:
            continue
        if key == "occurred_at" and isinstance(value, str):
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        setattr(interaction, key, value)

    interaction.updated_at = datetime.now(UTC)
    db.commit()
    db.refresh(interaction)
    return {"message": "Interaction updated", "interaction": _interaction_to_dict(interaction)}


def get_hcp_profile_tool(db: Session, state: AgentState) -> dict[str, Any]:
    hcp = _get_hcp(db, state.get("hcp_id"))
    recent = (
        db.query(Interaction)
        .filter(Interaction.hcp_id == hcp.id)
        .order_by(Interaction.occurred_at.desc())
        .limit(3)
        .all()
    )
    return {"hcp": _hcp_to_dict(hcp), "recent_interactions": [_interaction_to_dict(item) for item in recent]}


def suggest_next_best_action_tool(db: Session, state: AgentState) -> dict[str, Any]:
    profile = get_hcp_profile_tool(db, state)
    hcp = profile["hcp"]
    recent = profile["recent_interactions"]
    fallback = (
        f"Prioritize a concise {hcp['preferred_channel'].lower()} follow-up for {hcp['full_name']} "
        "with evidence aligned to the last discussion, then schedule the next in-person visit."
    )
    system = (
        "You are a life-sciences sales operations assistant. Recommend one compliant next best action. "
        "Keep it practical for a field representative and avoid medical claims."
    )
    user = json.dumps({"hcp": hcp, "recent_interactions": recent}, indent=2)
    recommendation = _invoke_text(system, user, fallback)
    return {"hcp": hcp, "recommendation": recommendation}


def draft_follow_up_tool(db: Session, state: AgentState) -> dict[str, Any]:
    hcp = _get_hcp(db, state.get("hcp_id"))
    latest = _latest_interaction(db, hcp.id)
    fallback_body = (
        f"Dear {hcp.full_name},\n\n"
        "Thank you for your time during our recent discussion. I will share the resources we discussed "
        "and remain available for any follow-up questions.\n\n"
        "Best regards,\nField Representative"
    )
    system = (
        "Draft a short, compliant follow-up email for a field representative. "
        "Do not include promotional claims not present in the interaction summary."
    )
    user = json.dumps(
        {
            "hcp": _hcp_to_dict(hcp),
            "latest_interaction": _interaction_to_dict(latest) if latest else None,
        },
        indent=2,
    )
    body = _invoke_text(system, user, fallback_body)
    return {
        "hcp": _hcp_to_dict(hcp),
        "subject": f"Follow-up from our recent discussion",
        "body": body,
        "source_interaction_id": latest.id if latest else None,
    }


def compliance_review_tool(db: Session, state: AgentState) -> dict[str, Any]:
    hcp = _get_hcp(db, state.get("hcp_id"))
    latest = _latest_interaction(db, hcp.id)
    if not latest:
        return {
            "hcp": _hcp_to_dict(hcp),
            "status": "No interaction available",
            "flags": [],
            "recommended_action": "Log an interaction before running compliance review.",
        }

    flags = latest.compliance_flags or _detect_compliance_flags(f"{latest.summary} {latest.raw_notes}")
    status = "Needs review" if flags else "Clear for standard follow-up"
    recommended_action = (
        "Escalate the flagged item to compliance or medical information before follow-up."
        if flags
        else "Proceed with approved materials and keep the follow-up factual."
    )
    return {
        "hcp": _hcp_to_dict(hcp),
        "interaction": _interaction_to_dict(latest),
        "status": status,
        "flags": flags,
        "recommended_action": recommended_action,
    }


TOOL_FUNCTIONS = {
    "log_interaction": log_interaction_tool,
    "edit_interaction": edit_interaction_tool,
    "get_hcp_profile": get_hcp_profile_tool,
    "suggest_next_best_action": suggest_next_best_action_tool,
    "draft_follow_up": draft_follow_up_tool,
    "compliance_review": compliance_review_tool,
}


def build_agent(db: Session):
    graph = StateGraph(AgentState)

    def route_node(state: AgentState) -> AgentState:
        if state.get("tool_name"):
            return state
        parsed = _extract_payload(state.get("message", ""), state.get("hcp_id"))
        return {
            **state,
            "tool_name": parsed.get("tool_name", "log_interaction"),
            "hcp_id": parsed.get("hcp_id") or state.get("hcp_id"),
            "interaction_id": parsed.get("interaction_id"),
            "payload": parsed.get("payload", {}),
        }

    def execute_node(state: AgentState) -> AgentState:
        tool_name = state.get("tool_name", "log_interaction")
        if tool_name not in TOOL_FUNCTIONS:
            raise ValueError(f"Unknown tool: {tool_name}")
        result = TOOL_FUNCTIONS[tool_name](db, state)
        return {**state, "result": result}

    graph.add_node("route", route_node)
    graph.add_node("execute_tool", execute_node)
    graph.set_entry_point("route")
    graph.add_edge("route", "execute_tool")
    graph.add_edge("execute_tool", END)
    return graph.compile()


def run_agent(
    db: Session,
    *,
    message: str = "",
    tool_name: ToolName | None = None,
    hcp_id: int | None = None,
    interaction_id: int | None = None,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    agent = build_agent(db)
    state: AgentState = {
        "message": message,
        "hcp_id": hcp_id,
        "interaction_id": interaction_id,
        "payload": payload or {},
    }
    if tool_name:
        state["tool_name"] = tool_name
    final_state = agent.invoke(state)
    return {"tool_name": final_state["tool_name"], "result": final_state["result"]}
