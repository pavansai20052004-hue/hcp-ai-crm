from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class HCPOut(BaseModel):
    id: int
    full_name: str
    specialty: str
    tier: str
    territory: str
    organization: str
    email: str
    preferred_channel: str
    persona_notes: str

    model_config = ConfigDict(from_attributes=True)


class InteractionBase(BaseModel):
    hcp_id: int
    occurred_at: datetime | None = None
    channel: str = "In person"
    interaction_type: str = "Detailing"
    summary: str | None = None
    raw_notes: str = ""
    sentiment: str | None = None
    topics: list[str] = Field(default_factory=list)
    products: list[str] = Field(default_factory=list)
    objections: list[str] = Field(default_factory=list)
    commitments: list[str] = Field(default_factory=list)
    compliance_flags: list[str] = Field(default_factory=list)
    call_quality_score: int | None = None
    ai_confidence: int | None = None
    follow_up_date: str | None = None
    follow_up_owner: str | None = None
    next_best_action: str | None = None


class InteractionCreate(InteractionBase):
    pass


class InteractionEdit(BaseModel):
    occurred_at: datetime | None = None
    channel: str | None = None
    interaction_type: str | None = None
    summary: str | None = None
    raw_notes: str | None = None
    sentiment: str | None = None
    topics: list[str] | None = None
    products: list[str] | None = None
    objections: list[str] | None = None
    commitments: list[str] | None = None
    compliance_flags: list[str] | None = None
    call_quality_score: int | None = None
    ai_confidence: int | None = None
    follow_up_date: str | None = None
    follow_up_owner: str | None = None
    next_best_action: str | None = None


class InteractionOut(InteractionBase):
    id: int
    occurred_at: datetime
    summary: str
    sentiment: str
    call_quality_score: int
    ai_confidence: int
    next_best_action: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AgentChatRequest(BaseModel):
    message: str
    hcp_id: int | None = None


class AgentToolRequest(BaseModel):
    hcp_id: int | None = None
    interaction_id: int | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class AgentResponse(BaseModel):
    tool_name: str
    result: dict[str, Any]
