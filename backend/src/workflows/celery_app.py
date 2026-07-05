"""
SBI Vishwas — Celery Application

Background task queue configuration with Redis broker.
Handles SLA monitoring, dormancy scanning, notifications, and knowledge sync.
"""

from __future__ import annotations

from celery import Celery
from celery.schedules import crontab

from src.config.settings import get_settings


def create_celery_app() -> Celery:
    """Create and configure the Celery application."""
    settings = get_settings()

    app = Celery(
        "sbi_vishwas",
        broker=settings.celery_broker,
        backend=settings.celery_backend,
    )

    app.conf.update(
        # Serialization
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",

        # Timezone
        timezone="Asia/Kolkata",
        enable_utc=True,

        # Task execution
        task_track_started=True,
        task_time_limit=300,  # 5 minutes hard limit
        task_soft_time_limit=240,  # 4 minutes soft limit
        task_acks_late=True,
        worker_prefetch_multiplier=1,

        # Retry
        task_default_retry_delay=60,  # 1 minute
        task_max_retries=3,

        # Result
        result_expires=3600,  # 1 hour

        # Queues
        task_default_queue="default",
        task_routes={
            "src.workflows.tasks.complaint_sla_monitor.*": {"queue": "agents"},
            "src.workflows.tasks.dormancy_scanner.*": {"queue": "agents"},
            "src.workflows.tasks.notification_dispatcher.*": {"queue": "notifications"},
            "src.workflows.tasks.knowledge_sync.*": {"queue": "knowledge"},
        },

        # Beat schedule — periodic tasks
        beat_schedule={
            "check-complaint-slas": {
                "task": "src.workflows.tasks.complaint_sla_monitor.check_complaint_slas",
                "schedule": crontab(minute="*/15"),  # Every 15 minutes
                "options": {"queue": "agents"},
            },
            "scan-dormant-accounts": {
                "task": "src.workflows.tasks.dormancy_scanner.scan_dormant_accounts",
                "schedule": crontab(hour=2, minute=0),  # Daily at 2 AM IST
                "options": {"queue": "agents"},
            },
            "process-notification-queue": {
                "task": "src.workflows.tasks.notification_dispatcher.process_notification_queue",
                "schedule": crontab(minute="*/5"),  # Every 5 minutes
                "options": {"queue": "notifications"},
            },
            "sync-knowledge-base": {
                "task": "src.workflows.tasks.knowledge_sync.sync_knowledge_base",
                "schedule": crontab(hour=3, minute=0),  # Daily at 3 AM IST
                "options": {"queue": "knowledge"},
            },
            "run-memory-maintenance": {
                "task": "src.workflows.tasks.memory_maintenance.run_memory_maintenance",
                "schedule": crontab(hour=4, minute=0),  # Daily at 4 AM IST
                "options": {"queue": "default"},
            },
        },
    )

    # Auto-discover tasks
    app.autodiscover_tasks([
        "src.workflows.tasks",
    ])

    return app


# Module-level Celery app instance
celery_app = create_celery_app()
