"""
SBI Vishwas — Audit Router

Immutable audit log queries — every AI decision, tool call, policy check,
and human override is recorded and queryable here.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.middleware import PermissionChecker, get_current_active_user, CurrentUser
from src.auth.rbac import Permission
from src.config.constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from src.database.engine import get_session
from src.database.models.domain import AuditLog

logger = structlog.get_logger(__name__)

router = APIRouter()


class AuditLogResponse(BaseModel):
    id: uuid.UUID
    action: str
    action_category: str
    actor_type: str
    actor_id: str
    actor_name: str | None
    entity_type: str | None
    entity_id: uuid.UUID | None
    customer_id: uuid.UUID | None
    workflow_id: uuid.UUID | None
    description: str
    details: dict | None
    reasoning: str | None
    confidence: float | None
    ip_address: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class AuditListResponse(BaseModel):
    items: list[AuditLogResponse]
    total: int
    page: int
    page_size: int


class AuditStatsResponse(BaseModel):
    total_entries: int
    actions_breakdown: dict[str, int]
    actor_type_breakdown: dict[str, int]
    recent_24h_count: int


@router.get(
    "",
    response_model=AuditListResponse,
    summary="Query audit logs",
    dependencies=[Depends(PermissionChecker(Permission.AUDIT_READ.value))],
)
async def list_audit_logs(
    db: Annotated[AsyncSession, Depends(get_session)],
    page: int = Query(1, ge=1),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    action: str | None = None,
    action_category: str | None = None,
    actor_type: str | None = None,
    actor_id: str | None = None,
    entity_type: str | None = None,
    entity_id: uuid.UUID | None = None,
    customer_id: uuid.UUID | None = None,
    workflow_id: uuid.UUID | None = None,
    from_date: datetime | None = None,
    to_date: datetime | None = None,
) -> AuditListResponse:
    """Query the immutable audit log with comprehensive filtering."""
    query = select(AuditLog)

    if action:
        query = query.where(AuditLog.action == action)
    if action_category:
        query = query.where(AuditLog.action_category == action_category)
    if actor_type:
        query = query.where(AuditLog.actor_type == actor_type)
    if actor_id:
        query = query.where(AuditLog.actor_id == actor_id)
    if entity_type:
        query = query.where(AuditLog.entity_type == entity_type)
    if entity_id:
        query = query.where(AuditLog.entity_id == entity_id)
    if customer_id:
        query = query.where(AuditLog.customer_id == customer_id)
    if workflow_id:
        query = query.where(AuditLog.workflow_id == workflow_id)
    if from_date:
        query = query.where(AuditLog.created_at >= from_date)
    if to_date:
        query = query.where(AuditLog.created_at <= to_date)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar_one()

    query = query.offset((page - 1) * page_size).limit(page_size)
    query = query.order_by(AuditLog.created_at.desc())

    result = await db.execute(query)
    logs = result.scalars().all()

    return AuditListResponse(
        items=[AuditLogResponse.model_validate(log) for log in logs],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/stats",
    response_model=AuditStatsResponse,
    summary="Get audit statistics",
    dependencies=[Depends(PermissionChecker(Permission.AUDIT_READ.value))],
)
async def get_audit_stats(
    db: Annotated[AsyncSession, Depends(get_session)],
) -> AuditStatsResponse:
    """Get aggregate audit statistics."""
    from datetime import timedelta, timezone

    total = (await db.execute(select(func.count(AuditLog.id)))).scalar_one()

    # Actions breakdown
    actions_result = await db.execute(
        select(AuditLog.action, func.count(AuditLog.id))
        .group_by(AuditLog.action)
        .order_by(func.count(AuditLog.id).desc())
        .limit(20)
    )
    actions_breakdown = {row[0]: row[1] for row in actions_result.all()}

    # Actor type breakdown
    actor_result = await db.execute(
        select(AuditLog.actor_type, func.count(AuditLog.id))
        .group_by(AuditLog.actor_type)
    )
    actor_breakdown = {row[0]: row[1] for row in actor_result.all()}

    # Last 24h
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    recent = (await db.execute(
        select(func.count(AuditLog.id)).where(AuditLog.created_at >= cutoff)
    )).scalar_one()

    return AuditStatsResponse(
        total_entries=total,
        actions_breakdown=actions_breakdown,
        actor_type_breakdown=actor_breakdown,
        recent_24h_count=recent,
    )
