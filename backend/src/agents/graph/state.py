"""
SBI Vishwas — LangGraph State Definition

The global state schema used across all nodes in the StateGraph.
This is the single source of truth for workflow state.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated, Any

from pydantic import BaseModel, Field
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


def merge_dicts(left: dict, right: dict) -> dict:
    """Merge two dicts, with right values taking precedence."""
    merged = {**left, **right}
    return merged


def append_list(left: list, right: list) -> list:
    """Append new items to existing list."""
    return left + right


class VishwasState(BaseModel):
    """
    Global state for the SBI Vishwas LangGraph.

    This state flows through every node in the graph. Each agent node
    reads from and writes to this state. The state is checkpointed
    at each step for persistence and recovery.
    """

    # -------------------------------------------------------------------------
    # Workflow identity
    # -------------------------------------------------------------------------
    workflow_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    workflow_type: str = ""  # phase_a_onboarding, phase_b_reactivation, complaint_handling, etc.
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

    # -------------------------------------------------------------------------
    # Customer context
    # -------------------------------------------------------------------------
    customer_id: uuid.UUID | None = None
    customer_profile: dict[str, Any] = Field(default_factory=dict)
    account_id: uuid.UUID | None = None
    account_data: dict[str, Any] = Field(default_factory=dict)

    # -------------------------------------------------------------------------
    # Conversation / Messages
    # -------------------------------------------------------------------------
    messages: Annotated[list[BaseMessage], add_messages] = Field(default_factory=list)
    conversation_id: uuid.UUID | None = None
    current_channel: str = "web"

    # -------------------------------------------------------------------------
    # Agent routing
    # -------------------------------------------------------------------------
    current_agent: str = ""  # Which agent is currently executing
    next_agent: str | None = None  # Determined by current agent's output
    agent_sequence: Annotated[list[str], append_list] = Field(default_factory=list)
    completed_agents: Annotated[list[str], append_list] = Field(default_factory=list)

    # -------------------------------------------------------------------------
    # Agent outputs (accumulated across the workflow)
    # -------------------------------------------------------------------------
    agent_outputs: Annotated[dict[str, Any], merge_dicts] = Field(default_factory=dict)

    # Phase A specific
    journey_analysis: dict[str, Any] | None = None
    policy_check_result: dict[str, Any] | None = None
    communication_plan: dict[str, Any] | None = None
    escalation_decision: dict[str, Any] | None = None

    # Phase B specific
    dormancy_diagnosis: dict[str, Any] | None = None
    readiness_score: dict[str, Any] | None = None
    channel_selection: dict[str, Any] | None = None
    graduation_application: dict[str, Any] | None = None

    # -------------------------------------------------------------------------
    # Complaint context
    # -------------------------------------------------------------------------
    complaint_id: uuid.UUID | None = None
    complaint_data: dict[str, Any] = Field(default_factory=dict)

    # -------------------------------------------------------------------------
    # Human approval
    # -------------------------------------------------------------------------
    requires_approval: bool = False
    approval_context: dict[str, Any] | None = None
    approval_status: str | None = None  # pending, approved, rejected
    approval_decision: dict[str, Any] | None = None

    # -------------------------------------------------------------------------
    # Execution control
    # -------------------------------------------------------------------------
    is_complete: bool = False
    should_stop: bool = False
    error: str | None = None
    iteration_count: int = 0
    max_iterations: int = 15

    # -------------------------------------------------------------------------
    # Audit trail
    # -------------------------------------------------------------------------
    audit_trail: Annotated[list[dict[str, Any]], append_list] = Field(default_factory=list)

    # -------------------------------------------------------------------------
    # Metrics
    # -------------------------------------------------------------------------
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    total_tool_calls: int = 0

    class Config:
        arbitrary_types_allowed = True
