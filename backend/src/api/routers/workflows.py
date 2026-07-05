"""
SBI Vishwas — Workflows Router

Workflow management, execution, visualization data, and checkpoint control.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.middleware import CurrentUser, PermissionChecker, get_current_active_user
from src.auth.rbac import Permission
from src.config.constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE, WorkflowStatus
from src.database.engine import get_session
from src.database.models.workflow import AgentTask, Workflow

logger = structlog.get_logger(__name__)

router = APIRouter()


class WorkflowCreateRequest(BaseModel):
    workflow_type: str
    trigger_type: str = "manual"
    customer_id: uuid.UUID | None = None
    input_data: dict | None = None


class WorkflowResponse(BaseModel):
    id: uuid.UUID
    workflow_type: str
    status: str
    trigger_type: str
    customer_id: uuid.UUID | None
    current_node: str | None
    execution_path: list[str] | None
    started_at: datetime | None
    completed_at: datetime | None
    total_duration_ms: int | None
    total_token_count: int | None
    total_cost_usd: float | None
    error_message: str | None
    retry_count: int
    input_data: dict | None
    output_data: dict | None
    created_at: datetime
    tasks: list[AgentTaskResponse] = []

    class Config:
        from_attributes = True


class AgentTaskResponse(BaseModel):
    id: uuid.UUID
    agent_type: str
    status: str
    confidence: float | None
    decision_explanation: str | None
    model_name: str | None
    total_tokens: int | None
    latency_ms: int | None
    tool_call_count: int
    error_message: str | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True


class WorkflowListResponse(BaseModel):
    items: list[WorkflowResponse]
    total: int
    page: int
    page_size: int


@router.post(
    "",
    response_model=WorkflowResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create and start a workflow",
    dependencies=[Depends(PermissionChecker(Permission.WORKFLOW_EXECUTE.value))],
)
async def create_workflow(
    request: WorkflowCreateRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> WorkflowResponse:
    """Create and enqueue a new workflow execution."""
    workflow = Workflow(
        workflow_type=request.workflow_type,
        status=WorkflowStatus.CREATED.value,
        trigger_type=request.trigger_type,
        customer_id=request.customer_id,
        input_data=request.input_data,
        created_by=str(current_user.id),
    )
    db.add(workflow)
    await db.flush()

    logger.info("Workflow created", workflow_id=str(workflow.id), type=request.workflow_type)

    return WorkflowResponse.model_validate(workflow)


@router.get(
    "",
    response_model=WorkflowListResponse,
    summary="List workflows",
    dependencies=[Depends(PermissionChecker(Permission.WORKFLOW_READ.value))],
)
async def list_workflows(
    db: Annotated[AsyncSession, Depends(get_session)],
    page: int = Query(1, ge=1),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    status_filter: str | None = Query(None, alias="status"),
    workflow_type: str | None = None,
    customer_id: uuid.UUID | None = None,
) -> WorkflowListResponse:
    """List workflows with filtering."""
    query = select(Workflow).where(Workflow.is_deleted == False)

    if status_filter:
        query = query.where(Workflow.status == status_filter)
    if workflow_type:
        query = query.where(Workflow.workflow_type == workflow_type)
    if customer_id:
        query = query.where(Workflow.customer_id == customer_id)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar_one()

    query = query.offset((page - 1) * page_size).limit(page_size)
    query = query.order_by(Workflow.created_at.desc())

    result = await db.execute(query)
    workflows = result.scalars().all()

    return WorkflowListResponse(
        items=[_workflow_response(w) for w in workflows],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{workflow_id}",
    response_model=WorkflowResponse,
    summary="Get workflow details",
    dependencies=[Depends(PermissionChecker(Permission.WORKFLOW_READ.value))],
)
async def get_workflow(
    workflow_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> WorkflowResponse:
    """Get workflow with full task execution history."""
    result = await db.execute(
        select(Workflow).where(Workflow.id == workflow_id, Workflow.is_deleted == False)
    )
    workflow = result.scalar_one_or_none()
    if not workflow:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")

    return _workflow_response(workflow)


@router.post(
    "/{workflow_id}/cancel",
    response_model=WorkflowResponse,
    summary="Cancel a running workflow",
    dependencies=[Depends(PermissionChecker(Permission.WORKFLOW_CANCEL.value))],
)
async def cancel_workflow(
    workflow_id: uuid.UUID,
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> WorkflowResponse:
    """Cancel a running or paused workflow."""
    result = await db.execute(
        select(Workflow).where(Workflow.id == workflow_id, Workflow.is_deleted == False)
    )
    workflow = result.scalar_one_or_none()
    if not workflow:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")

    if workflow.status in (WorkflowStatus.COMPLETED.value, WorkflowStatus.CANCELLED.value):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel workflow in status: {workflow.status}",
        )

    workflow.status = WorkflowStatus.CANCELLED.value
    workflow.updated_by = str(current_user.id)
    await db.flush()

    logger.info("Workflow cancelled", workflow_id=str(workflow_id))
    return _workflow_response(workflow)


@router.get(
    "/{workflow_id}/graph",
    summary="Get workflow execution graph data",
    dependencies=[Depends(PermissionChecker(Permission.WORKFLOW_READ.value))],
)
async def get_workflow_graph(
    workflow_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    """Get workflow graph data for visualization (nodes, edges, execution state)."""
    result = await db.execute(
        select(Workflow).where(Workflow.id == workflow_id)
    )
    workflow = result.scalar_one_or_none()
    if not workflow:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")

    # Build graph representation from tasks
    nodes = []
    edges = []

    if workflow.tasks:
        for i, task in enumerate(workflow.tasks):
            nodes.append({
                "id": str(task.id),
                "label": task.agent_type,
                "status": task.status,
                "confidence": task.confidence,
                "duration_ms": task.latency_ms,
            })
            if i > 0:
                edges.append({
                    "source": str(workflow.tasks[i - 1].id),
                    "target": str(task.id),
                })

    return {
        "workflow_id": str(workflow_id),
        "workflow_type": workflow.workflow_type,
        "status": workflow.status,
        "current_node": workflow.current_node,
        "nodes": nodes,
        "edges": edges,
        "execution_path": workflow.execution_path or [],
    }


def _workflow_response(workflow: Workflow) -> WorkflowResponse:
    tasks = []
    if workflow.tasks:
        tasks = [
            AgentTaskResponse(
                id=t.id,
                agent_type=t.agent_type,
                status=t.status,
                confidence=t.confidence,
                decision_explanation=t.decision_explanation,
                model_name=t.model_name,
                total_tokens=t.total_tokens,
                latency_ms=t.latency_ms,
                tool_call_count=t.tool_call_count,
                error_message=t.error_message,
                started_at=t.started_at,
                completed_at=t.completed_at,
                created_at=t.created_at,
            )
            for t in workflow.tasks
        ]

    return WorkflowResponse(
        id=workflow.id,
        workflow_type=workflow.workflow_type,
        status=workflow.status,
        trigger_type=workflow.trigger_type,
        customer_id=workflow.customer_id,
        current_node=workflow.current_node,
        execution_path=workflow.execution_path,
        started_at=workflow.started_at,
        completed_at=workflow.completed_at,
        total_duration_ms=workflow.total_duration_ms,
        total_token_count=workflow.total_token_count,
        total_cost_usd=workflow.total_cost_usd,
        error_message=workflow.error_message,
        retry_count=workflow.retry_count,
        input_data=workflow.input_data,
        output_data=workflow.output_data,
        created_at=workflow.created_at,
        tasks=tasks,
    )
