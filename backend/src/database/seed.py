"""
SBI Vishwas — Database Seed Data

Seeds the database with initial roles, permissions, a superadmin user,
and sample knowledge base entries for policy checking.
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone

import structlog
from passlib.context import CryptContext
from sqlalchemy import select

from src.auth.rbac import ROLE_PERMISSIONS, SystemRole
from src.config.constants import KnowledgeCategory, KnowledgeSourceType
from src.database.engine import get_transactional_session
from src.database.models.domain import KnowledgeEntry
from src.database.models.user import Role, User, UserRole

logger = structlog.get_logger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def seed_roles() -> None:
    """Seed all system roles with their permissions."""
    async with get_transactional_session() as session:
        for role_name in SystemRole:
            existing = await session.execute(
                select(Role).where(Role.name == role_name.value)
            )
            if existing.scalar_one_or_none():
                continue

            permissions = ROLE_PERMISSIONS.get(role_name.value, [])
            role = Role(
                name=role_name.value,
                display_name=role_name.value.replace("_", " ").title(),
                description=f"System role: {role_name.value}",
                permissions=permissions,
                is_system_role=True,
            )
            session.add(role)
            logger.info("Role created", role=role_name.value)


async def seed_superadmin() -> None:
    """Seed the superadmin user."""
    async with get_transactional_session() as session:
        existing = await session.execute(
            select(User).where(User.email == "admin@sbivishwas.in")
        )
        if existing.scalar_one_or_none():
            logger.info("Superadmin already exists")
            return

        admin = User(
            email="admin@sbivishwas.in",
            full_name="System Administrator",
            hashed_password=pwd_context.hash("admin@vishwas2024"),
            employee_id="SA001",
            is_active=True,
            is_superuser=True,
        )
        session.add(admin)
        await session.flush()

        # Assign superadmin role
        role_result = await session.execute(
            select(Role).where(Role.name == SystemRole.SUPERADMIN.value)
        )
        role = role_result.scalar_one_or_none()
        if role:
            user_role = UserRole(user_id=admin.id, role_id=role.id)
            session.add(user_role)

        logger.info("Superadmin created", email="admin@sbivishwas.in")


async def seed_knowledge_base() -> None:
    """Seed initial knowledge base with key RBI/SBI policies."""
    entries = [
        {
            "title": "BSBD Account — No Minimum Balance Requirement",
            "category": KnowledgeCategory.RBI_CIRCULAR.value,
            "source_type": KnowledgeSourceType.POLICY.value,
            "content": """As per RBI Master Direction on Financial Inclusion, dated 18.05.2023:

Basic Savings Bank Deposit (BSBD) Account / PM Jan Dhan Yojana Account:
1. No minimum balance is required to open or maintain the account.
2. No charges are levied for non-maintenance of minimum balance.
3. Banks shall not refuse to open BSBD accounts citing inability to maintain minimum balance.
4. The facility of ATM card / debit card shall be provided without any charge.
5. No charges for deposit and withdrawal at bank branch / ATMs.

Any demand for minimum balance in a BSBD/PMJDY account is a policy deviation.""",
            "summary": "BSBD/Jan Dhan accounts require zero minimum balance with no charges.",
            "tags": ["bsbd", "jan_dhan", "minimum_balance", "rbi"],
        },
        {
            "title": "No Forced Product Bundling with Accounts",
            "category": KnowledgeCategory.RBI_CIRCULAR.value,
            "source_type": KnowledgeSourceType.POLICY.value,
            "content": """RBI Master Direction on Customer Service in Banks:

1. Banks shall not force customers to buy insurance or any other product as a condition for opening a bank account.
2. No credit card, recurring deposit, or insurance policy shall be bundled mandatorily with account opening.
3. Customers have the right to open a standalone savings account without any ancillary product.
4. If a customer declines any add-on product, the bank cannot refuse account opening or delay it.
5. Any staff insistence on product purchase as a prerequisite for account opening constitutes mis-selling and is a violation of RBI guidelines.

This applies to all account types including BSBD, regular savings, and current accounts.""",
            "summary": "Banks cannot force insurance or product purchases with account opening.",
            "tags": ["forced_bundling", "insurance", "mis_selling", "rbi"],
        },
        {
            "title": "Account Opening Timeline — RBI Guidelines",
            "category": KnowledgeCategory.RBI_CIRCULAR.value,
            "source_type": KnowledgeSourceType.POLICY.value,
            "content": """RBI Guidelines on Account Opening:

1. Banks should open accounts within a reasonable timeframe, ideally same day if KYC is complete.
2. BSBD accounts should be opened immediately upon submission of valid KYC documents.
3. No customer should be asked to visit the branch multiple times for account opening.
4. If account opening is delayed beyond 7 working days, the bank must provide written reasons.
5. E-KYC (Aadhaar-based) account opening should be completed within the same visit.
6. Banks shall not demand documents beyond what is prescribed in KYC norms for the specific account type.

Acceptable KYC for BSBD: Aadhaar alone is sufficient. No need for PAN, income proof, or address proof beyond Aadhaar.""",
            "summary": "Account opening should be same-day with e-KYC. Only Aadhaar needed for BSBD.",
            "tags": ["account_opening", "kyc", "timeline", "rbi"],
        },
        {
            "title": "Dormant Account Reactivation — SBI Policy",
            "category": KnowledgeCategory.SBI_POLICY.value,
            "source_type": KnowledgeSourceType.POLICY.value,
            "content": """SBI Dormant Account Policy:

1. An account is classified as dormant/inoperative if no customer-induced transactions for 24 months.
2. Reactivation requires: KYC verification, identity confirmation, and a nominal transaction.
3. No charges should be levied for reactivation of dormant accounts.
4. The customer's balance and accrued interest must be preserved in full.
5. Reactivation can be initiated at any SBI branch, not just the home branch.
6. Digital reactivation through YONO/internet banking is available for accounts with valid e-KYC.
7. Dormant accounts with unclaimed DBT/subsidy credits should be prioritized for reactivation outreach.

Banks must make genuine efforts to contact dormant account holders before classifying accounts as unclaimed.""",
            "summary": "Dormant accounts can be reactivated at any branch with no charges.",
            "tags": ["dormant", "reactivation", "sbi_policy"],
        },
        {
            "title": "RBI FREE-AI Framework — Seven Sutras",
            "category": KnowledgeCategory.RBI_CIRCULAR.value,
            "source_type": KnowledgeSourceType.POLICY.value,
            "content": """RBI Framework for Responsible and Ethical Enablement of AI (FREE-AI):

The Seven Sutras:
1. ACCOUNTABILITY — Clear ownership of AI decisions. Human-in-the-loop for consequential actions.
2. TRANSPARENCY — AI decisions must be explainable. Reasoning chains must be auditable.
3. FAIRNESS — No discrimination based on gender, caste, religion, or geography.
4. SECURITY & PRIVACY — PII protection, data minimization, DPDP Act compliance.
5. QUALITY & RELIABILITY — Continuous monitoring, evaluation, and improvement.
6. SUSTAINABILITY — Resource efficiency, cost awareness, environmental impact.
7. INCLUSION — AI must serve all segments, especially underserved populations.

All AI systems deployed in Indian banking must comply with these principles.""",
            "summary": "RBI's seven principles for responsible AI in banking.",
            "tags": ["free_ai", "rbi", "responsible_ai", "sutras"],
        },
    ]

    async with get_transactional_session() as session:
        for entry_data in entries:
            existing = await session.execute(
                select(KnowledgeEntry).where(KnowledgeEntry.title == entry_data["title"])
            )
            if existing.scalar_one_or_none():
                continue

            entry = KnowledgeEntry(**entry_data)
            session.add(entry)
            logger.info("Knowledge entry seeded", title=entry_data["title"])


async def run_seed() -> None:
    """Run all seed functions."""
    logger.info("Starting database seeding...")
    await seed_roles()
    await seed_superadmin()
    await seed_knowledge_base()
    logger.info("Database seeding complete")


if __name__ == "__main__":
    asyncio.run(run_seed())
