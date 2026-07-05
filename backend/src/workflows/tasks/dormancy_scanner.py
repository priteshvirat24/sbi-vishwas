"""
SBI Vishwas — Dormancy Scanner

Periodic batch task that identifies dormant accounts and triggers
the Phase B diagnosis pipeline.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone

import structlog

from src.workflows.celery_app import celery_app

logger = structlog.get_logger(__name__)


@celery_app.task(
    name="src.workflows.tasks.dormancy_scanner.scan_dormant_accounts",
    bind=True,
    max_retries=3,
    default_retry_delay=120,
)
def scan_dormant_accounts(self):
    """
    Scan accounts for dormancy.

    Identifies accounts that:
    - Have no transactions in the past N months (configurable)
    - Are not already classified as dormant
    - Are of type Jan Dhan / BSBD / savings

    Marks them as dormant and queues for diagnosis.
    """
    logger.info("Starting dormancy scan")

    try:
        asyncio.run(_scan_dormancy())
    except Exception as exc:
        logger.error("Dormancy scan failed", error=str(exc))
        raise self.retry(exc=exc)


async def _scan_dormancy():
    """Async implementation of dormancy scanning."""
    from sqlalchemy import select, and_
    from src.database.engine import get_transactional_session
    from src.database.models.account import Account
    from src.config.constants import AccountStatus
    from src.config.settings import get_settings

    settings = get_settings()
    cutoff = datetime.now(timezone.utc) - timedelta(days=settings.dormancy_inactive_months * 30)

    async with get_transactional_session() as session:
        result = await session.execute(
            select(Account).where(
                and_(
                    Account.is_deleted == False,
                    Account.status == AccountStatus.ACTIVE.value,
                    Account.is_dormant == False,
                    Account.last_transaction_at.isnot(None),
                    Account.last_transaction_at < cutoff,
                )
            ).limit(settings.dormancy_scan_batch_size)
        )
        accounts = result.scalars().all()

        newly_dormant = 0
        for account in accounts:
            account.is_dormant = True
            account.status = AccountStatus.DORMANT.value
            newly_dormant += 1

        logger.info(
            "Dormancy scan complete",
            scanned=len(accounts),
            newly_dormant=newly_dormant,
        )
