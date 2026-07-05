"""
SBI Vishwas — FastAPI Application Factory

Creates and configures the FastAPI application with all middleware,
routers, exception handlers, and lifecycle management.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

import structlog
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from src.config.settings import get_settings
from src.config.observability import PrometheusMiddleware, router as observability_router
from src.database.engine import close_engine, get_engine


logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager — handles startup and shutdown.
    """
    settings = get_settings()
    logger.info(
        "Starting SBI Vishwas",
        version=settings.app_version,
        env=settings.app_env.value,
    )

    # Startup: ensure DB engine is initialized
    get_engine()
    logger.info("Database engine initialized")

    yield

    # Shutdown: close connections
    await close_engine()
    logger.info("Database engine closed")
    logger.info("SBI Vishwas shutdown complete")


def create_app() -> FastAPI:
    """
    FastAPI application factory.

    Usage:
        uvicorn src.api.main:create_app --factory
    """
    settings = get_settings()

    app = FastAPI(
        title="SBI Vishwas",
        description="Autonomous Agentic AI Banking Operating System",
        version=settings.app_version,
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
        openapi_url="/openapi.json" if settings.is_development else None,
        default_response_class=ORJSONResponse,
        lifespan=lifespan,
    )

    # -------------------------------------------------------------------------
    # Middleware
    # -------------------------------------------------------------------------

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add Prometheus observability middleware
    app.add_middleware(PrometheusMiddleware)

    # Request ID middleware
    app.add_middleware(RequestIDMiddleware)

    # -------------------------------------------------------------------------
    # Exception handlers
    # -------------------------------------------------------------------------

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> ORJSONResponse:
        logger.error(
            "Unhandled exception",
            error=str(exc),
            path=request.url.path,
            method=request.method,
            exc_info=exc,
        )
        return ORJSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "internal_server_error",
                "message": "An unexpected error occurred. Please try again later.",
                "request_id": getattr(request.state, "request_id", None),
            },
        )

    # -------------------------------------------------------------------------
    # Routers
    # -------------------------------------------------------------------------

    from src.api.routers import (
        agents,
        approvals,
        audit,
        auth,
        complaints,
        conversations,
        customers,
        health,
        knowledge,
        notifications,
        workflows,
    )

    api_prefix = "/api/v1"

    app.include_router(health.router, tags=["Health"])
    app.include_router(auth.router, prefix=f"{api_prefix}/auth", tags=["Authentication"])
    app.include_router(customers.router, prefix=f"{api_prefix}/customers", tags=["Customers"])
    app.include_router(complaints.router, prefix=f"{api_prefix}/complaints", tags=["Complaints"])
    app.include_router(conversations.router, prefix=f"{api_prefix}/conversations", tags=["Conversations"])
    app.include_router(workflows.router, prefix=f"{api_prefix}/workflows", tags=["Workflows"])
    app.include_router(agents.router, prefix=f"{api_prefix}/agents", tags=["Agents"])
    app.include_router(approvals.router, prefix=f"{api_prefix}/approvals", tags=["Approvals"])
    app.include_router(knowledge.router, prefix=f"{api_prefix}/knowledge", tags=["Knowledge"])
    app.include_router(notifications.router, prefix=f"{api_prefix}/notifications", tags=["Notifications"])
    app.include_router(audit.router, prefix=f"{api_prefix}/audit", tags=["Audit"])

    logger.info("All routers registered", router_count=11)

    # Mount observability router
    app.include_router(observability_router)

    return app


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Add a unique request ID to every request for tracing."""

    async def dispatch(self, request: Request, call_next):
        import uuid
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
