"""
SBI Vishwas — Account Model

Bank accounts with dormancy tracking, balance history, and DBT linkage.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.config.constants import AccountStatus, AccountType, DormancyCause
from src.database.base import BaseModel


class Account(BaseModel):
    """
    Bank account linked to a customer.

    Tracks dormancy status, last activity, DBT linkage —
    the data backbone for Phase B agents.
    """

    __tablename__ = "accounts"
    __table_args__ = (
        Index("ix_accounts_account_number", "account_number", unique=True),
        Index("ix_accounts_customer_id", "customer_id"),
        Index("ix_accounts_status", "status"),
        Index("ix_accounts_branch_code", "branch_code"),
        Index("ix_accounts_type_status", "account_type", "status"),
    )

    # Identity
    account_number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False
    )
    branch_code: Mapped[str] = mapped_column(String(20), nullable=False)
    ifsc_code: Mapped[str] = mapped_column(String(11), nullable=False)

    # Type & status
    account_type: Mapped[str] = mapped_column(
        String(50), default=AccountType.SAVINGS.value, nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(50), default=AccountStatus.ACTIVE.value, nullable=False
    )
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Balance
    current_balance: Mapped[Decimal] = mapped_column(
        Numeric(precision=15, scale=2), default=Decimal("0.00"), nullable=False
    )
    available_balance: Mapped[Decimal] = mapped_column(
        Numeric(precision=15, scale=2), default=Decimal("0.00"), nullable=False
    )

    # Dormancy tracking (Phase B)
    last_transaction_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    is_dormant: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    dormancy_classified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    dormancy_cause: Mapped[str | None] = mapped_column(String(50), nullable=True)
    dormancy_cause_confidence: Mapped[float | None] = mapped_column(nullable=True)
    reactivated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reactivation_channel: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # DBT (Direct Benefit Transfer) linkage
    dbt_linked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    dbt_scheme_count: Mapped[int] = mapped_column(default=0, nullable=False)
    last_dbt_credit_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Credit readiness (Phase B — Agent 6 output)
    readiness_score: Mapped[float | None] = mapped_column(nullable=True)
    readiness_score_computed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    readiness_explanation: Mapped[str | None] = mapped_column(Text, nullable=True)

    # RuPay card
    rupay_card_issued: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    rupay_last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Transaction summary (aggregated, not per-transaction)
    total_credits_12m: Mapped[Decimal] = mapped_column(
        Numeric(precision=15, scale=2), default=Decimal("0.00"), nullable=False
    )
    total_debits_12m: Mapped[Decimal] = mapped_column(
        Numeric(precision=15, scale=2), default=Decimal("0.00"), nullable=False
    )
    transaction_count_12m: Mapped[int] = mapped_column(default=0, nullable=False)
    avg_monthly_balance: Mapped[Decimal] = mapped_column(
        Numeric(precision=15, scale=2), default=Decimal("0.00"), nullable=False
    )

    # Prior credit history (from CBS data)
    has_prior_kcc: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_prior_overdraft: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    prior_credit_conduct: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Flexible metadata
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)

    # Relationships
    customer: Mapped["Customer"] = relationship("Customer", back_populates="accounts")


# Forward reference
from src.database.models.customer import Customer  # noqa: E402, F401
