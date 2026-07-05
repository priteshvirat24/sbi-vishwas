"""
SBI Vishwas — Database Base Model

Declarative base with common mixins for timestamps, soft-delete, and audit fields.
All ORM models inherit from these.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """SQLAlchemy declarative base for all models."""
    pass


class TimestampMixin:
    """Adds created_at and updated_at columns with auto-management."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class SoftDeleteMixin:
    """Adds soft-delete capability. Records are never physically deleted."""

    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )


class AuditMixin:
    """Adds audit fields for tracking who created/modified records."""

    created_by: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    updated_by: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )


class UUIDPrimaryKeyMixin:
    """Adds a UUID primary key column."""

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )


class DescriptionMixin:
    """Adds optional description/notes field."""

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )


class BaseModel(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, AuditMixin):
    """
    Abstract base model combining UUID PK, timestamps, soft-delete, and audit fields.

    All domain models should inherit from this.
    """
    __abstract__ = True

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(id={self.id})>"
