"""
SBI Vishwas — Complaint Model

Complaint lifecycle with SLA tracking, escalation history, and resolution.
Directly supports Phase A — Escalation & Advocate Agent.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.config.constants import ComplaintCategory, ComplaintStatus, EscalationLevel
from src.database.base import BaseModel


class Complaint(BaseModel):
    """
    Customer complaint with full lifecycle tracking.

    SLA timers are tracked to enable auto-escalation by Agent 4,
    addressing the evidence of 6-month unresolved complaints.
    """

    __tablename__ = "complaints"
    __table_args__ = (
        Index("ix_complaints_customer_id", "customer_id"),
        Index("ix_complaints_status", "status"),
        Index("ix_complaints_branch_code", "branch_code"),
        Index("ix_complaints_sla_deadline", "sla_deadline"),
        Index("ix_complaints_category", "category"),
        Index("ix_complaints_escalation_level", "escalation_level"),
    )

    # Identity
    complaint_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False
    )

    # Classification
    category: Mapped[str] = mapped_column(
        String(50), default=ComplaintCategory.OTHER.value, nullable=False
    )
    subcategory: Mapped[str | None] = mapped_column(String(100), nullable=True)
    subject: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    # Source
    source_channel: Mapped[str] = mapped_column(String(50), nullable=False)
    branch_code: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Status & lifecycle
    status: Mapped[str] = mapped_column(
        String(50), default=ComplaintStatus.FILED.value, nullable=False
    )
    priority: Mapped[str] = mapped_column(String(20), default="medium", nullable=False)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolution_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # SLA tracking
    sla_deadline: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    sla_breached: Mapped[bool] = mapped_column(default=False, nullable=False, index=True)

    # Escalation
    escalation_level: Mapped[int] = mapped_column(
        Integer, default=EscalationLevel.BRANCH.value, nullable=False
    )
    last_escalated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    escalation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Assignment
    assigned_to_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    assigned_branch_code: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # AI analysis (from Diagnosis Agent)
    ai_classification: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ai_classification_confidence: Mapped[float | None] = mapped_column(nullable=True)
    ai_suggested_resolution: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_root_cause: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Policy deviation link (if complaint triggered by Policy Compliance Agent)
    policy_deviation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("policy_checks.id", ondelete="SET NULL"), nullable=True
    )

    # Satisfaction
    customer_satisfaction_score: Mapped[int | None] = mapped_column(nullable=True)
    customer_feedback: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Metadata
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)

    # Relationships
    customer: Mapped["Customer"] = relationship("Customer", back_populates="complaints")
    escalation_history: Mapped[list["ComplaintEscalation"]] = relationship(
        "ComplaintEscalation", back_populates="complaint", lazy="selectin",
        cascade="all, delete-orphan"
    )


class ComplaintEscalation(BaseModel):
    """
    Immutable record of each escalation step for a complaint.
    Maintains complete escalation audit trail.
    """

    __tablename__ = "complaint_escalations"
    __table_args__ = (
        Index("ix_complaint_escalations_complaint_id", "complaint_id"),
    )

    complaint_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("complaints.id", ondelete="CASCADE"), nullable=False
    )
    from_level: Mapped[int] = mapped_column(Integer, nullable=False)
    to_level: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    escalated_by: Mapped[str] = mapped_column(String(255), nullable=False)  # agent or user
    escalated_to: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    auto_escalated: Mapped[bool] = mapped_column(default=False, nullable=False)

    # Relationships
    complaint: Mapped[Complaint] = relationship("Complaint", back_populates="escalation_history")


# Forward reference
from src.database.models.customer import Customer  # noqa: E402, F401
