"""
SBI Vishwas — Agents Router

Agent execution, status, history, and configuration endpoints.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.middleware import CurrentUser, PermissionChecker, get_current_active_user
from src.auth.rbac import Permission
from src.config.constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE, AgentStatus, AgentType
from src.database.engine import get_session
from src.database.models.workflow import AgentTask
from src.database.models.domain import AgentEvaluation

logger = structlog.get_logger(__name__)

router = APIRouter()


class AgentCatalogEntry(BaseModel):
    agent_type: str
    name: str
    phase: str
    description: str
    capabilities: list[str]
    available_tools: list[str]
    requires_approval: bool


class AgentExecuteRequest(BaseModel):
    agent_type: str
    customer_id: uuid.UUID | None = None
    input_data: dict
    conversation_id: uuid.UUID | None = None


class AgentTaskDetailResponse(BaseModel):
    id: uuid.UUID
    agent_type: str
    status: str
    input_data: dict | None
    output_data: dict | None
    structured_output: dict | None
    reasoning_chain: list[dict] | None
    confidence: float | None
    decision_explanation: str | None
    tool_calls: list[dict] | None
    tool_call_count: int
    model_provider: str | None
    model_name: str | None
    prompt_tokens: int | None
    completion_tokens: int | None
    total_tokens: int | None
    cost_usd: float | None
    latency_ms: int | None
    error_message: str | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True


class AgentTaskListResponse(BaseModel):
    items: list[AgentTaskDetailResponse]
    total: int
    page: int
    page_size: int


# Agent catalog — static definition of all agents
AGENT_CATALOG: list[AgentCatalogEntry] = [
    AgentCatalogEntry(
        agent_type=AgentType.JOURNEY_TRACKER.value,
        name="Journey Tracker Agent",
        phase="A",
        description="Maintains a persistent case file per customer across all channels. No customer re-explains themselves after transfer.",
        capabilities=["case_linking", "channel_tracking", "context_preservation"],
        available_tools=["crm_tool", "knowledge_search"],
        requires_approval=False,
    ),
    AgentCatalogEntry(
        agent_type=AgentType.POLICY_COMPLIANCE.value,
        name="Policy Compliance Companion",
        phase="A",
        description="Real-time policy checking against RBI/SBI knowledge base. Detects forced bundling, incorrect document demands.",
        capabilities=["policy_check", "deviation_detection", "citation_generation"],
        available_tools=["knowledge_search", "policy_engine"],
        requires_approval=False,
    ),
    AgentCatalogEntry(
        agent_type=AgentType.PROACTIVE_COMMUNICATION.value,
        name="Proactive Communication Agent",
        phase="A",
        description="Automatically sends complete status updates after events — account number, card ETA, next steps.",
        capabilities=["event_detection", "template_selection", "multi_channel_dispatch"],
        available_tools=["email_tool", "sms_tool", "whatsapp_tool", "notification_tool"],
        requires_approval=False,
    ),
    AgentCatalogEntry(
        agent_type=AgentType.ESCALATION_ADVOCATE.value,
        name="Escalation & Advocate Agent",
        phase="A",
        description="SLA tracking with auto-escalation before customer goes external to RBI Ombudsman.",
        capabilities=["sla_monitoring", "auto_escalation", "advocacy"],
        available_tools=["notification_tool", "crm_tool"],
        requires_approval=True,
    ),
    AgentCatalogEntry(
        agent_type=AgentType.DIAGNOSIS.value,
        name="Diagnosis Agent",
        phase="B",
        description="Classifies dormant account causes — no DBT, lost access, duplicate, seasonal, no need.",
        capabilities=["dormancy_classification", "signal_analysis", "suppression"],
        available_tools=["cbs_adapter", "knowledge_search"],
        requires_approval=False,
    ),
    AgentCatalogEntry(
        agent_type=AgentType.READINESS.value,
        name="Readiness Agent",
        phase="B",
        description="Computes Day-1 financial readiness score from historical CBS data.",
        capabilities=["score_computation", "continuous_refinement", "explainability"],
        available_tools=["cbs_adapter"],
        requires_approval=False,
    ),
    AgentCatalogEntry(
        agent_type=AgentType.CHANNEL_JOURNEY.value,
        name="Channel & Journey Agent",
        phase="B",
        description="Selects optimal outreach channel per account — YONO, WhatsApp, IVR, or Bank Mitra.",
        capabilities=["channel_selection", "script_generation", "bc_optimization"],
        available_tools=["sms_tool", "whatsapp_tool", "notification_tool"],
        requires_approval=False,
    ),
    AgentCatalogEntry(
        agent_type=AgentType.GRADUATION.value,
        name="Graduation Agent",
        phase="B",
        description="Prepares small-ticket credit applications (KCC, Mudra) for human sign-off.",
        capabilities=["application_preparation", "eligibility_check", "documentation"],
        available_tools=["cbs_adapter", "kyc_tool"],
        requires_approval=True,
    ),
]


@router.get(
    "/catalog",
    response_model=list[AgentCatalogEntry],
    summary="Get agent catalog",
)
async def get_agent_catalog() -> list[AgentCatalogEntry]:
    """Get the full catalog of available agents with their capabilities."""
    return AGENT_CATALOG


@router.post(
    "/execute",
    response_model=AgentTaskDetailResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Execute an agent",
    dependencies=[Depends(PermissionChecker(Permission.AGENT_EXECUTE.value))],
)
async def execute_agent(
    request: AgentExecuteRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> AgentTaskDetailResponse:
    """
    Execute an agent. Creates an agent task and enqueues it for processing.
    Returns immediately with PENDING status — use the task ID to poll for results
    or subscribe to WebSocket updates.
    """
    # Validate agent type
    valid_types = [a.agent_type for a in AGENT_CATALOG]
    if request.agent_type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown agent type: {request.agent_type}. Valid types: {valid_types}",
        )

    # Create agent task (workflow will be created by the orchestrator)
    task = AgentTask(
        workflow_id=uuid.uuid4(),  # Placeholder — orchestrator creates real workflow
        agent_type=request.agent_type,
        status=AgentStatus.PENDING.value,
        input_data=request.input_data,
        created_by=str(current_user.id),
    )
    db.add(task)
    await db.flush()

    logger.info(
        "Agent execution requested",
        task_id=str(task.id),
        agent_type=request.agent_type,
    )

    return AgentTaskDetailResponse.model_validate(task)


@router.get(
    "/tasks",
    response_model=AgentTaskListResponse,
    summary="List agent tasks",
    dependencies=[Depends(PermissionChecker(Permission.AGENT_READ.value))],
)
async def list_agent_tasks(
    db: Annotated[AsyncSession, Depends(get_session)],
    page: int = Query(1, ge=1),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    agent_type: str | None = None,
    status_filter: str | None = Query(None, alias="status"),
) -> AgentTaskListResponse:
    """List agent task executions with filtering."""
    query = select(AgentTask).where(AgentTask.is_deleted == False)

    if agent_type:
        query = query.where(AgentTask.agent_type == agent_type)
    if status_filter:
        query = query.where(AgentTask.status == status_filter)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar_one()

    query = query.offset((page - 1) * page_size).limit(page_size)
    query = query.order_by(AgentTask.created_at.desc())

    result = await db.execute(query)
    tasks = result.scalars().all()

    return AgentTaskListResponse(
        items=[AgentTaskDetailResponse.model_validate(t) for t in tasks],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/tasks/{task_id}",
    response_model=AgentTaskDetailResponse,
    summary="Get agent task details",
    dependencies=[Depends(PermissionChecker(Permission.AGENT_READ.value))],
)
async def get_agent_task(
    task_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> AgentTaskDetailResponse:
    """Get full details of an agent task including reasoning chain and tool calls."""
    result = await db.execute(select(AgentTask).where(AgentTask.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent task not found")

    return AgentTaskDetailResponse.model_validate(task)
