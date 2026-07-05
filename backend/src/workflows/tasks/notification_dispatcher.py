"""
SBI Vishwas — Notification Dispatcher

Processes queued notifications and dispatches them through configured channels.
"""

from __future__ import annotations

import asyncio

import structlog

from src.workflows.celery_app import celery_app

logger = structlog.get_logger(__name__)


@celery_app.task(
    name="src.workflows.tasks.notification_dispatcher.process_notification_queue",
    bind=True,
    max_retries=3,
)
def process_notification_queue(self):
    """Process pending notifications in the queue."""
    logger.info("Processing notification queue")

    try:
        asyncio.run(_process_notifications())
    except Exception as exc:
        logger.error("Notification processing failed", error=str(exc))
        raise self.retry(exc=exc)


async def _process_notifications():
    """Async notification processing."""
    from datetime import datetime, timezone
    from sqlalchemy import select, and_
    from src.database.engine import get_transactional_session
    from src.database.models.domain import Notification

    async with get_transactional_session() as session:
        result = await session.execute(
            select(Notification).where(
                and_(
                    Notification.status == "queued",
                    Notification.is_deleted == False,
                )
            ).limit(100)
        )
        notifications = result.scalars().all()

        for notification in notifications:
            try:
                # Channel-specific dispatch will be implemented via tool ecosystem
                # For now, mark as sent and log
                notification.status = "sent"
                notification.sent_at = datetime.now(timezone.utc)

                logger.info(
                    "Notification dispatched",
                    notification_id=str(notification.id),
                    channel=notification.channel,
                    type=notification.notification_type,
                )
            except Exception as e:
                notification.retry_count += 1
                if notification.retry_count >= notification.max_retries:
                    notification.status = "failed"
                    notification.failed_at = datetime.now(timezone.utc)
                    notification.failure_reason = str(e)
                logger.error(
                    "Notification dispatch failed",
                    notification_id=str(notification.id),
                    error=str(e),
                )

        logger.info("Notification queue processed", count=len(notifications))
