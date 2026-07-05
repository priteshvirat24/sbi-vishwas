"""
SBI Vishwas — Customer Model

Customer profiles — distinct from system users.
A customer may or may not have a system login.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.config.constants import Channel, KYCStatus
from src.database.base import BaseModel


class Customer(BaseModel):
    """
    Core customer profile — the central entity across Phase A and Phase B.

    PII fields (aadhaar_hash, pan_hash, phone, email) are stored encrypted.
    Raw PII is never stored — only encrypted or hashed versions.
    """

    __tablename__ = "customers"
    __table_args__ = (
        Index("ix_customers_cif_number", "cif_number", unique=True),
        Index("ix_customers_phone_hash", "phone_hash"),
        Index("ix_customers_email_hash", "email_hash"),
        Index("ix_customers_branch_code", "branch_code"),
        Index("ix_customers_kyc_status", "kyc_status"),
    )

    # SBI Identity
    cif_number: Mapped[str | None] = mapped_column(String(20), unique=True, nullable=True)
    branch_code: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Personal (encrypted at application layer)
    full_name_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    phone_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    phone_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    email_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    email_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)
    gender: Mapped[str | None] = mapped_column(String(10), nullable=True)

    # Address (encrypted)
    address_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    state: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    pincode: Mapped[str | None] = mapped_column(String(10), nullable=True, index=True)

    # KYC
    kyc_status: Mapped[str] = mapped_column(
        String(50), default=KYCStatus.NOT_STARTED.value, nullable=False
    )
    kyc_completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    kyc_expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    aadhaar_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    pan_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Channel preferences
    preferred_channel: Mapped[str] = mapped_column(
        String(50), default=Channel.BRANCH.value, nullable=False
    )
    preferred_language: Mapped[str] = mapped_column(String(10), default="hi", nullable=False)
    whatsapp_opted_in: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sms_opted_in: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Consent management (DPDP Act)
    consent_data_processing: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    consent_data_processing_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    consent_credit_scoring: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    consent_credit_scoring_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    consent_marketing: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationship
    relationship_manager_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    customer_since: Mapped[date | None] = mapped_column(Date, nullable=True)
    segment: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Linked system user (if customer has a portal login)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Flexible metadata
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)
    tags: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)

    # Relationships
    accounts: Mapped[list["Account"]] = relationship(
        "Account", back_populates="customer", lazy="selectin"
    )
    complaints: Mapped[list["Complaint"]] = relationship(
        "Complaint", back_populates="customer", lazy="noload"
    )
    conversations: Mapped[list["Conversation"]] = relationship(
        "Conversation", back_populates="customer", lazy="noload"
    )


# Avoid circular import — Account and Complaint are forward-referenced
from src.database.models.account import Account  # noqa: E402, F401
from src.database.models.complaint import Complaint  # noqa: E402, F401
from src.database.models.conversation import Conversation  # noqa: E402, F401
