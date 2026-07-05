"""
SBI Vishwas — Approvals Router

Human-in-the-loop approval queue for credit decisions, policy escalations,
and regulatory compliance actions.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.middleware import CurrentUser, PermissionChecker, get_current_active_user
from src.auth.rbac import Permission
from src.config.constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE, ApprovalStatus
from src.database.engine import get_session
from src.database.models.workflow import Approval

logger = structlog.get_logger(__name__)

router = APIRouter()


class ApprovalResponse(BaseModel):
    id: uuid.UUID
    approval_type: str
    title: str
    description: str
    workflow_id: uuid.UUID | None
    customer_id: uuid.UUID | None
    agent_type: str
    context_data: dict
    ai_recommendation: str | None
    ai_confidence: float | None
    risk_assessment: str | None
    status: str
    priority: str
    assigned_to_id: uuid.UUID | None
    assigned_role: str | None
    decided_by_id: uuid.UUID | None
    decided_at: datetime | None
    decision: str | None
    decision_notes: str | None
    expires_at: datetime | None
    sla_breached: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ApprovalDecisionRequest(BaseModel):
    decision: str = Field(pattern="^(approved|rejected)$")
    notes: str | None = None


class ApprovalListResponse(BaseModel):
    items: list[ApprovalResponse]
    total: int
    page: int
    page_size: int
    pending_count: int


@router.get(
    "",
    response_model=ApprovalListResponse,
    summary="List approval requests",
    dependencies=[Depends(PermissionChecker(Permission.APPROVAL_READ.value))],
)
async def list_approvals(
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    page: int = Query(1, ge=1),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    status_filter: str | None = Query(None, alias="status"),
    approval_type: str | None = None,
    assigned_to_me: bool = False,
) -> ApprovalListResponse:
    """List approval requests with filtering. Optionally filter to only my queue."""
    query = select(Approval).where(Approval.is_deleted == False)

    if status_filter:
        query = query.where(Approval.status == status_filter)
    if approval_type:
        query = query.where(Approval.approval_type == approval_type)
    if assigned_to_me:
        query = query.where(Approval.assigned_to_id == current_user.id)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar_one()

    # Count pending
    pending_query = select(func.count()).where(
        Approval.status == ApprovalStatus.PENDING.value,
        Approval.is_deleted == False,
    )
    if assigned_to_me:
        pending_query = pending_query.where(Approval.assigned_to_id == current_user.id)
    pending_count = (await db.execute(pending_query)).scalar_one()

    query = query.offset((page - 1) * page_size).limit(page_size)
    query = query.order_by(Approval.created_at.desc())

    result = await db.execute(query)
    approvals = result.scalars().all()

    return ApprovalListResponse(
        items=[ApprovalResponse.model_validate(a) for a in approvals],
        total=total,
        page=page,
        page_size=page_size,
        pending_count=pending_count,
    )


@router.get(
    "/{approval_id}",
    response_model=ApprovalResponse,
    summary="Get approval details",
    dependencies=[Depends(PermissionChecker(Permission.APPROVAL_READ.value))],
)
async def get_approval(
    approval_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> ApprovalResponse:
    """Get full approval context including AI recommendation and risk assessment."""
    result = await db.execute(
        select(Approval).where(Approval.id == approval_id, Approval.is_deleted == False)
    )
    approval = result.scalar_one_or_none()
    if not approval:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Approval not found")

    return ApprovalResponse.model_validate(approval)


@router.post(
    "/{approval_id}/decide",
    response_model=ApprovalResponse,
    summary="Make an approval decision",
    dependencies=[Depends(PermissionChecker(Permission.APPROVAL_DECIDE.value))],
)
async def decide_approval(
    approval_id: uuid.UUID,
    request: ApprovalDecisionRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> ApprovalResponse:
    """Approve or reject a pending approval request."""
    result = await db.execute(
        select(Approval).where(Approval.id == approval_id, Approval.is_deleted == False)
    )
    approval = result.scalar_one_or_none()
    if not approval:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Approval not found")

    if approval.status != ApprovalStatus.PENDING.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot decide on approval in status: {approval.status}",
        )

    approval.status = (
        ApprovalStatus.APPROVED.value
        if request.decision == "approved"
        else ApprovalStatus.REJECTED.value
    )
    approval.decision = request.decision
    approval.decision_notes = request.notes
    approval.decided_by_id = current_user.id
    approval.decided_at = datetime.now(timezone.utc)
    approval.updated_by = str(current_user.id)

    await db.flush()

    logger.info(
        "Approval decided",
        approval_id=str(approval_id),
        decision=request.decision,
        decided_by=str(current_user.id),
    )

    return ApprovalResponse.model_validate(approval)
