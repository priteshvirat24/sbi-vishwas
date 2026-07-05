"""
SBI Vishwas — Conversation Model

Multi-channel conversation threads with message history.
Supports Journey Tracker Agent maintaining a single case across channels.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.config.constants import Channel
from src.database.base import BaseModel


class Conversation(BaseModel):
    """
    A conversation thread that persists across channels and sessions.
    The Journey Tracker Agent uses this to maintain a single case file.
    """

    __tablename__ = "conversations"
    __table_args__ = (
        Index("ix_conversations_customer_id", "customer_id"),
        Index("ix_conversations_status", "status"),
        Index("ix_conversations_channel", "channel"),
    )

    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False
    )

    # Channel tracking — a conversation can span multiple channels
    channel: Mapped[str] = mapped_column(
        String(50), default=Channel.WEB.value, nullable=False
    )
    channels_used: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)

    # Status
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)
    subject: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Linked entities
    complaint_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("complaints.id", ondelete="SET NULL"), nullable=True
    )
    workflow_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )

    # Conversation metrics
    message_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_message_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_agent_type: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Handoff tracking
    transfer_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    assigned_agent_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    assigned_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Satisfaction
    satisfaction_score: Mapped[int | None] = mapped_column(nullable=True)
    resolved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Metadata
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)
    context: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Relationships
    customer: Mapped["Customer"] = relationship("Customer", back_populates="conversations")
    messages: Mapped[list["ConversationMessage"]] = relationship(
        "ConversationMessage", back_populates="conversation", lazy="noload",
        cascade="all, delete-orphan", order_by="ConversationMessage.created_at"
    )


class ConversationMessage(BaseModel):
    """
    Individual message in a conversation.
    Tracks role, content, tool calls, and agent reasoning.
    """

    __tablename__ = "conversation_messages"
    __table_args__ = (
        Index("ix_conversation_messages_conversation_id", "conversation_id"),
        Index("ix_conversation_messages_created_at", "created_at"),
    )

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False
    )

    # Message content
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # user, assistant, system, tool
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_type: Mapped[str] = mapped_column(String(50), default="text", nullable=False)

    # Channel this specific message came through
    channel: Mapped[str] = mapped_column(String(50), nullable=False)

    # AI metadata
    agent_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    model_used: Mapped[str | None] = mapped_column(String(100), nullable=True)
    token_count: Mapped[int | None] = mapped_column(nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(nullable=True)
    confidence: Mapped[float | None] = mapped_column(nullable=True)

    # Reasoning chain (for explainability)
    reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)
    tool_calls: Mapped[list[dict] | None] = mapped_column(JSONB, nullable=True)
    tool_results: Mapped[list[dict] | None] = mapped_column(JSONB, nullable=True)

    # Attachments
    attachments: Mapped[list[dict] | None] = mapped_column(JSONB, nullable=True)

    # Language
    language: Mapped[str | None] = mapped_column(String(10), nullable=True)

    # Metadata
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)

    # Relationships
    conversation: Mapped[Conversation] = relationship(
        "Conversation", back_populates="messages"
    )


# Forward reference
from src.database.models.customer import Customer  # noqa: E402, F401
