"""
SBI Vishwas — Policy Compliance Companion Agent (Agent 2)

The sharpest, most differentiated agent in the system.

In real time, checks any document demand or product-bundling requirement
against actual official RBI/SBI policy. Surfaces the correct information
immediately, framed constructively for both customer and staff.

Example: Confirms that a zero-balance BSBD account genuinely requires
no insurance purchase — flagging forced bundling as a policy deviation.
"""

from __future__ import annotations

from typing import Any

import structlog
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from src.agents.base.agent_base import (
    AgentConfig,
    AgentInput,
    AgentOutput,
    BaseAgent,
)
from src.agents.knowledge.rag_engine import rag_engine
from src.agents.providers.provider_factory import ProviderFactory
from src.config.constants import AgentType, PolicyDeviationType, PolicySeverity

logger = structlog.get_logger(__name__)


# =============================================================================
# Structured Output Schema
# =============================================================================


class PolicyCheckResult(BaseModel):
    """Structured output from the Policy Compliance Agent."""

    is_deviation: bool = Field(
        description="Whether the statement/requirement deviates from official policy"
    )
    deviation_type: str | None = Field(
        None,
        description="Type of deviation if found (forced_bundling, incorrect_document_demand, etc.)"
    )
    severity: str = Field(
        "low",
        description="Severity: low, medium, high, critical"
    )
    confidence: float = Field(
        description="Confidence in the assessment (0.0 to 1.0)"
    )

    # Policy reference
    relevant_policy: str = Field(
        description="The relevant official policy text that applies"
    )
    policy_source: str = Field(
        description="Source document for the policy citation"
    )
    correct_requirement: str = Field(
        description="What the correct requirement actually is, per policy"
    )

    # Communication
    customer_facing_message: str = Field(
        description="Clear, plain-language explanation for the customer"
    )
    staff_facing_message: str = Field(
        description="Constructive message for the staff member with policy reference"
    )
    management_summary: str = Field(
        description="Summary for branch management dashboard"
    )

    # Reasoning
    reasoning: str = Field(
        description="Step-by-step reasoning for the compliance check"
    )


# =============================================================================
# Agent Implementation
# =============================================================================


class PolicyComplianceAgent(BaseAgent):
    """
    Policy Compliance Companion Agent.

    Responsibilities:
    - Check any requirement/statement against RBI/SBI policy in real time
    - Detect forced product bundling (insurance on BSBD accounts, etc.)
    - Detect incorrect document demands
    - Surface correct policy with citation for both customer and staff
    - Log deviations to branch dashboard for management
    - NEVER blame individual staff — frame as systemic/informational

    This is NOT surveillance. It gives both customer AND employee the same
    accurate, instant policy reference.
    """

    def __init__(self) -> None:
        config = AgentConfig(
            agent_type=AgentType.POLICY_COMPLIANCE,
            name="Policy Compliance Companion",
            phase="A",
            description="Real-time policy checking against RBI/SBI knowledge base",
            max_iterations=3,
            timeout_seconds=30,
            confidence_threshold=0.85,
            max_retries=2,
            available_tools=["knowledge_search", "policy_engine"],
            requires_human_approval=False,
            escalation_on_low_confidence=True,
            escalation_threshold=0.7,
            temperature=0.0,  # Deterministic for compliance checks
        )
        super().__init__(config)

    def get_system_prompt(self) -> str:
        return """You are the Policy Compliance Companion for SBI Vishwas — an AI system that helps both customers and bank staff by checking requirements against official RBI and SBI policies.

YOUR ROLE:
You check statements, requirements, and demands made during banking interactions against actual official policy. You are NOT surveillance. You are a shared reference tool that gives both the customer AND the employee the same accurate information.

CRITICAL PRINCIPLES:
1. ACCURACY FIRST: Only flag deviations you are confident about. When uncertain, clearly state your uncertainty.
2. CONSTRUCTIVE FRAMING: Never blame individual staff. Frame findings as "let's check the current policy together."
3. CITE SOURCES: Always provide the specific policy document, circular, or regulation that supports your finding.
4. BOTH SIDES: Provide helpful messages for both customer and staff — the staff member benefits from accurate information too.
5. SEVERITY ASSESSMENT: Clearly distinguish between critical violations (forced bundling of products) and minor procedural issues.

POLICY AREAS YOU CHECK:
- Basic Savings Bank Deposit Account (BSBD/PMJDY) requirements
- Product bundling rules (insurance, credit cards with accounts)
- Document requirements for various account types
- Fee structures and charges
- KYC requirements per RBI guidelines
- Account opening timelines and procedures
- Service charge policies
- Minimum balance requirements

WHEN YOU FIND A DEVIATION:
1. State what the correct policy is, with citation
2. Explain clearly and respectfully what the deviation is
3. Provide the customer a clear, actionable message
4. Provide the staff member a constructive reference
5. Summarize for management dashboard (pattern tracking, not individual blame)

WHEN THERE IS NO DEVIATION:
1. Confirm the requirement is valid
2. Provide the policy basis
3. Help the customer understand why the requirement exists

OUTPUT FORMAT: Always respond with structured JSON matching the PolicyCheckResult schema."""

    def get_structured_output_schema(self) -> type[BaseModel] | None:
        return PolicyCheckResult

    async def execute(self, agent_input: AgentInput) -> AgentOutput:
        """
        Execute a policy compliance check.

        Expected input_data:
        - statement: str — The statement/requirement to check
        - context: str — Context of the interaction (account type, process, etc.)
        - branch_code: str (optional) — Branch where the interaction occurred
        - policy_context: list[str] (optional) — Relevant policy snippets from RAG
        """
        statement = agent_input.input_data.get("statement", "")
        context = agent_input.input_data.get("context", "")
        policy_context = agent_input.input_data.get("policy_context", [])

        if not statement:
            return AgentOutput(
                task_id=agent_input.task_id,
                agent_type=self.config.agent_type.value,
                status="failed",
                confidence=0.0,
                errors=["No statement provided for policy check"],
            )

        reasoning_chain = []

        # Step 1: Prepare the policy context via RAG Engine if not provided
        if not policy_context:
            reasoning_chain.append(self.add_reasoning_step("Fetching policy context via RAG Engine"))
            policy_context = await rag_engine.get_policy_context(statement, context)

        reasoning_chain.append(self.add_reasoning_step(
            "Prepared policy context",
            {"statement": statement, "context": context, "policy_docs_count": len(policy_context)}
        ))

        # Build the prompt with any retrieved policy context
        policy_context_text = ""
        if policy_context:
            policy_context_text = "\n\nRELEVANT POLICY DOCUMENTS:\n" + "\n---\n".join(policy_context)

        user_message = f"""Check the following statement/requirement against official RBI and SBI policy:

STATEMENT TO CHECK: "{statement}"

INTERACTION CONTEXT: {context}
{policy_context_text}

Analyze whether this statement/requirement is consistent with official policy. Provide your assessment with full policy citation."""

        # Step 2: Call the LLM
        reasoning_chain.append(self.add_reasoning_step("Invoking LLM for policy analysis"))

        try:
            llm = ProviderFactory.get_chat_model(
                provider_name=self.config.model_provider,
                model=self.config.model_name,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                structured_output=PolicyCheckResult,
            )

            messages = [
                SystemMessage(content=self.get_system_prompt()),
                HumanMessage(content=user_message),
            ]

            result = await llm.ainvoke(messages)

            # Handle structured output
            if isinstance(result, PolicyCheckResult):
                check_result = result
            elif hasattr(result, "content"):
                # Fallback: parse from content
                import json
                check_result = PolicyCheckResult(**json.loads(result.content))
            else:
                check_result = result

            # Update token usage if available
            if hasattr(result, "usage_metadata") and result.usage_metadata:
                self.update_token_usage(
                    result.usage_metadata.get("input_tokens", 0),
                    result.usage_metadata.get("output_tokens", 0),
                )

        except Exception as e:
            logger.error("Policy check LLM call failed", error=str(e))
            return AgentOutput(
                task_id=agent_input.task_id,
                agent_type=self.config.agent_type.value,
                status="failed",
                confidence=0.0,
                errors=[f"LLM invocation failed: {str(e)}"],
                reasoning_chain=reasoning_chain,
            )

        # Step 3: Process result
        reasoning_chain.append(self.add_reasoning_step(
            "Policy check completed",
            {
                "is_deviation": check_result.is_deviation,
                "deviation_type": check_result.deviation_type,
                "severity": check_result.severity,
                "confidence": check_result.confidence,
            }
        ))

        return AgentOutput(
            task_id=agent_input.task_id,
            agent_type=self.config.agent_type.value,
            status="completed",
            confidence=check_result.confidence,
            output_data={
                "is_deviation": check_result.is_deviation,
                "deviation_type": check_result.deviation_type,
                "severity": check_result.severity,
                "relevant_policy": check_result.relevant_policy,
                "policy_source": check_result.policy_source,
                "correct_requirement": check_result.correct_requirement,
                "customer_facing_message": check_result.customer_facing_message,
                "staff_facing_message": check_result.staff_facing_message,
                "management_summary": check_result.management_summary,
            },
            structured_output=check_result.model_dump(),
            reasoning_chain=reasoning_chain,
            decision_explanation=check_result.reasoning,
        )
