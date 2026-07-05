"""
SBI Vishwas — Workflow, Task, Event, Approval Models

Core workflow orchestration persistence: workflow executions, checkpoints,
agent tasks, banking events, and human approval queue.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.config.constants import AgentStatus, ApprovalStatus, WorkflowStatus
from src.database.base import BaseModel


class Workflow(BaseModel):
    """
    Workflow execution record — a single LangGraph execution.
    Tracks state, checkpoints, and execution history.
    """

    __tablename__ = "workflows"
    __table_args__ = (
        Index("ix_workflows_status", "status"),
        Index("ix_workflows_workflow_type", "workflow_type"),
        Index("ix_workflows_customer_id", "customer_id"),
    )

    workflow_type: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(
        String(50), default=WorkflowStatus.CREATED.value, nullable=False
    )

    # Trigger
    trigger_type: Mapped[str] = mapped_column(String(50), nullable=False)  # event, manual, scheduled
    trigger_event_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )

    # Context
    customer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customers.id", ondelete="SET NULL"), nullable=True
    )
    input_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    output_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Execution
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    current_node: Mapped[str | None] = mapped_column(String(100), nullable=True)
    execution_path: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)

    # Checkpoint (for resume/rollback)
    checkpoint_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    checkpoint_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Error handling
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_retries: Mapped[int] = mapped_column(Integer, default=3, nullable=False)

    # Metrics
    total_duration_ms: Mapped[int | None] = mapped_column(nullable=True)
    total_token_count: Mapped[int | None] = mapped_column(nullable=True)
    total_cost_usd: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Metadata
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)

    # Relationships
    tasks: Mapped[list["AgentTask"]] = relationship(
        "AgentTask", back_populates="workflow", lazy="selectin",
        cascade="all, delete-orphan"
    )
    approvals: Mapped[list["Approval"]] = relationship(
        "Approval", back_populates="workflow", lazy="noload"
    )


class AgentTask(BaseModel):
    """
    A single agent execution within a workflow.
    Tracks the agent type, input/output, metrics, and tool calls.
    """

    __tablename__ = "agent_tasks"
    __table_args__ = (
        Index("ix_agent_tasks_workflow_id", "workflow_id"),
        Index("ix_agent_tasks_agent_type", "agent_type"),
        Index("ix_agent_tasks_status", "status"),
    )

    workflow_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False
    )

    # Agent identification
    agent_type: Mapped[str] = mapped_column(String(50), nullable=False)
    agent_version: Mapped[str] = mapped_column(String(20), default="1.0.0", nullable=False)

    # Execution
    status: Mapped[str] = mapped_column(
        String(50), default=AgentStatus.PENDING.value, nullable=False
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # I/O
    input_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    output_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    structured_output: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Reasoning
    reasoning_chain: Mapped[list[dict] | None] = mapped_column(JSONB, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    decision_explanation: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Tool usage
    tool_calls: Mapped[list[dict] | None] = mapped_column(JSONB, nullable=True)
    tool_call_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Model usage
    model_provider: Mapped[str | None] = mapped_column(String(50), nullable=True)
    model_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    prompt_tokens: Mapped[int | None] = mapped_column(nullable=True)
    completion_tokens: Mapped[int | None] = mapped_column(nullable=True)
    total_tokens: Mapped[int | None] = mapped_column(nullable=True)
    cost_usd: Mapped[float | None] = mapped_column(Float, nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(nullable=True)

    # Error
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_traceback: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Metadata
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)

    # Relationships
    workflow: Mapped[Workflow] = relationship("Workflow", back_populates="tasks")


class BankingEvent(BaseModel):
    """
    Banking events that trigger agent workflows.
    Examples: account_opened, complaint_filed, sla_breached, dbt_received.
    """

    __tablename__ = "banking_events"
    __table_args__ = (
        Index("ix_banking_events_event_type", "event_type"),
        Index("ix_banking_events_customer_id", "customer_id"),
        Index("ix_banking_events_processed", "processed"),
        Index("ix_banking_events_created_at", "created_at"),
    )

    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    source: Mapped[str] = mapped_column(String(100), nullable=False)  # cbs, branch, digital, agent

    # Context
    customer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customers.id", ondelete="SET NULL"), nullable=True
    )
    account_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True
    )
    complaint_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("complaints.id", ondelete="SET NULL"), nullable=True
    )

    # Event data
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    priority: Mapped[str] = mapped_column(String(20), default="normal", nullable=False)

    # Processing
    processed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    workflow_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workflows.id", ondelete="SET NULL"), nullable=True
    )
    processing_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Idempotency
    idempotency_key: Mapped[str | None] = mapped_column(
        String(255), unique=True, nullable=True
    )

    # Metadata
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)


class Approval(BaseModel):
    """
    Human approval request — the human-in-the-loop mechanism.

    Used by Audit Guardian agent to route credit decisions,
    policy deviation resolutions, and escalation decisions to humans.
    """

    __tablename__ = "approvals"
    __table_args__ = (
        Index("ix_approvals_status", "status"),
        Index("ix_approvals_workflow_id", "workflow_id"),
        Index("ix_approvals_assigned_to", "assigned_to_id"),
        Index("ix_approvals_approval_type", "approval_type"),
    )

    # What needs approval
    approval_type: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    # Context
    workflow_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workflows.id", ondelete="SET NULL"), nullable=True
    )
    customer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customers.id", ondelete="SET NULL"), nullable=True
    )
    agent_type: Mapped[str] = mapped_column(String(50), nullable=False)
    agent_task_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agent_tasks.id", ondelete="SET NULL"), nullable=True
    )

    # Decision context provided to human
    context_data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    ai_recommendation: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    risk_assessment: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Status
    status: Mapped[str] = mapped_column(
        String(50), default=ApprovalStatus.PENDING.value, nullable=False
    )
    priority: Mapped[str] = mapped_column(String(20), default="medium", nullable=False)

    # Assignment
    assigned_to_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    assigned_role: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Decision
    decided_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    decision: Mapped[str | None] = mapped_column(String(50), nullable=True)
    decision_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # SLA
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sla_breached: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Metadata
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)

    # Relationships
    workflow: Mapped[Workflow | None] = relationship("Workflow", back_populates="approvals")
