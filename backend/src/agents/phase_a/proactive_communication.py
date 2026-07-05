"""
SBI Vishwas — Proactive Communication Agent (Agent 3)

Automatically sends complete, specific status updates the moment any
process completes — account number, card dispatch ETA, next steps.

Directly closes the "just one vague SMS, nothing else" gap from the evidence.
"""

from __future__ import annotations

import structlog
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from src.agents.base.agent_base import AgentConfig, AgentInput, AgentOutput, BaseAgent
from src.agents.providers.provider_factory import ProviderFactory
from src.config.constants import AgentType, Channel, NotificationType

logger = structlog.get_logger(__name__)


class CommunicationPlan(BaseModel):
    """Structured output for proactive communication."""
    should_communicate: bool = Field(description="Whether communication is needed now")
    communication_type: str = Field(description="Type: status_update, welcome, reminder, alert")
    urgency: str = Field(description="immediate, within_hour, next_day")

    # Content
    subject: str = Field(description="Subject line for the communication")
    body: str = Field(description="Complete, specific message body")
    key_information: list[str] = Field(
        description="Key data points included (account number, ETA, next steps, etc.)"
    )
    next_steps: list[str] = Field(description="Clear next steps for the customer")
    help_contact: str = Field(description="How to get help if needed")

    # Channel selection
    recommended_channels: list[str] = Field(description="Ordered list of channels to use")
    language: str = Field(default="en", description="Language for the communication")

    confidence: float = Field(description="Confidence in communication plan")


class ProactiveCommunicationAgent(BaseAgent):
    """
    Proactive Communication Agent.

    Responsibilities:
    - Detect when a process completes (account opened, card dispatched, etc.)
    - Generate complete, specific status updates — not vague one-liners
    - Include all relevant details: account number, card ETA, next steps, help info
    - Select appropriate channel based on customer preferences
    - Send immediately without waiting for customer to ask
    """

    def __init__(self) -> None:
        config = AgentConfig(
            agent_type=AgentType.PROACTIVE_COMMUNICATION,
            name="Proactive Communication Agent",
            phase="A",
            description="Event-driven, complete status updates across all channels",
            max_iterations=3,
            timeout_seconds=20,
            confidence_threshold=0.85,
            max_retries=2,
            available_tools=["email_tool", "sms_tool", "whatsapp_tool", "notification_tool"],
            requires_human_approval=False,
        )
        super().__init__(config)

    def get_system_prompt(self) -> str:
        return """You are the Proactive Communication Agent for SBI Vishwas.

YOUR MISSION:
When something happens in a customer's banking journey, tell them EVERYTHING they need to know, IMMEDIATELY, without them having to ask.

THE PROBLEM YOU SOLVE:
The evidence shows customers receiving "one vague SMS with no details" after account opening — no account number, no card timeline, no next steps. That stops now.

COMMUNICATION RULES:
1. BE COMPLETE: Include all relevant details — account number, reference numbers, timelines, next steps
2. BE SPECIFIC: "Your card will be dispatched within 7 business days" not "We'll send your card soon"
3. BE ACTIONABLE: Every message must include what the customer should do next
4. BE HUMAN: Write like a helpful person, not a system notification
5. INCLUDE HELP: Always include how to get help if something goes wrong

LANGUAGE: Default to the customer's preferred language. Always be clear and jargon-free.

CHANNEL SELECTION:
- WhatsApp: For customers who opted in — rich content, links
- SMS: For all — keep under 160 chars per segment, essential info only
- Email: For detailed communications — full details, attachments
- YONO: For digitally active customers — in-app notifications

OUTPUT: Provide a structured communication plan with complete message content."""

    def get_structured_output_schema(self) -> type[BaseModel] | None:
        return CommunicationPlan

    async def execute(self, agent_input: AgentInput) -> AgentOutput:
        """
        Generate proactive communication based on a banking event.

        Expected input_data:
        - event_type: str — What happened (account_opened, card_dispatched, etc.)
        - event_data: dict — Details of the event
        - customer_profile: dict — Customer info including preferences
        """
        event_type = agent_input.input_data.get("event_type", "")
        event_data = agent_input.input_data.get("event_data", {})
        customer_profile = agent_input.input_data.get("customer_profile", {})

        reasoning_chain = []
        reasoning_chain.append(self.add_reasoning_step(
            "Processing banking event for communication",
            {"event_type": event_type, "has_profile": bool(customer_profile)}
        ))

        user_message = f"""A banking event has occurred that requires customer communication:

EVENT TYPE: {event_type}
EVENT DETAILS: {event_data}

CUSTOMER PROFILE:
- Name: {customer_profile.get('name', 'Customer')}
- Preferred Language: {customer_profile.get('preferred_language', 'en')}
- Preferred Channel: {customer_profile.get('preferred_channel', 'sms')}
- WhatsApp Opted In: {customer_profile.get('whatsapp_opted_in', False)}
- Email Available: {bool(customer_profile.get('email'))}

Generate a complete, specific communication plan with the actual message content.
Include ALL relevant details — no vague messages."""

        try:
            llm = ProviderFactory.get_chat_model(
                temperature=0.3,
                structured_output=CommunicationPlan,
            )

            messages = [
                SystemMessage(content=self.get_system_prompt()),
                HumanMessage(content=user_message),
            ]

            result = await llm.ainvoke(messages)

            if isinstance(result, CommunicationPlan):
                plan = result
            else:
                import json
                plan = CommunicationPlan(**json.loads(result.content))

            if hasattr(result, "usage_metadata") and result.usage_metadata:
                self.update_token_usage(
                    result.usage_metadata.get("input_tokens", 0),
                    result.usage_metadata.get("output_tokens", 0),
                )

        except Exception as e:
            logger.error("Communication planning failed", error=str(e))
            return AgentOutput(
                task_id=agent_input.task_id,
                agent_type=self.config.agent_type.value,
                status="failed",
                errors=[str(e)],
                reasoning_chain=reasoning_chain,
            )

        reasoning_chain.append(self.add_reasoning_step(
            "Communication plan generated",
            {
                "should_communicate": plan.should_communicate,
                "type": plan.communication_type,
                "channels": plan.recommended_channels,
                "urgency": plan.urgency,
            }
        ))

        return AgentOutput(
            task_id=agent_input.task_id,
            agent_type=self.config.agent_type.value,
            status="completed",
            confidence=plan.confidence,
            output_data=plan.model_dump(),
            structured_output=plan.model_dump(),
            reasoning_chain=reasoning_chain,
            decision_explanation=(
                f"Communication {'needed' if plan.should_communicate else 'not needed'}. "
                f"Type: {plan.communication_type}. Urgency: {plan.urgency}. "
                f"Channels: {', '.join(plan.recommended_channels)}."
            ),
        )
