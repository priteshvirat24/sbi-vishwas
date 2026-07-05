"""
SBI Vishwas — Database Engine

Async SQLAlchemy engine and session factory configuration.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.config.settings import get_settings


def create_engine() -> AsyncEngine:
    """Create and configure the async SQLAlchemy engine."""
    settings = get_settings()
    return create_async_engine(
        settings.async_database_url,
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow,
        echo=settings.database_echo,
        pool_pre_ping=True,
        pool_recycle=3600,
        connect_args={
            "server_settings": {
                "application_name": settings.app_name,
            },
        },
    )


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Create an async session factory bound to the given engine."""
    return async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )


# Module-level engine and session factory (initialized lazily)
_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    """Get or create the module-level engine."""
    global _engine
    if _engine is None:
        _engine = create_engine()
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Get or create the module-level session factory."""
    global _session_factory
    if _session_factory is None:
        _session_factory = create_session_factory(get_engine())
    return _session_factory


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency: yield an async database session.

    Usage in route:
        async def endpoint(db: AsyncSession = Depends(get_session)):
            ...
    """
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            if session.new or session.dirty or session.deleted:
                await session.commit()
            else:
                await session.rollback()
        except Exception:
            await session.rollback()
            raise


@asynccontextmanager
async def get_transactional_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager for transactional operations outside of FastAPI request lifecycle.

    Usage:
        async with get_transactional_session() as session:
            ...
    """
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def close_engine() -> None:
    """Dispose the engine and close all connections. Called during shutdown."""
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _session_factory = None
