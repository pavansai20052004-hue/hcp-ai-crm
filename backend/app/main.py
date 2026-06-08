from contextlib import asynccontextmanager
from time import perf_counter

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from sqlalchemy.orm import Session

from app.ai import TOOL_DESCRIPTIONS, ToolName, run_agent
from app.config import get_settings
from app.db import check_db, get_db, init_db
from app.models import HCP, Interaction
from app.schemas import (
    AgentChatRequest,
    AgentResponse,
    AgentToolRequest,
    HCPOut,
    InteractionCreate,
    InteractionEdit,
    InteractionOut,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


settings = get_settings()
app = FastAPI(title=settings.app_name, version=settings.app_version, lifespan=lifespan)

app.add_middleware(GZipMiddleware, minimum_size=1000)
if settings.trusted_host_list:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.trusted_host_list)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_origin_regex=settings.cors_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_platform_headers(request: Request, call_next):
    started = perf_counter()
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers["X-Process-Time-Ms"] = f"{(perf_counter() - started) * 1000:.2f}"
    return response


@app.get("/")
def root() -> dict[str, str | bool]:
    return {
        "message": "AI-First HCP CRM backend is running",
        "version": settings.app_version,
        "environment": settings.environment,
        "demo_seed_enabled": settings.seed_demo_data,
        "health": "/health",
        "ready": "/ready",
        "docs": "/docs",
        "hcps": "/hcps",
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "model": settings.groq_model}


@app.get("/ready")
def ready() -> dict[str, str | bool]:
    try:
        db_ready = check_db()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Database not ready: {exc}") from exc
    return {"status": "ready", "database": db_ready, "model": settings.groq_model}


@app.get("/agent/tools")
def list_agent_tools() -> dict[str, str]:
    return TOOL_DESCRIPTIONS


@app.get("/hcps", response_model=list[HCPOut])
def list_hcps(db: Session = Depends(get_db)) -> list[HCP]:
    return db.query(HCP).order_by(HCP.full_name).all()


@app.get("/hcps/{hcp_id}", response_model=HCPOut)
def get_hcp(hcp_id: int, db: Session = Depends(get_db)) -> HCP:
    hcp = db.get(HCP, hcp_id)
    if not hcp:
        raise HTTPException(status_code=404, detail="HCP not found")
    return hcp


@app.get("/interactions", response_model=list[InteractionOut])
def list_interactions(
    hcp_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[Interaction]:
    query = db.query(Interaction).order_by(Interaction.occurred_at.desc())
    if hcp_id:
        query = query.filter(Interaction.hcp_id == hcp_id)
    return query.all()


@app.get("/insights/summary")
def interaction_insights(hcp_id: int | None = Query(default=None), db: Session = Depends(get_db)) -> dict:
    query = db.query(Interaction)
    if hcp_id:
        query = query.filter(Interaction.hcp_id == hcp_id)
    interactions = query.all()
    total = len(interactions)
    flagged = sum(1 for item in interactions if item.compliance_flags)
    avg_quality = round(sum(item.call_quality_score for item in interactions) / total) if total else 0
    topics: dict[str, int] = {}
    for item in interactions:
        for topic in item.topics or []:
            topics[topic] = topics.get(topic, 0) + 1
    top_topics = sorted(topics.items(), key=lambda pair: pair[1], reverse=True)[:4]
    return {
        "total_interactions": total,
        "flagged_interactions": flagged,
        "average_quality_score": avg_quality,
        "top_topics": [{"name": name, "count": count} for name, count in top_topics],
    }


@app.post("/interactions", response_model=AgentResponse)
def create_interaction(payload: InteractionCreate, db: Session = Depends(get_db)) -> dict:
    try:
        return run_agent(
            db,
            tool_name="log_interaction",
            hcp_id=payload.hcp_id,
            payload=payload.model_dump(exclude_none=True),
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.patch("/interactions/{interaction_id}", response_model=AgentResponse)
def update_interaction(
    interaction_id: int,
    payload: InteractionEdit,
    db: Session = Depends(get_db),
) -> dict:
    try:
        return run_agent(
            db,
            tool_name="edit_interaction",
            interaction_id=interaction_id,
            payload=payload.model_dump(exclude_none=True),
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/agent/chat", response_model=AgentResponse)
def agent_chat(payload: AgentChatRequest, db: Session = Depends(get_db)) -> dict:
    try:
        return run_agent(db, message=payload.message, hcp_id=payload.hcp_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/agent/tools/{tool_name}", response_model=AgentResponse)
def run_tool(tool_name: ToolName, payload: AgentToolRequest, db: Session = Depends(get_db)) -> dict:
    try:
        return run_agent(
            db,
            tool_name=tool_name,
            hcp_id=payload.hcp_id,
            interaction_id=payload.interaction_id,
            payload=payload.payload,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
