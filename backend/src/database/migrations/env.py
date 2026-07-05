"""
SBI Vishwas — Alembic Migrations Environment

Configures Alembic to use async SQLAlchemy and discover all models.
"""

from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine

from src.config.settings import get_settings
from src.database.base import Base

# Import all models so Alembic discovers them
from src.database.models.user import User, Role, UserRole, RefreshToken  # noqa: F401
from src.database.models.customer import Customer  # noqa: F401
from src.database.models.account import Account  # noqa: F401
from src.database.models.complaint import Complaint, ComplaintEscalation  # noqa: F401
from src.database.models.conversation import Conversation, ConversationMessage  # noqa: F401
from src.database.models.workflow import Workflow, AgentTask, BankingEvent, Approval  # noqa: F401
from src.database.models.domain import (  # noqa: F401
    PolicyDocument, PolicyCheck, KnowledgeEntry, Document,
    Notification, AuditLog, AgentEvaluation, AgentMemory,
)

config = context.config
target_metadata = Base.metadata

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    settings = get_settings()
    url = settings.sync_database_url
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in 'online' mode with async engine."""
    settings = get_settings()
    connectable = create_async_engine(
        settings.async_database_url,
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
