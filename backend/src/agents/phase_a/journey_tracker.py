"""
SBI Vishwas — Journey Tracker Agent (Agent 1)

Maintains a single, persistent case file per customer from first contact
through resolution. No customer is ever forced to re-explain themselves
after being transferred — directly fixing the "transferred six times" failure.
"""

from __future__ import annotations

from typing import Any

import structlog
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from src.agents.base.agent_base import AgentConfig, AgentInput, AgentOutput, BaseAgent
from src.agents.providers.provider_factory import ProviderFactory
from src.config.constants import AgentType, Channel

logger = structlog.get_logger(__name__)


class JourneyAnalysis(BaseModel):
    """Structured output from Journey Tracker."""
    existing_case_id: str | None = Field(
        None, description="ID of existing case this contact belongs to, if any"
    )
    is_new_case: bool = Field(description="Whether this is a new case or continuation")
    case_summary: str = Field(description="Current summary of the customer's journey/case")
    channels_traversed: list[str] = Field(description="All channels this case has touched")
    unresolved_issues: list[str] = Field(description="List of unresolved issues from case history")
    context_for_next_agent: str = Field(
        description="Key context the next agent needs — so the customer never repeats themselves"
    )
    recommended_action: str = Field(description="Recommended next action")
    urgency: str = Field(description="low, medium, high, critical")
    confidence: float = Field(description="Confidence in case linking (0.0 to 1.0)")


class JourneyTrackerAgent(BaseAgent):
    """
    Journey Tracker Agent — maintains cross-channel case continuity.

    Responsibilities:
    - Link new contacts to existing cases
    - Preserve full context across channel switches
    - Track all touchpoints and interactions
    - Generate context summaries for downstream agents
    - Identify unresolved issues from history
    - Ensure no customer re-explains themselves after transfer
    """

    def __init__(self) -> None:
        config = AgentConfig(
            agent_type=AgentType.JOURNEY_TRACKER,
            name="Journey Tracker Agent",
            phase="A",
            description="Cross-channel case file maintenance and context preservation",
            max_iterations=5,
            timeout_seconds=30,
            confidence_threshold=0.80,
            max_retries=2,
            available_tools=["crm_tool", "knowledge_search"],
            requires_human_approval=False,
            use_long_term_memory=True,
            use_semantic_memory=True,
        )
        super().__init__(config)

    def get_system_prompt(self) -> str:
        return """You are the Journey Tracker Agent for SBI Vishwas. Your job is to maintain a single, persistent case file per customer that follows them across every channel — branch, call center, WhatsApp, app, web.

YOUR CORE MISSION:
No customer should EVER have to re-explain their situation after being transferred. The "transferred six times, each time starting over" failure mode must never happen.

WHAT YOU DO:
1. When a new contact comes in, determine if it belongs to an existing case or is a new issue.
2. If existing: pull all relevant context, generate a summary so the next agent has full history.
3. If new: create a case file with all initial context.
4. Track every channel the customer has used.
5. Identify unresolved issues from previous interactions.
6. Generate a context package that downstream agents can use immediately.

CASE LINKING SIGNALS:
- Same customer ID/CIF across channels
- Similar topic/issue within recent timeframe
- References to previous interactions in current message
- Unresolved items from prior cases

OUTPUT: Generate structured analysis of the case status and context for downstream agents."""

    def get_structured_output_schema(self) -> type[BaseModel] | None:
        return JourneyAnalysis

    async def execute(self, agent_input: AgentInput) -> AgentOutput:
        """
        Analyze incoming contact and link to existing case or create new one.

        Expected input_data:
        - current_message: str — The customer's current message/contact
        - channel: str — Current channel (branch, whatsapp, call_center, etc.)
        - customer_history: list[dict] — Previous interactions/cases
        - customer_profile: dict — Basic customer info
        """
        current_message = agent_input.input_data.get("current_message", "")
        channel = agent_input.input_data.get("channel", "unknown")
        customer_history = agent_input.input_data.get("customer_history", [])
        customer_profile = agent_input.input_data.get("customer_profile", {})

        reasoning_chain = []
        reasoning_chain.append(self.add_reasoning_step(
            "Analyzing incoming contact",
            {
                "channel": channel,
                "history_items": len(customer_history),
                "has_profile": bool(customer_profile),
            }
        ))

        # Build context
        history_text = ""
        if customer_history:
            history_entries = []
            for h in customer_history[-10:]:  # Last 10 interactions
                history_entries.append(
                    f"- [{h.get('channel', 'unknown')}] {h.get('timestamp', 'unknown')}: "
                    f"{h.get('summary', h.get('content', 'No summary'))}"
                )
            history_text = "\n\nPREVIOUS INTERACTIONS:\n" + "\n".join(history_entries)

        profile_text = ""
        if customer_profile:
            profile_text = f"\n\nCUSTOMER PROFILE:\n- Name: {customer_profile.get('name', 'Unknown')}"
            if customer_profile.get("cif"):
                profile_text += f"\n- CIF: {customer_profile['cif']}"
            if customer_profile.get("branch"):
                profile_text += f"\n- Branch: {customer_profile['branch']}"

        user_message = f"""A customer has made contact through {channel}.

CURRENT MESSAGE/CONTACT: "{current_message}"
{profile_text}
{history_text}

Analyze this contact:
1. Does this belong to an existing case? If so, which one and why?
2. What is the full case summary including all prior context?
3. What unresolved issues exist?
4. What context does the next agent need so the customer doesn't repeat themselves?"""

        try:
            llm = ProviderFactory.get_chat_model(
                provider_name=self.config.model_provider,
                model=self.config.model_name,
                temperature=0.1,
                structured_output=JourneyAnalysis,
            )

            messages = [
                SystemMessage(content=self.get_system_prompt()),
                HumanMessage(content=user_message),
            ]

            result = await llm.ainvoke(messages)

            if isinstance(result, JourneyAnalysis):
                analysis = result
            else:
                import json
                analysis = JourneyAnalysis(**json.loads(result.content))

            if hasattr(result, "usage_metadata") and result.usage_metadata:
                self.update_token_usage(
                    result.usage_metadata.get("input_tokens", 0),
                    result.usage_metadata.get("output_tokens", 0),
                )

        except Exception as e:
            logger.error("Journey tracking failed", error=str(e))
            return AgentOutput(
                task_id=agent_input.task_id,
                agent_type=self.config.agent_type.value,
                status="failed",
                errors=[str(e)],
                reasoning_chain=reasoning_chain,
            )

        reasoning_chain.append(self.add_reasoning_step(
            "Journey analysis complete",
            {
                "is_new_case": analysis.is_new_case,
                "existing_case_id": analysis.existing_case_id,
                "unresolved_count": len(analysis.unresolved_issues),
                "urgency": analysis.urgency,
            }
        ))

        return AgentOutput(
            task_id=agent_input.task_id,
            agent_type=self.config.agent_type.value,
            status="completed",
            confidence=analysis.confidence,
            output_data=analysis.model_dump(),
            structured_output=analysis.model_dump(),
            reasoning_chain=reasoning_chain,
            decision_explanation=(
                f"{'Linked to existing case ' + analysis.existing_case_id if analysis.existing_case_id else 'Created new case'}. "
                f"Urgency: {analysis.urgency}. "
                f"{len(analysis.unresolved_issues)} unresolved issues identified."
            ),
        )
