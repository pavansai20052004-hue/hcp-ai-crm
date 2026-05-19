from datetime import UTC, datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def utc_now() -> datetime:
    return datetime.now(UTC)


class HCP(Base):
    __tablename__ = "hcps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    specialty: Mapped[str] = mapped_column(String(100), nullable=False)
    tier: Mapped[str] = mapped_column(String(20), nullable=False, default="B")
    territory: Mapped[str] = mapped_column(String(100), nullable=False)
    organization: Mapped[str] = mapped_column(String(160), nullable=False)
    email: Mapped[str] = mapped_column(String(160), nullable=False)
    preferred_channel: Mapped[str] = mapped_column(String(60), nullable=False, default="Email")
    persona_notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    interactions: Mapped[list["Interaction"]] = relationship(
        back_populates="hcp",
        cascade="all, delete-orphan",
        order_by="desc(Interaction.occurred_at)",
    )


class Interaction(Base):
    __tablename__ = "interactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    hcp_id: Mapped[int] = mapped_column(ForeignKey("hcps.id"), nullable=False, index=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)
    channel: Mapped[str] = mapped_column(String(50), nullable=False, default="In person")
    interaction_type: Mapped[str] = mapped_column(String(80), nullable=False, default="Detailing")
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    raw_notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    sentiment: Mapped[str] = mapped_column(String(30), nullable=False, default="Neutral")
    topics: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    products: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    objections: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    commitments: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    compliance_flags: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    call_quality_score: Mapped[int] = mapped_column(Integer, nullable=False, default=70)
    ai_confidence: Mapped[int] = mapped_column(Integer, nullable=False, default=75)
    follow_up_date: Mapped[str | None] = mapped_column(String(40), nullable=True)
    follow_up_owner: Mapped[str | None] = mapped_column(String(80), nullable=True)
    next_best_action: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    hcp: Mapped[HCP] = relationship(back_populates="interactions")
