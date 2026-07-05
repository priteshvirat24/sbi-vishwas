"""
SBI Vishwas — CBS Adapter (Simulated)

Configurable data factory that simulates Core Banking System responses.
Uses Faker with banking-specific patterns — never hardcoded mock data.

In production, this adapter is replaced with the real CBS connector.
"""

from __future__ import annotations

import random
import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


class CBSAccountData(BaseModel):
    """Account data as returned by CBS."""
    account_number: str
    account_type: str
    status: str
    current_balance: Decimal
    avg_monthly_balance: Decimal
    total_credits_12m: Decimal
    total_debits_12m: Decimal
    transaction_count_12m: int
    opened_at: date
    last_transaction_at: date | None
    branch_code: str
    ifsc_code: str
    rupay_card_issued: bool
    rupay_last_used_at: date | None
    has_prior_kcc: bool
    has_prior_overdraft: bool


class CBSTransactionData(BaseModel):
    """Individual transaction from CBS."""
    transaction_id: str
    date: date
    type: str  # credit or debit
    amount: Decimal
    description: str
    channel: str
    balance_after: Decimal


class CBSDBTData(BaseModel):
    """Direct Benefit Transfer data."""
    linked: bool
    scheme_count: int
    schemes: list[str]
    last_credit_at: date | None
    frequency: str  # monthly, quarterly, irregular, none
    total_credited_12m: Decimal


class CBSKYCData(BaseModel):
    """KYC status data."""
    status: str  # verified, pending, expired, re_kyc_needed
    aadhaar_linked: bool
    pan_available: bool
    expiry_date: date | None
    documents: list[str]


class CBSCreditData(BaseModel):
    """Prior credit history."""
    has_kcc: bool
    kcc_conduct: str  # good, fair, poor, N/A
    kcc_limit: Decimal
    has_overdraft: bool
    overdraft_conduct: str
    overdraft_limit: Decimal


class DataFactory:
    """
    Configurable data factory for generating realistic CBS data.

    Each factory instance can be configured with distribution parameters
    to generate different types of customer profiles (rural, urban,
    high-activity, dormant, etc.).
    """

    # Indian state codes for realistic branch distribution
    STATES = [
        "MH", "UP", "RJ", "MP", "GJ", "KA", "AP", "TN", "WB", "OR",
        "JH", "BR", "CG", "PB", "HR", "UK", "HP", "GA", "MN", "TR",
    ]

    BRANCH_CODES = [
        f"SBI{s}{random.randint(100, 999)}"
        for s in ["MH", "UP", "RJ", "MP", "GJ", "KA"]
        for _ in range(5)
    ]

    DBT_SCHEMES = [
        "PM-KISAN", "MGNREGA", "PM-AWaas Yojana", "NSAP-Old Age Pension",
        "Ujjwala Yojana", "PM Fasal Bima", "PM-SYM", "PMSMA",
        "Sukanya Samriddhi", "Jan Dhan Overdraft",
    ]

    TRANSACTION_DESCRIPTIONS_CREDIT = [
        "DBT: PM-KISAN", "DBT: MGNREGA", "Salary Credit", "UPI Credit",
        "Cash Deposit", "Interest Credit", "Transfer Credit",
        "DBT: PM-AWaas", "DBT: NSAP Pension", "BC Agent Deposit",
    ]

    TRANSACTION_DESCRIPTIONS_DEBIT = [
        "ATM Withdrawal", "UPI Payment", "RuPay POS", "Cash Withdrawal",
        "Utility Payment", "Mobile Recharge", "Transfer Debit",
        "Aadhaar-enabled Payment", "BC Agent Withdrawal",
    ]

    def __init__(
        self,
        seed: int | None = None,
        dormancy_rate: float = 0.30,
        dbt_linkage_rate: float = 0.60,
        rupay_issuance_rate: float = 0.70,
    ) -> None:
        self._rng = random.Random(seed)
        self.dormancy_rate = dormancy_rate
        self.dbt_linkage_rate = dbt_linkage_rate
        self.rupay_issuance_rate = rupay_issuance_rate

    def generate_account(
        self,
        *,
        force_dormant: bool | None = None,
        force_dbt_linked: bool | None = None,
    ) -> CBSAccountData:
        """Generate a realistic account."""
        is_dormant = force_dormant if force_dormant is not None else (self._rng.random() < self.dormancy_rate)
        has_dbt = force_dbt_linked if force_dbt_linked is not None else (self._rng.random() < self.dbt_linkage_rate)

        # Account age: 1-8 years
        days_old = self._rng.randint(365, 365 * 8)
        opened = date.today() - timedelta(days=days_old)

        # Generate transaction patterns
        if is_dormant:
            last_txn_days_ago = self._rng.randint(180, 730)
            txn_count = self._rng.randint(0, 10)
            balance = Decimal(str(self._rng.uniform(0, 500)))
        else:
            last_txn_days_ago = self._rng.randint(0, 30)
            txn_count = self._rng.randint(12, 120)
            balance = Decimal(str(self._rng.uniform(100, 50000)))

        last_txn = date.today() - timedelta(days=last_txn_days_ago)
        branch = self._rng.choice(self.BRANCH_CODES)
        has_rupay = self._rng.random() < self.rupay_issuance_rate

        return CBSAccountData(
            account_number=f"{self._rng.randint(10000000000, 99999999999)}",
            account_type="jan_dhan" if self._rng.random() < 0.6 else "savings",
            status="dormant" if is_dormant else "active",
            current_balance=balance.quantize(Decimal("0.01")),
            avg_monthly_balance=Decimal(str(self._rng.uniform(50, balance * 1.2))).quantize(Decimal("0.01")),
            total_credits_12m=Decimal(str(self._rng.uniform(0, 200000))).quantize(Decimal("0.01")),
            total_debits_12m=Decimal(str(self._rng.uniform(0, 150000))).quantize(Decimal("0.01")),
            transaction_count_12m=txn_count,
            opened_at=opened,
            last_transaction_at=last_txn if txn_count > 0 else None,
            branch_code=branch,
            ifsc_code=f"SBIN0{self._rng.randint(10000, 99999)}",
            rupay_card_issued=has_rupay,
            rupay_last_used_at=(
                date.today() - timedelta(days=self._rng.randint(0, 365))
                if has_rupay and not is_dormant
                else None
            ),
            has_prior_kcc=self._rng.random() < 0.15,
            has_prior_overdraft=self._rng.random() < 0.10,
        )

    def generate_transactions(
        self,
        account: CBSAccountData,
        count: int | None = None,
    ) -> list[CBSTransactionData]:
        """Generate a realistic transaction history."""
        n = count or account.transaction_count_12m
        if n == 0:
            return []

        transactions = []
        balance = float(account.current_balance)
        current_date = date.today()

        for i in range(n):
            days_ago = self._rng.randint(0, 365)
            txn_date = current_date - timedelta(days=days_ago)

            is_credit = self._rng.random() < 0.55
            if is_credit:
                amount = Decimal(str(self._rng.uniform(100, 25000))).quantize(Decimal("0.01"))
                description = self._rng.choice(self.TRANSACTION_DESCRIPTIONS_CREDIT)
                balance += float(amount)
            else:
                amount = Decimal(str(self._rng.uniform(50, 10000))).quantize(Decimal("0.01"))
                description = self._rng.choice(self.TRANSACTION_DESCRIPTIONS_DEBIT)
                balance = max(0, balance - float(amount))

            transactions.append(CBSTransactionData(
                transaction_id=f"TXN{uuid.uuid4().hex[:12].upper()}",
                date=txn_date,
                type="credit" if is_credit else "debit",
                amount=amount,
                description=description,
                channel=self._rng.choice(["atm", "branch", "upi", "pos", "bc_agent", "yono"]),
                balance_after=Decimal(str(balance)).quantize(Decimal("0.01")),
            ))

        # Sort by date descending
        transactions.sort(key=lambda t: t.date, reverse=True)
        return transactions

    def generate_dbt_data(self, account: CBSAccountData) -> CBSDBTData:
        """Generate DBT linkage data."""
        linked = self._rng.random() < self.dbt_linkage_rate

        if not linked:
            return CBSDBTData(
                linked=False, scheme_count=0, schemes=[], last_credit_at=None,
                frequency="none", total_credited_12m=Decimal("0"),
            )

        scheme_count = self._rng.randint(1, 3)
        schemes = self._rng.sample(self.DBT_SCHEMES, scheme_count)
        freq = self._rng.choice(["monthly", "quarterly", "irregular"])

        return CBSDBTData(
            linked=True,
            scheme_count=scheme_count,
            schemes=schemes,
            last_credit_at=date.today() - timedelta(days=self._rng.randint(0, 90)),
            frequency=freq,
            total_credited_12m=Decimal(str(self._rng.uniform(2000, 100000))).quantize(Decimal("0.01")),
        )

    def generate_kyc_data(self) -> CBSKYCData:
        """Generate KYC data."""
        status = self._rng.choice(["verified", "verified", "verified", "pending", "expired", "re_kyc_needed"])
        return CBSKYCData(
            status=status,
            aadhaar_linked=self._rng.random() < 0.85,
            pan_available=self._rng.random() < 0.40,
            expiry_date=(
                date.today() + timedelta(days=self._rng.randint(-90, 730))
                if status != "verified"
                else date.today() + timedelta(days=self._rng.randint(365, 1825))
            ),
            documents=["aadhaar"] + (["pan"] if self._rng.random() < 0.4 else []),
        )

    def generate_credit_data(self, account: CBSAccountData) -> CBSCreditData:
        """Generate prior credit history."""
        has_kcc = account.has_prior_kcc
        has_od = account.has_prior_overdraft

        return CBSCreditData(
            has_kcc=has_kcc,
            kcc_conduct=self._rng.choice(["good", "good", "fair", "poor"]) if has_kcc else "N/A",
            kcc_limit=Decimal(str(self._rng.uniform(25000, 300000))).quantize(Decimal("0.01")) if has_kcc else Decimal("0"),
            has_overdraft=has_od,
            overdraft_conduct=self._rng.choice(["good", "good", "fair"]) if has_od else "N/A",
            overdraft_limit=Decimal(str(self._rng.uniform(5000, 10000))).quantize(Decimal("0.01")) if has_od else Decimal("0"),
        )

    def generate_complete_customer_data(
        self,
        force_dormant: bool | None = None,
    ) -> dict[str, Any]:
        """
        Generate a complete customer dataset for testing.
        Returns everything needed for the Phase B pipeline.
        """
        account = self.generate_account(force_dormant=force_dormant)
        transactions = self.generate_transactions(account)
        dbt = self.generate_dbt_data(account)
        kyc = self.generate_kyc_data()
        credit = self.generate_credit_data(account)

        return {
            "account": account.model_dump(mode="json"),
            "transaction_history": [t.model_dump(mode="json") for t in transactions],
            "dbt_data": dbt.model_dump(mode="json"),
            "kyc_data": kyc.model_dump(mode="json"),
            "prior_credit": credit.model_dump(mode="json"),
        }


# Module-level factory instance with default configuration
cbs_data_factory = DataFactory(seed=42)
