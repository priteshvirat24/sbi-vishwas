"""
SBI Vishwas — Policy, Knowledge, Document, Notification, Audit, Evaluation Models

Remaining domain models for policy compliance, knowledge base, document management,
notifications, immutable audit log, and agent evaluation.
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

from src.database.base import BaseModel


# =============================================================================
# POLICY COMPLIANCE (Agent 2)
# =============================================================================


class PolicyDocument(BaseModel):
    """
    Versioned RBI/SBI policy documents in the knowledge base.
    Used by the Policy Compliance Companion Agent.
    """

    __tablename__ = "policy_documents"
    __table_args__ = (
        Index("ix_policy_documents_category", "category"),
        Index("ix_policy_documents_is_active", "is_active"),
    )

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    subcategory: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Content
    content: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Versioning
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    effective_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    superseded_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("policy_documents.id", ondelete="SET NULL"), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Embedding
    embedding_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Review
    reviewed_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Metadata
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)
    tags: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)


class PolicyCheck(BaseModel):
    """
    Record of a policy compliance check performed by Agent 2.
    Every check is logged — deviations trigger dashboard updates.
    """

    __tablename__ = "policy_checks"
    __table_args__ = (
        Index("ix_policy_checks_customer_id", "customer_id"),
        Index("ix_policy_checks_branch_code", "branch_code"),
        Index("ix_policy_checks_deviation_type", "deviation_type"),
        Index("ix_policy_checks_is_deviation", "is_deviation"),
    )

    customer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customers.id", ondelete="SET NULL"), nullable=True
    )
    conversation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True
    )
    branch_code: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # What was checked
    check_type: Mapped[str] = mapped_column(String(100), nullable=False)
    statement_checked: Mapped[str] = mapped_column(Text, nullable=False)
    context: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Result
    is_deviation: Mapped[bool] = mapped_column(Boolean, nullable=False)
    deviation_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    severity: Mapped[str | None] = mapped_column(String(20), nullable=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)

    # Policy reference
    policy_document_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("policy_documents.id", ondelete="SET NULL"), nullable=True
    )
    policy_citation: Mapped[str | None] = mapped_column(Text, nullable=True)
    correct_policy: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Action taken
    customer_informed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    staff_informed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    management_notified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Metadata
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)


# =============================================================================
# KNOWLEDGE BASE
# =============================================================================


class KnowledgeEntry(BaseModel):
    """
    Knowledge base entry — the RAG system's source documents.
    Can be policies, FAQs, procedures, circulars, etc.
    """

    __tablename__ = "knowledge_entries"
    __table_args__ = (
        Index("ix_knowledge_entries_category", "category"),
        Index("ix_knowledge_entries_source_type", "source_type"),
    )

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)  # policy, faq, procedure, circular

    # Content
    content: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    source_file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Embedding status
    is_embedded: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    embedding_ids: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_embedded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Version
    version: Mapped[str] = mapped_column(String(50), default="1.0", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Metadata
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)
    tags: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    language: Mapped[str] = mapped_column(String(10), default="en", nullable=False)


# =============================================================================
# DOCUMENTS
# =============================================================================


class Document(BaseModel):
    """
    Uploaded documents — KYC documents, complaint attachments, etc.
    """

    __tablename__ = "documents"
    __table_args__ = (
        Index("ix_documents_customer_id", "customer_id"),
        Index("ix_documents_document_type", "document_type"),
    )

    customer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customers.id", ondelete="SET NULL"), nullable=True
    )
    document_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_name: Mapped[str] = mapped_column(String(500), nullable=False)
    file_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    checksum: Mapped[str] = mapped_column(String(64), nullable=False)

    # OCR
    ocr_processed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ocr_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    ocr_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    ocr_structured_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Verification
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    verified_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Metadata
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)


# =============================================================================
# NOTIFICATIONS
# =============================================================================


class Notification(BaseModel):
    """
    Notification queue — used by the Proactive Communication Agent (Agent 3).
    Tracks multi-channel delivery with retry and delivery status.
    """

    __tablename__ = "notifications"
    __table_args__ = (
        Index("ix_notifications_customer_id", "customer_id"),
        Index("ix_notifications_status", "status"),
        Index("ix_notifications_notification_type", "notification_type"),
        Index("ix_notifications_channel", "channel"),
    )

    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False
    )

    # Content
    notification_type: Mapped[str] = mapped_column(String(100), nullable=False)
    channel: Mapped[str] = mapped_column(String(50), nullable=False)
    subject: Mapped[str | None] = mapped_column(String(500), nullable=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    template_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    template_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    language: Mapped[str] = mapped_column(String(10), default="en", nullable=False)

    # Delivery
    status: Mapped[str] = mapped_column(String(50), default="queued", nullable=False)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Retry
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_retries: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    next_retry_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # External reference
    external_message_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Trigger
    triggered_by_agent: Mapped[str | None] = mapped_column(String(50), nullable=True)
    triggered_by_event_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )

    # Metadata
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)


# =============================================================================
# AUDIT LOG (Immutable)
# =============================================================================


class AuditLog(BaseModel):
    """
    Immutable audit log — every agent decision, tool call, policy check,
    escalation, and human override is recorded here.

    This is the backbone of explainability and regulatory compliance.
    Records are NEVER updated or deleted.
    """

    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_logs_action", "action"),
        Index("ix_audit_logs_actor_id", "actor_id"),
        Index("ix_audit_logs_entity_type_id", "entity_type", "entity_id"),
        Index("ix_audit_logs_created_at", "created_at"),
        Index("ix_audit_logs_customer_id", "customer_id"),
    )

    # Action
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    action_category: Mapped[str] = mapped_column(String(50), nullable=False)

    # Actor
    actor_type: Mapped[str] = mapped_column(String(20), nullable=False)  # agent, user, system
    actor_id: Mapped[str] = mapped_column(String(255), nullable=False)
    actor_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Target entity
    entity_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    entity_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    # Customer context
    customer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customers.id", ondelete="SET NULL"), nullable=True
    )

    # Workflow context
    workflow_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    agent_task_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )

    # Details
    description: Mapped[str] = mapped_column(Text, nullable=False)
    details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    before_state: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    after_state: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Decision explainability
    reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Request context
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Metadata
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)


# =============================================================================
# AGENT EVALUATION (Reflection Agent)
# =============================================================================


class AgentEvaluation(BaseModel):
    """
    Agent self-evaluation and reflection records.
    Used by the Reflection/Critic agent to learn and improve.
    """

    __tablename__ = "agent_evaluations"
    __table_args__ = (
        Index("ix_agent_evaluations_agent_type", "agent_type"),
        Index("ix_agent_evaluations_agent_task_id", "agent_task_id"),
    )

    agent_task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agent_tasks.id", ondelete="CASCADE"), nullable=False
    )
    agent_type: Mapped[str] = mapped_column(String(50), nullable=False)

    # Scores
    overall_score: Mapped[float] = mapped_column(Float, nullable=False)
    accuracy_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    relevance_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    completeness_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    safety_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Reflection
    strengths: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    weaknesses: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    improvement_suggestions: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)

    # Critic feedback
    critic_feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    requires_retry: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Human evaluation (if reviewed)
    human_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    human_feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Metadata
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)


# =============================================================================
# MEMORY (Agent Memory persistence)
# =============================================================================


class AgentMemory(BaseModel):
    """
    Persistent agent memory entries.
    Stored in PostgreSQL for durability; mirrored to Qdrant for semantic retrieval.
    """

    __tablename__ = "agent_memories"
    __table_args__ = (
        Index("ix_agent_memories_memory_type", "memory_type"),
        Index("ix_agent_memories_customer_id", "customer_id"),
        Index("ix_agent_memories_agent_type", "agent_type"),
        Index("ix_agent_memories_importance", "importance_score"),
    )

    memory_type: Mapped[str] = mapped_column(String(50), nullable=False)
    agent_type: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Context
    customer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customers.id", ondelete="SET NULL"), nullable=True
    )
    conversation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )

    # Content
    content: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    key: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Scoring
    importance_score: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    access_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_accessed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    decay_factor: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)

    # Embedding
    embedding_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_embedded: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Lifecycle
    is_summarized: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    summarized_into_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agent_memories.id", ondelete="SET NULL"), nullable=True
    )

    # Metadata
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)
    tags: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
