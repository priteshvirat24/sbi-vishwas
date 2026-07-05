"""
SBI Vishwas — Complaints Router

Complaint filing, tracking, SLA management, and escalation endpoints.
Supports the Escalation & Advocate Agent (Agent 4).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.middleware import CurrentUser, PermissionChecker, get_current_active_user
from src.auth.rbac import Permission
from src.config.constants import (
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    ComplaintCategory,
    ComplaintStatus,
    EscalationLevel,
)
from src.config.settings import get_settings
from src.database.engine import get_session
from src.database.models.complaint import Complaint, ComplaintEscalation

logger = structlog.get_logger(__name__)

router = APIRouter()


# =============================================================================
# Schemas
# =============================================================================


class ComplaintCreateRequest(BaseModel):
    customer_id: uuid.UUID
    category: str = ComplaintCategory.OTHER.value
    subcategory: str | None = None
    subject: str = Field(min_length=5, max_length=500)
    description: str = Field(min_length=10)
    source_channel: str
    branch_code: str | None = None
    priority: str = "medium"


class ComplaintUpdateRequest(BaseModel):
    status: str | None = None
    priority: str | None = None
    assigned_to_id: uuid.UUID | None = None
    resolution_notes: str | None = None


class EscalateRequest(BaseModel):
    reason: str = Field(min_length=5)
    escalate_to: str | None = None
    notes: str | None = None


class ComplaintResponse(BaseModel):
    id: uuid.UUID
    complaint_number: str
    customer_id: uuid.UUID
    category: str
    subcategory: str | None
    subject: str
    description: str
    source_channel: str
    branch_code: str | None
    status: str
    priority: str
    escalation_level: int
    sla_deadline: datetime | None
    sla_breached: bool
    acknowledged_at: datetime | None
    resolved_at: datetime | None
    assigned_to_id: uuid.UUID | None
    ai_classification: str | None
    ai_suggested_resolution: str | None
    resolution_notes: str | None
    customer_satisfaction_score: int | None
    created_at: datetime
    updated_at: datetime
    escalation_history: list[EscalationResponse] = []

    class Config:
        from_attributes = True


class EscalationResponse(BaseModel):
    id: uuid.UUID
    from_level: int
    to_level: int
    reason: str
    escalated_by: str
    escalated_to: str | None
    auto_escalated: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ComplaintListResponse(BaseModel):
    items: list[ComplaintResponse]
    total: int
    page: int
    page_size: int
    pages: int


# =============================================================================
# Endpoints
# =============================================================================


@router.post(
    "",
    response_model=ComplaintResponse,
    status_code=status.HTTP_201_CREATED,
    summary="File a new complaint",
    dependencies=[Depends(PermissionChecker(Permission.COMPLAINT_WRITE.value))],
)
async def create_complaint(
    request: ComplaintCreateRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> ComplaintResponse:
    """File a new customer complaint with SLA tracking."""
    settings = get_settings()

    # Generate unique complaint number
    complaint_number = f"VIS-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"

    # Calculate SLA deadline
    sla_hours = settings.sla_complaint_resolution
    sla_deadline = datetime.now(timezone.utc) + timedelta(hours=sla_hours)

    complaint = Complaint(
        complaint_number=complaint_number,
        customer_id=request.customer_id,
        category=request.category,
        subcategory=request.subcategory,
        subject=request.subject,
        description=request.description,
        source_channel=request.source_channel,
        branch_code=request.branch_code or current_user.branch_code,
        status=ComplaintStatus.FILED.value,
        priority=request.priority,
        sla_deadline=sla_deadline,
        acknowledged_at=datetime.now(timezone.utc),
        created_by=str(current_user.id),
    )
    db.add(complaint)
    await db.flush()

    logger.info(
        "Complaint filed",
        complaint_id=str(complaint.id),
        complaint_number=complaint_number,
        category=request.category,
    )

    return _complaint_to_response(complaint)


@router.get(
    "",
    response_model=ComplaintListResponse,
    summary="List complaints",
    dependencies=[Depends(PermissionChecker(Permission.COMPLAINT_READ.value))],
)
async def list_complaints(
    db: Annotated[AsyncSession, Depends(get_session)],
    page: int = Query(1, ge=1),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    status_filter: str | None = Query(None, alias="status"),
    category: str | None = None,
    branch_code: str | None = None,
    customer_id: uuid.UUID | None = None,
    sla_breached: bool | None = None,
    escalation_level: int | None = None,
) -> ComplaintListResponse:
    """List complaints with filtering, pagination, and SLA tracking."""
    query = select(Complaint).where(Complaint.is_deleted == False)

    if status_filter:
        query = query.where(Complaint.status == status_filter)
    if category:
        query = query.where(Complaint.category == category)
    if branch_code:
        query = query.where(Complaint.branch_code == branch_code)
    if customer_id:
        query = query.where(Complaint.customer_id == customer_id)
    if sla_breached is not None:
        query = query.where(Complaint.sla_breached == sla_breached)
    if escalation_level is not None:
        query = query.where(Complaint.escalation_level == escalation_level)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar_one()

    query = query.offset((page - 1) * page_size).limit(page_size)
    query = query.order_by(Complaint.created_at.desc())

    result = await db.execute(query)
    complaints = result.scalars().all()

    pages = (total + page_size - 1) // page_size if total > 0 else 0

    return ComplaintListResponse(
        items=[_complaint_to_response(c) for c in complaints],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get(
    "/{complaint_id}",
    response_model=ComplaintResponse,
    summary="Get complaint details",
    dependencies=[Depends(PermissionChecker(Permission.COMPLAINT_READ.value))],
)
async def get_complaint(
    complaint_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> ComplaintResponse:
    """Get a complaint by ID with full escalation history."""
    result = await db.execute(
        select(Complaint).where(Complaint.id == complaint_id, Complaint.is_deleted == False)
    )
    complaint = result.scalar_one_or_none()

    if not complaint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found")

    return _complaint_to_response(complaint)


@router.patch(
    "/{complaint_id}",
    response_model=ComplaintResponse,
    summary="Update complaint status",
    dependencies=[Depends(PermissionChecker(Permission.COMPLAINT_WRITE.value))],
)
async def update_complaint(
    complaint_id: uuid.UUID,
    request: ComplaintUpdateRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> ComplaintResponse:
    """Update complaint status, assignment, or resolution."""
    result = await db.execute(
        select(Complaint).where(Complaint.id == complaint_id, Complaint.is_deleted == False)
    )
    complaint = result.scalar_one_or_none()

    if not complaint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found")

    update_data = request.model_dump(exclude_unset=True)

    if "status" in update_data:
        if update_data["status"] == ComplaintStatus.RESOLVED.value:
            complaint.resolved_at = datetime.now(timezone.utc)
        elif update_data["status"] == ComplaintStatus.CLOSED.value:
            complaint.closed_at = datetime.now(timezone.utc)

    for key, value in update_data.items():
        if hasattr(complaint, key):
            setattr(complaint, key, value)

    complaint.updated_by = str(current_user.id)
    await db.flush()

    logger.info("Complaint updated", complaint_id=str(complaint_id), updates=list(update_data.keys()))

    return _complaint_to_response(complaint)


@router.post(
    "/{complaint_id}/escalate",
    response_model=ComplaintResponse,
    summary="Escalate a complaint",
    dependencies=[Depends(PermissionChecker(Permission.COMPLAINT_ESCALATE.value))],
)
async def escalate_complaint(
    complaint_id: uuid.UUID,
    request: EscalateRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> ComplaintResponse:
    """Manually escalate a complaint to the next level."""
    result = await db.execute(
        select(Complaint).where(Complaint.id == complaint_id, Complaint.is_deleted == False)
    )
    complaint = result.scalar_one_or_none()

    if not complaint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found")

    current_level = complaint.escalation_level
    max_level = EscalationLevel.OMBUDSMAN.value

    if current_level >= max_level:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Complaint is already at maximum escalation level",
        )

    new_level = current_level + 1

    # Record escalation
    escalation = ComplaintEscalation(
        complaint_id=complaint.id,
        from_level=current_level,
        to_level=new_level,
        reason=request.reason,
        escalated_by=str(current_user.id),
        escalated_to=request.escalate_to,
        notes=request.notes,
        auto_escalated=False,
    )
    db.add(escalation)

    # Update complaint
    complaint.escalation_level = new_level
    complaint.last_escalated_at = datetime.now(timezone.utc)
    complaint.escalation_reason = request.reason

    # Update status
    status_map = {
        1: ComplaintStatus.ESCALATED_L1.value,
        2: ComplaintStatus.ESCALATED_L2.value,
        4: ComplaintStatus.ESCALATED_OMBUDSMAN.value,
    }
    if new_level in status_map:
        complaint.status = status_map[new_level]

    await db.flush()

    logger.info(
        "Complaint escalated",
        complaint_id=str(complaint_id),
        from_level=current_level,
        to_level=new_level,
    )

    return _complaint_to_response(complaint)


# =============================================================================
# Helpers
# =============================================================================


def _complaint_to_response(complaint: Complaint) -> ComplaintResponse:
    escalation_history = []
    if complaint.escalation_history:
        escalation_history = [
            EscalationResponse(
                id=e.id,
                from_level=e.from_level,
                to_level=e.to_level,
                reason=e.reason,
                escalated_by=e.escalated_by,
                escalated_to=e.escalated_to,
                auto_escalated=e.auto_escalated,
                created_at=e.created_at,
            )
            for e in complaint.escalation_history
        ]

    return ComplaintResponse(
        id=complaint.id,
        complaint_number=complaint.complaint_number,
        customer_id=complaint.customer_id,
        category=complaint.category,
        subcategory=complaint.subcategory,
        subject=complaint.subject,
        description=complaint.description,
        source_channel=complaint.source_channel,
        branch_code=complaint.branch_code,
        status=complaint.status,
        priority=complaint.priority,
        escalation_level=complaint.escalation_level,
        sla_deadline=complaint.sla_deadline,
        sla_breached=complaint.sla_breached,
        acknowledged_at=complaint.acknowledged_at,
        resolved_at=complaint.resolved_at,
        assigned_to_id=complaint.assigned_to_id,
        ai_classification=complaint.ai_classification,
        ai_suggested_resolution=complaint.ai_suggested_resolution,
        resolution_notes=complaint.resolution_notes,
        customer_satisfaction_score=complaint.customer_satisfaction_score,
        created_at=complaint.created_at,
        updated_at=complaint.updated_at,
        escalation_history=escalation_history,
    )
