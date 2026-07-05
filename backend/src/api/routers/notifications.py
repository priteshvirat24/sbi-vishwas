"""
SBI Vishwas — Notifications Router

Notification management and delivery status tracking.
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
from src.database.models.domain import Notification

logger = structlog.get_logger(__name__)

router = APIRouter()


class NotificationResponse(BaseModel):
    id: uuid.UUID
    customer_id: uuid.UUID
    notification_type: str
    channel: str
    subject: str | None
    body: str
    language: str
    status: str
    sent_at: datetime | None
    delivered_at: datetime | None
    failed_at: datetime | None
    failure_reason: str | None
    retry_count: int
    triggered_by_agent: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    items: list[NotificationResponse]
    total: int
    page: int
    page_size: int


@router.get(
    "",
    response_model=NotificationListResponse,
    summary="List notifications",
    dependencies=[Depends(PermissionChecker(Permission.NOTIFICATION_READ.value))],
)
async def list_notifications(
    db: Annotated[AsyncSession, Depends(get_session)],
    page: int = Query(1, ge=1),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    customer_id: uuid.UUID | None = None,
    status_filter: str | None = Query(None, alias="status"),
    channel: str | None = None,
    notification_type: str | None = None,
) -> NotificationListResponse:
    """List notifications with filtering."""
    query = select(Notification).where(Notification.is_deleted == False)

    if customer_id:
        query = query.where(Notification.customer_id == customer_id)
    if status_filter:
        query = query.where(Notification.status == status_filter)
    if channel:
        query = query.where(Notification.channel == channel)
    if notification_type:
        query = query.where(Notification.notification_type == notification_type)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar_one()

    query = query.offset((page - 1) * page_size).limit(page_size)
    query = query.order_by(Notification.created_at.desc())

    result = await db.execute(query)
    notifications = result.scalars().all()

    return NotificationListResponse(
        items=[NotificationResponse.model_validate(n) for n in notifications],
        total=total,
        page=page,
        page_size=page_size,
    )
