"""
SBI Vishwas — LangGraph Graph Builder

Constructs the production StateGraph with conditional routing,
human interrupt nodes, parallel branches, and checkpointing.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Literal

import structlog
from langgraph.graph import END, StateGraph

from src.agents.base.agent_base import AgentInput
from src.agents.graph.state import VishwasState
from src.config.constants import AgentType

logger = structlog.get_logger(__name__)


# =============================================================================
# Node functions — each wraps an agent execution
# =============================================================================


async def supervisor_node(state: VishwasState) -> dict[str, Any]:
    """
    Entry node — routes to the appropriate agent based on workflow type
    and current state.
    """
    logger.info("Supervisor routing", workflow_type=state.workflow_type)

    state_update: dict[str, Any] = {
        "current_agent": "supervisor",
        "agent_sequence": ["supervisor"],
        "iteration_count": state.iteration_count + 1,
    }

    # Route based on workflow type
    if state.workflow_type == "policy_check":
        state_update["next_agent"] = AgentType.POLICY_COMPLIANCE.value
    elif state.workflow_type == "complaint_handling":
        state_update["next_agent"] = AgentType.JOURNEY_TRACKER.value
    elif state.workflow_type == "onboarding":
        state_update["next_agent"] = AgentType.JOURNEY_TRACKER.value
    elif state.workflow_type == "dormancy_reactivation":
        state_update["next_agent"] = AgentType.DIAGNOSIS.value
    elif state.workflow_type == "communication":
        state_update["next_agent"] = AgentType.PROACTIVE_COMMUNICATION.value
    elif state.workflow_type == "escalation_check":
        state_update["next_agent"] = AgentType.ESCALATION_ADVOCATE.value
    else:
        # Default: conversation agent
        state_update["next_agent"] = AgentType.JOURNEY_TRACKER.value

    state_update["audit_trail"] = [{
        "node": "supervisor",
        "action": "routed",
        "target": state_update["next_agent"],
        "workflow_type": state.workflow_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }]

    return state_update


async def journey_tracker_node(state: VishwasState) -> dict[str, Any]:
    """Execute the Journey Tracker Agent."""
    from src.agents.phase_a.journey_tracker import JourneyTrackerAgent

    agent = JourneyTrackerAgent()
    agent_input = AgentInput(
        customer_id=state.customer_id,
        conversation_id=state.conversation_id,
        workflow_id=state.workflow_id,
        input_data={
            "current_message": state.messages[-1].content if state.messages else "",
            "channel": state.current_channel,
            "customer_history": state.customer_profile.get("history", []),
            "customer_profile": state.customer_profile,
        },
    )

    output = await agent.run(agent_input)

    return {
        "current_agent": AgentType.JOURNEY_TRACKER.value,
        "journey_analysis": output.structured_output,
        "agent_outputs": {AgentType.JOURNEY_TRACKER.value: output.output_data},
        "completed_agents": [AgentType.JOURNEY_TRACKER.value],
        "agent_sequence": [AgentType.JOURNEY_TRACKER.value],
        "next_agent": output.next_agent,
        "total_tokens": state.total_tokens + output.total_tokens,
        "audit_trail": [{
            "node": AgentType.JOURNEY_TRACKER.value,
            "status": output.status,
            "confidence": output.confidence,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }],
    }


async def policy_compliance_node(state: VishwasState) -> dict[str, Any]:
    """Execute the Policy Compliance Agent."""
    from src.agents.phase_a.policy_compliance import PolicyComplianceAgent

    agent = PolicyComplianceAgent()
    agent_input = AgentInput(
        customer_id=state.customer_id,
        conversation_id=state.conversation_id,
        workflow_id=state.workflow_id,
        input_data={
            "statement": state.messages[-1].content if state.messages else "",
            "context": state.customer_profile.get("interaction_context", ""),
            "policy_context": [],  # Filled by RAG in Phase 3
        },
    )

    output = await agent.run(agent_input)

    return {
        "current_agent": AgentType.POLICY_COMPLIANCE.value,
        "policy_check_result": output.structured_output,
        "agent_outputs": {AgentType.POLICY_COMPLIANCE.value: output.output_data},
        "completed_agents": [AgentType.POLICY_COMPLIANCE.value],
        "agent_sequence": [AgentType.POLICY_COMPLIANCE.value],
        "requires_approval": output.requires_approval,
        "approval_context": output.approval_context,
        "total_tokens": state.total_tokens + output.total_tokens,
        "audit_trail": [{
            "node": AgentType.POLICY_COMPLIANCE.value,
            "status": output.status,
            "confidence": output.confidence,
            "is_deviation": output.output_data.get("is_deviation", False),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }],
    }


async def escalation_node(state: VishwasState) -> dict[str, Any]:
    """Execute the Escalation & Advocate Agent."""
    from src.agents.phase_a.escalation_advocate import EscalationAdvocateAgent

    agent = EscalationAdvocateAgent()
    agent_input = AgentInput(
        customer_id=state.customer_id,
        workflow_id=state.workflow_id,
        input_data={
            "complaint": state.complaint_data,
            "complaint_history": state.complaint_data.get("history", []),
            "customer_contacts": state.complaint_data.get("customer_contacts", 0),
            "similar_complaints": state.complaint_data.get("similar_complaints", []),
        },
    )

    output = await agent.run(agent_input)

    return {
        "current_agent": AgentType.ESCALATION_ADVOCATE.value,
        "escalation_decision": output.structured_output,
        "agent_outputs": {AgentType.ESCALATION_ADVOCATE.value: output.output_data},
        "completed_agents": [AgentType.ESCALATION_ADVOCATE.value],
        "agent_sequence": [AgentType.ESCALATION_ADVOCATE.value],
        "requires_approval": output.requires_approval,
        "approval_context": output.approval_context,
        "total_tokens": state.total_tokens + output.total_tokens,
        "audit_trail": [{
            "node": AgentType.ESCALATION_ADVOCATE.value,
            "status": output.status,
            "should_escalate": output.output_data.get("should_escalate", False),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }],
    }


async def communication_node(state: VishwasState) -> dict[str, Any]:
    """Execute the Proactive Communication Agent."""
    from src.agents.phase_a.proactive_communication import ProactiveCommunicationAgent

    agent = ProactiveCommunicationAgent()
    agent_input = AgentInput(
        customer_id=state.customer_id,
        workflow_id=state.workflow_id,
        input_data={
            "event_type": state.agent_outputs.get("event_type", "general"),
            "event_data": state.agent_outputs.get("event_data", {}),
            "customer_profile": state.customer_profile,
        },
    )

    output = await agent.run(agent_input)

    return {
        "current_agent": AgentType.PROACTIVE_COMMUNICATION.value,
        "communication_plan": output.structured_output,
        "agent_outputs": {AgentType.PROACTIVE_COMMUNICATION.value: output.output_data},
        "completed_agents": [AgentType.PROACTIVE_COMMUNICATION.value],
        "agent_sequence": [AgentType.PROACTIVE_COMMUNICATION.value],
        "total_tokens": state.total_tokens + output.total_tokens,
        "is_complete": True,  # Communication is typically the final step
        "audit_trail": [{
            "node": AgentType.PROACTIVE_COMMUNICATION.value,
            "status": output.status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }],
    }


async def diagnosis_node(state: VishwasState) -> dict[str, Any]:
    """Execute the Diagnosis Agent (Phase B)."""
    from src.agents.phase_b.diagnosis import DiagnosisAgent

    agent = DiagnosisAgent()
    agent_input = AgentInput(
        customer_id=state.customer_id,
        workflow_id=state.workflow_id,
        input_data={
            "account": state.account_data,
            "transaction_history": state.account_data.get("transactions", []),
            "customer_profile": state.customer_profile,
            "dbt_data": state.account_data.get("dbt", {}),
            "kyc_data": state.customer_profile.get("kyc", {}),
            "prior_reactivation_attempts": state.account_data.get("reactivation_attempts", []),
        },
    )

    output = await agent.run(agent_input)

    return {
        "current_agent": AgentType.DIAGNOSIS.value,
        "dormancy_diagnosis": output.structured_output,
        "agent_outputs": {AgentType.DIAGNOSIS.value: output.output_data},
        "completed_agents": [AgentType.DIAGNOSIS.value],
        "agent_sequence": [AgentType.DIAGNOSIS.value],
        "next_agent": output.next_agent,
        "total_tokens": state.total_tokens + output.total_tokens,
        "audit_trail": [{
            "node": AgentType.DIAGNOSIS.value,
            "status": output.status,
            "cause": output.output_data.get("primary_cause"),
            "should_pursue": output.output_data.get("should_pursue_reactivation"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }],
    }


async def readiness_node(state: VishwasState) -> dict[str, Any]:
    """Execute the Readiness Agent (Phase B)."""
    from src.agents.phase_b.readiness import ReadinessAgent

    agent = ReadinessAgent()
    agent_input = AgentInput(
        customer_id=state.customer_id,
        workflow_id=state.workflow_id,
        input_data={
            "account": state.account_data,
            "transaction_history": state.account_data.get("transactions", []),
            "dbt_data": state.account_data.get("dbt", {}),
            "kyc_data": state.customer_profile.get("kyc", {}),
            "prior_credit": state.account_data.get("prior_credit", {}),
            "diagnosis": state.dormancy_diagnosis or {},
        },
    )

    output = await agent.run(agent_input)

    return {
        "current_agent": AgentType.READINESS.value,
        "readiness_score": output.structured_output,
        "agent_outputs": {AgentType.READINESS.value: output.output_data},
        "completed_agents": [AgentType.READINESS.value],
        "agent_sequence": [AgentType.READINESS.value],
        "next_agent": output.next_agent,
        "total_tokens": state.total_tokens + output.total_tokens,
        "audit_trail": [{
            "node": AgentType.READINESS.value,
            "status": output.status,
            "score": output.output_data.get("overall_score"),
            "tier": output.output_data.get("readiness_tier"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }],
    }


async def human_approval_node(state: VishwasState) -> dict[str, Any]:
    """
    Human-in-the-loop interrupt node.

    This node pauses the workflow and waits for a human decision.
    The workflow is checkpointed here and resumed after approval/rejection.
    """
    logger.info(
        "Workflow paused for human approval",
        workflow_id=str(state.workflow_id),
        agent=state.current_agent,
        approval_context=state.approval_context,
    )

    return {
        "approval_status": "pending",
        "audit_trail": [{
            "node": "human_approval",
            "action": "waiting_for_approval",
            "context": state.approval_context,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }],
    }


async def completion_node(state: VishwasState) -> dict[str, Any]:
    """Terminal node — marks workflow as complete."""
    return {
        "is_complete": True,
        "audit_trail": [{
            "node": "completion",
            "action": "workflow_completed",
            "agents_executed": state.completed_agents,
            "total_tokens": state.total_tokens,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }],
    }


# =============================================================================
# Routing functions
# =============================================================================


def route_after_supervisor(state: VishwasState) -> str:
    """Route from supervisor to the appropriate agent."""
    next_agent = state.next_agent
    route_map = {
        AgentType.JOURNEY_TRACKER.value: "journey_tracker",
        AgentType.POLICY_COMPLIANCE.value: "policy_compliance",
        AgentType.ESCALATION_ADVOCATE.value: "escalation",
        AgentType.PROACTIVE_COMMUNICATION.value: "communication",
        AgentType.DIAGNOSIS.value: "diagnosis",
        AgentType.READINESS.value: "readiness",
    }
    return route_map.get(next_agent, "completion")


def route_after_agent(state: VishwasState) -> str:
    """Route after any agent execution — check for approval, next agent, or completion."""
    # Check iteration limit
    if state.iteration_count >= state.max_iterations:
        logger.warning("Max iterations reached", count=state.iteration_count)
        return "completion"

    # Check if approval is needed
    if state.requires_approval:
        return "human_approval"

    # Check if workflow is complete
    if state.is_complete or state.should_stop:
        return "completion"

    # Route to next agent if specified
    if state.next_agent:
        route_map = {
            AgentType.POLICY_COMPLIANCE.value: "policy_compliance",
            AgentType.PROACTIVE_COMMUNICATION.value: "communication",
            AgentType.ESCALATION_ADVOCATE.value: "escalation",
            AgentType.READINESS.value: "readiness",
            AgentType.GRADUATION.value: "completion",  # Graduation → completion for now
            AgentType.CHANNEL_JOURNEY.value: "completion",
        }
        return route_map.get(state.next_agent, "completion")

    return "completion"


def route_after_diagnosis(state: VishwasState) -> str:
    """Route after diagnosis — to readiness if reactivation recommended, else complete."""
    if state.dormancy_diagnosis and state.dormancy_diagnosis.get("should_pursue_reactivation"):
        return "readiness"
    return "completion"


def route_after_approval(state: VishwasState) -> str:
    """Route after human approval decision."""
    if state.approval_status == "approved":
        # Continue workflow
        if state.next_agent:
            return route_after_agent(state)
        return "completion"
    elif state.approval_status == "rejected":
        return "completion"
    else:
        # Still pending — this should not happen in normal flow
        return "completion"


# =============================================================================
# Graph Builder
# =============================================================================


def build_vishwas_graph() -> StateGraph:
    """
    Build the production SBI Vishwas LangGraph StateGraph.

    Graph structure:
    - Supervisor → routes to appropriate agent
    - Phase A: Journey → Policy → Communication / Escalation
    - Phase B: Diagnosis → Readiness → (Graduation)
    - Human approval interrupt at any point
    - Completion node
    """

    graph = StateGraph(VishwasState)

    # Add all nodes
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("journey_tracker", journey_tracker_node)
    graph.add_node("policy_compliance", policy_compliance_node)
    graph.add_node("escalation", escalation_node)
    graph.add_node("communication", communication_node)
    graph.add_node("diagnosis", diagnosis_node)
    graph.add_node("readiness", readiness_node)
    graph.add_node("human_approval", human_approval_node)
    graph.add_node("completion", completion_node)

    # Set entry point
    graph.set_entry_point("supervisor")

    # Supervisor routing
    graph.add_conditional_edges(
        "supervisor",
        route_after_supervisor,
        {
            "journey_tracker": "journey_tracker",
            "policy_compliance": "policy_compliance",
            "escalation": "escalation",
            "communication": "communication",
            "diagnosis": "diagnosis",
            "readiness": "readiness",
            "completion": "completion",
        },
    )

    # Phase A edges
    graph.add_conditional_edges("journey_tracker", route_after_agent, {
        "policy_compliance": "policy_compliance",
        "communication": "communication",
        "escalation": "escalation",
        "human_approval": "human_approval",
        "completion": "completion",
    })

    graph.add_conditional_edges("policy_compliance", route_after_agent, {
        "communication": "communication",
        "human_approval": "human_approval",
        "completion": "completion",
    })

    graph.add_conditional_edges("escalation", route_after_agent, {
        "communication": "communication",
        "human_approval": "human_approval",
        "completion": "completion",
    })

    graph.add_conditional_edges("communication", route_after_agent, {
        "completion": "completion",
        "human_approval": "human_approval",
    })

    # Phase B edges
    graph.add_conditional_edges("diagnosis", route_after_diagnosis, {
        "readiness": "readiness",
        "completion": "completion",
    })

    graph.add_conditional_edges("readiness", route_after_agent, {
        "completion": "completion",
        "human_approval": "human_approval",
    })

    # Human approval edges
    graph.add_conditional_edges("human_approval", route_after_approval, {
        "policy_compliance": "policy_compliance",
        "communication": "communication",
        "escalation": "escalation",
        "readiness": "readiness",
        "completion": "completion",
    })

    # Completion is the end
    graph.add_edge("completion", END)

    return graph


def compile_vishwas_graph(checkpointer=None):
    """
    Compile the graph with optional checkpointer for persistence.

    Args:
        checkpointer: LangGraph checkpointer (PostgreSQL, Redis, or memory)

    Returns:
        Compiled graph ready for execution
    """
    graph = build_vishwas_graph()

    compile_kwargs = {}
    if checkpointer:
        compile_kwargs["checkpointer"] = checkpointer

    # Add interrupt points for human approval
    compile_kwargs["interrupt_before"] = ["human_approval"]

    compiled = graph.compile(**compile_kwargs)

    logger.info("Vishwas graph compiled", has_checkpointer=checkpointer is not None)

    return compiled
