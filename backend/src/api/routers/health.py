"""
SBI Vishwas — Health Check Router

Provides health, readiness, and liveness endpoints for monitoring
and Kubernetes probes.
"""

from __future__ import annotations

from datetime import datetime, timezone

import structlog
from fastapi import APIRouter, status
from fastapi.responses import ORJSONResponse

from src.config.settings import get_settings

logger = structlog.get_logger(__name__)

router = APIRouter()


@router.get(
    "/api/v1/health",
    status_code=status.HTTP_200_OK,
    summary="Health check",
    description="Returns the current health status of the application.",
)
async def health_check() -> ORJSONResponse:
    """Basic health check endpoint."""
    settings = get_settings()
    return ORJSONResponse(
        content={
            "status": "healthy",
            "service": settings.app_name,
            "version": settings.app_version,
            "environment": settings.app_env.value,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )


@router.get(
    "/api/v1/health/ready",
    status_code=status.HTTP_200_OK,
    summary="Readiness check",
    description="Checks if all dependencies are available.",
)
async def readiness_check() -> ORJSONResponse:
    """
    Readiness probe — checks database, Redis, and Qdrant connectivity.
    Returns 503 if any dependency is unavailable.
    """
    checks: dict[str, dict] = {}
    all_healthy = True

    # Check PostgreSQL
    try:
        from src.database.engine import get_engine
        engine = get_engine()
        async with engine.connect() as conn:
            await conn.execute(
                __import__("sqlalchemy").text("SELECT 1")
            )
        checks["postgres"] = {"status": "healthy"}
    except Exception as e:
        checks["postgres"] = {"status": "unhealthy", "error": str(e)}
        all_healthy = False

    # Check Redis
    try:
        from redis.asyncio import Redis
        settings = get_settings()
        redis = Redis.from_url(settings.redis_connection_url)
        await redis.ping()
        await redis.aclose()
        checks["redis"] = {"status": "healthy"}
    except Exception as e:
        checks["redis"] = {"status": "unhealthy", "error": str(e)}
        all_healthy = False

    # Check Qdrant
    try:
        from qdrant_client import QdrantClient
        settings = get_settings()
        client = QdrantClient(
            host=settings.qdrant_host,
            port=settings.qdrant_port,
            api_key=settings.qdrant_api_key,
        )
        client.get_collections()
        client.close()
        checks["qdrant"] = {"status": "healthy"}
    except Exception as e:
        checks["qdrant"] = {"status": "unhealthy", "error": str(e)}
        all_healthy = False

    status_code = status.HTTP_200_OK if all_healthy else status.HTTP_503_SERVICE_UNAVAILABLE
    return ORJSONResponse(
        status_code=status_code,
        content={
            "status": "ready" if all_healthy else "not_ready",
            "checks": checks,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


@router.get(
    "/api/v1/health/live",
    status_code=status.HTTP_200_OK,
    summary="Liveness check",
)
async def liveness_check() -> ORJSONResponse:
    """Liveness probe — always returns 200 if the process is running."""
    return ORJSONResponse(content={"status": "alive"})
