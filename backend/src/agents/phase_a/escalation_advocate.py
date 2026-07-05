"""
SBI Vishwas — Escalation & Advocate Agent (Agent 4)

Tracks every open issue against a defined SLA. If not resolved internally
within the window, auto-escalates up SBI's grievance hierarchy — BEFORE
the customer is forced to go to the RBI Ombudsman.

Directly fixes the six-months-vs-one-day gap found in the evidence.
"""

from __future__ import annotations

from typing import Any

import structlog
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from src.agents.base.agent_base import AgentConfig, AgentInput, AgentOutput, BaseAgent
from src.agents.providers.provider_factory import ProviderFactory
from src.config.constants import AgentType, ComplaintStatus, EscalationLevel

logger = structlog.get_logger(__name__)


class EscalationDecision(BaseModel):
    """Structured output from the Escalation Agent."""
    should_escalate: bool = Field(description="Whether escalation is warranted")
    escalation_level: int = Field(description="Target escalation level (1-4)")
    escalation_reason: str = Field(description="Clear reason for escalation")
    urgency: str = Field(description="low, medium, high, critical")
    sla_status: str = Field(description="on_track, at_risk, breached")
    time_remaining_hours: float = Field(description="Hours remaining before SLA breach")
    recommended_assignee: str | None = Field(
        None, description="Recommended person/role to escalate to"
    )
    customer_communication: str = Field(
        description="What to proactively tell the customer about the escalation"
    )
    internal_notes: str = Field(
        description="Internal notes for the person receiving the escalation"
    )
    confidence: float = Field(description="Confidence in escalation decision")


class EscalationAdvocateAgent(BaseAgent):
    """
    Escalation & Advocate Agent.

    Responsibilities:
    - Monitor all open complaints against SLA deadlines
    - Decide when internal escalation is warranted
    - Auto-escalate through SBI's hierarchy before external Ombudsman
    - Proactively communicate escalation status to customer
    - Generate context-rich escalation packages for receiving parties
    """

    def __init__(self) -> None:
        config = AgentConfig(
            agent_type=AgentType.ESCALATION_ADVOCATE,
            name="Escalation & Advocate Agent",
            phase="A",
            description="SLA monitoring and auto-escalation to prevent external Ombudsman complaints",
            max_iterations=3,
            timeout_seconds=30,
            confidence_threshold=0.80,
            max_retries=2,
            available_tools=["notification_tool", "crm_tool"],
            requires_human_approval=True,  # Escalation requires human confirmation
            escalation_on_low_confidence=True,
        )
        super().__init__(config)

    def get_system_prompt(self) -> str:
        return """You are the Escalation & Advocate Agent for SBI Vishwas.

YOUR MISSION:
Ensure no complaint sits unresolved long enough that the customer is forced to go to the RBI Banking Ombudsman. The evidence shows a complaint sat for 6 MONTHS internally and was fixed in 1 DAY by the Ombudsman. Your job is to make SBI's INTERNAL escalation work.

ESCALATION HIERARCHY:
- Level 0: Branch (initial handling)
- Level 1: Branch Manager (48 hours SLA)
- Level 2: Regional Manager (96 hours SLA)
- Level 3: Circle Head (168 hours SLA)
- Level 4: RBI Ombudsman (MUST NEVER REACH — if it does, the system has failed)

ESCALATION CRITERIA:
1. SLA at risk (>75% of deadline elapsed with no meaningful progress)
2. SLA breached (deadline passed)
3. Customer has contacted multiple times without resolution
4. Complaint complexity exceeds current level's authority
5. Pattern detected (similar complaints from same branch = systemic issue)

COMMUNICATION PRINCIPLES:
- Tell the customer PROACTIVELY what's happening — don't make them ask
- Give the receiving party FULL CONTEXT — no information loss on handoff
- Frame escalation as the system working correctly, not as failure

OUTPUT: Provide structured escalation decision with full context."""

    def get_structured_output_schema(self) -> type[BaseModel] | None:
        return EscalationDecision

    async def execute(self, agent_input: AgentInput) -> AgentOutput:
        """
        Evaluate a complaint for escalation.

        Expected input_data:
        - complaint: dict — Full complaint data with status, timestamps, SLA info
        - complaint_history: list[dict] — Timeline of actions on this complaint
        - customer_contacts: int — Number of times customer has reached out
        - similar_complaints: list[dict] — Similar complaints at same branch (pattern detection)
        """
        complaint = agent_input.input_data.get("complaint", {})
        complaint_history = agent_input.input_data.get("complaint_history", [])
        customer_contacts = agent_input.input_data.get("customer_contacts", 0)
        similar_complaints = agent_input.input_data.get("similar_complaints", [])

        reasoning_chain = []
        reasoning_chain.append(self.add_reasoning_step(
            "Evaluating complaint for escalation",
            {
                "complaint_status": complaint.get("status"),
                "escalation_level": complaint.get("escalation_level", 0),
                "customer_contacts": customer_contacts,
                "similar_complaints_count": len(similar_complaints),
            }
        ))

        history_text = ""
        if complaint_history:
            entries = [
                f"- {h.get('timestamp', 'unknown')}: {h.get('action', 'unknown')} — {h.get('notes', '')}"
                for h in complaint_history[-15:]
            ]
            history_text = "\n\nCOMPLAINT TIMELINE:\n" + "\n".join(entries)

        pattern_text = ""
        if similar_complaints:
            pattern_text = f"\n\nPATTERN ALERT: {len(similar_complaints)} similar complaints found at this branch in the last 30 days. This may be a systemic issue."

        user_message = f"""Evaluate this complaint for escalation:

COMPLAINT: {complaint.get('subject', 'Unknown')}
STATUS: {complaint.get('status', 'unknown')}
CATEGORY: {complaint.get('category', 'unknown')}
CURRENT LEVEL: {complaint.get('escalation_level', 0)}
FILED AT: {complaint.get('created_at', 'unknown')}
SLA DEADLINE: {complaint.get('sla_deadline', 'unknown')}
BRANCH: {complaint.get('branch_code', 'unknown')}
CUSTOMER CONTACTS: {customer_contacts} times
{history_text}
{pattern_text}

Should this complaint be escalated? If so, to what level and why?"""

        try:
            llm = ProviderFactory.get_chat_model(
                temperature=0.1,
                structured_output=EscalationDecision,
            )

            messages = [
                SystemMessage(content=self.get_system_prompt()),
                HumanMessage(content=user_message),
            ]

            result = await llm.ainvoke(messages)

            if isinstance(result, EscalationDecision):
                decision = result
            else:
                import json
                decision = EscalationDecision(**json.loads(result.content))

            if hasattr(result, "usage_metadata") and result.usage_metadata:
                self.update_token_usage(
                    result.usage_metadata.get("input_tokens", 0),
                    result.usage_metadata.get("output_tokens", 0),
                )

        except Exception as e:
            logger.error("Escalation analysis failed", error=str(e))
            return AgentOutput(
                task_id=agent_input.task_id,
                agent_type=self.config.agent_type.value,
                status="failed",
                errors=[str(e)],
                reasoning_chain=reasoning_chain,
            )

        reasoning_chain.append(self.add_reasoning_step(
            "Escalation decision made",
            {
                "should_escalate": decision.should_escalate,
                "target_level": decision.escalation_level,
                "sla_status": decision.sla_status,
                "urgency": decision.urgency,
            }
        ))

        output = AgentOutput(
            task_id=agent_input.task_id,
            agent_type=self.config.agent_type.value,
            status="completed",
            confidence=decision.confidence,
            output_data=decision.model_dump(),
            structured_output=decision.model_dump(),
            reasoning_chain=reasoning_chain,
            decision_explanation=decision.escalation_reason,
        )

        # If escalation is recommended, flag for human approval
        if decision.should_escalate:
            output.requires_approval = True
            output.approval_context = {
                "reason": "escalation_recommended",
                "target_level": decision.escalation_level,
                "sla_status": decision.sla_status,
                "urgency": decision.urgency,
                "customer_communication": decision.customer_communication,
            }

        return output
