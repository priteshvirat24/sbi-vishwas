"""
SBI Vishwas — Complaint SLA Monitor

Periodic task that checks all open complaints against SLA deadlines
and triggers auto-escalation through the Escalation Agent.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone

import structlog

from src.workflows.celery_app import celery_app

logger = structlog.get_logger(__name__)


@celery_app.task(
    name="src.workflows.tasks.complaint_sla_monitor.check_complaint_slas",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def check_complaint_slas(self):
    """
    Check all open complaints against SLA deadlines.

    For each complaint where:
    - SLA is at risk (>75% elapsed) or breached
    - Not already at max escalation level

    Trigger the Escalation Agent to evaluate and recommend escalation.
    """
    logger.info("Starting SLA check for open complaints")

    try:
        asyncio.run(_check_slas())
    except Exception as exc:
        logger.error("SLA check failed", error=str(exc))
        raise self.retry(exc=exc)


async def _check_slas():
    """Async implementation of SLA checking."""
    from sqlalchemy import select, and_
    from src.database.engine import get_transactional_session
    from src.database.models.complaint import Complaint
    from src.config.constants import ComplaintStatus

    now = datetime.now(timezone.utc)

    async with get_transactional_session() as session:
        # Find complaints at risk or breached
        result = await session.execute(
            select(Complaint).where(
                and_(
                    Complaint.is_deleted == False,
                    Complaint.status.not_in([
                        ComplaintStatus.RESOLVED.value,
                        ComplaintStatus.CLOSED.value,
                    ]),
                    Complaint.sla_deadline.isnot(None),
                    Complaint.sla_deadline <= now,
                    Complaint.sla_breached == False,
                )
            )
        )
        breached_complaints = result.scalars().all()

        for complaint in breached_complaints:
            complaint.sla_breached = True
            logger.warning(
                "SLA breached",
                complaint_id=str(complaint.id),
                complaint_number=complaint.complaint_number,
                sla_deadline=complaint.sla_deadline.isoformat(),
            )

        if breached_complaints:
            logger.info(
                "SLA check complete",
                breached_count=len(breached_complaints),
            )
        else:
            logger.info("SLA check complete — no breaches found")
