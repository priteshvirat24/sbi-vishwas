"""
SBI Vishwas — Diagnosis Agent (Agent 5)

Classifies each dormant account's likely cause of silence from historical
CBS signals. Suppresses outreach to genuinely no-need accounts rather than
wasting effort pursuing them.
"""

from __future__ import annotations

import structlog
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from src.agents.base.agent_base import AgentConfig, AgentInput, AgentOutput, BaseAgent
from src.agents.providers.provider_factory import ProviderFactory
from src.config.constants import AgentType, DormancyCause

logger = structlog.get_logger(__name__)


class DormancyDiagnosis(BaseModel):
    """Structured output from the Diagnosis Agent."""
    primary_cause: str = Field(
        description="Primary cause of dormancy: no_dbt_linkage, lost_access, duplicate_account, seasonal_income, migrated, no_ongoing_need, kyc_expired, unknown"
    )
    primary_cause_confidence: float = Field(description="Confidence in primary cause (0.0 to 1.0)")
    secondary_causes: list[str] = Field(
        default_factory=list,
        description="Other possible causes in order of likelihood"
    )

    # Signals used
    signals_analyzed: list[str] = Field(description="CBS signals that informed the diagnosis")
    signal_summary: str = Field(description="Human-readable summary of signal analysis")

    # Recommendation
    should_pursue_reactivation: bool = Field(
        description="Whether reactivation outreach is recommended (False for no_ongoing_need)"
    )
    suppression_reason: str | None = Field(
        None,
        description="If suppressed, why outreach should not be attempted"
    )
    recommended_approach: str = Field(
        description="Recommended reactivation approach if applicable"
    )
    estimated_reactivation_difficulty: str = Field(
        description="easy, moderate, difficult, unlikely"
    )

    # Reasoning
    reasoning: str = Field(description="Step-by-step reasoning for the diagnosis")
    confidence: float = Field(description="Overall diagnosis confidence")


class DiagnosisAgent(BaseAgent):
    """
    Diagnosis Agent — classifies dormant account causes.

    Responsibilities:
    - Analyze historical CBS data patterns for each dormant account
    - Classify the likely cause of dormancy from defined categories
    - Identify accounts that should NOT be pursued (no ongoing need)
    - Recommend reactivation approach based on cause
    - Score difficulty of reactivation
    - Provide explainable reasoning for every diagnosis
    """

    def __init__(self) -> None:
        config = AgentConfig(
            agent_type=AgentType.DIAGNOSIS,
            name="Diagnosis Agent",
            phase="B",
            description="Classifies dormant account causes from historical CBS signals",
            max_iterations=5,
            timeout_seconds=45,
            confidence_threshold=0.75,
            max_retries=3,
            available_tools=["cbs_adapter", "knowledge_search"],
            requires_human_approval=False,
            use_long_term_memory=True,
        )
        super().__init__(config)

    def get_system_prompt(self) -> str:
        return """You are the Diagnosis Agent for SBI Vishwas Phase B — Dormant Account Reactivation.

YOUR MISSION:
Classify WHY a Jan Dhan / PMJDY account has gone dormant, using historical data signals. Your diagnosis determines the entire reactivation strategy.

DORMANCY CAUSES (choose from these):
1. no_dbt_linkage — Account was never linked to Direct Benefit Transfer schemes. Customer may not know the account exists or has no incentive to use it.
2. lost_access — Customer lost their passbook, forgot PIN, phone number changed, or cannot reach the branch.
3. duplicate_account — Customer has another active account (possibly at another bank) and this one became redundant.
4. seasonal_income — Customer has seasonal income patterns (agriculture, migrant labor) and the account is used only during certain months.
5. migrated — Customer has migrated to another location and the original branch is inaccessible.
6. no_ongoing_need — Customer genuinely has no need for this account. DO NOT pursue reactivation — it wastes resources and annoys the customer.
7. kyc_expired — Account was frozen/restricted due to KYC expiry.
8. unknown — Insufficient signals to classify confidently.

SIGNALS TO ANALYZE:
- Transaction history pattern (frequency, recency, amounts)
- DBT linkage status and history
- RuPay card issuance and usage
- Last transaction date and type
- Account balance trend
- Branch proximity to current registered address
- KYC document status and expiry
- Prior reactivation attempts
- Multiple accounts in the system
- Seasonal patterns in transaction history

CRITICAL RULES:
1. NEVER recommend pursuing no_ongoing_need accounts — suppressing pointless outreach is a feature
2. Always provide confidence levels — uncertain diagnoses should be flagged
3. Use ALL available signals before concluding
4. Explain your reasoning step by step — every diagnosis must be auditable

OUTPUT: Structured diagnosis with cause, confidence, and reactivation recommendation."""

    def get_structured_output_schema(self) -> type[BaseModel] | None:
        return DormancyDiagnosis

    async def execute(self, agent_input: AgentInput) -> AgentOutput:
        """
        Diagnose the cause of dormancy for an account.

        Expected input_data:
        - account: dict — Account data (balance, status, last_transaction, etc.)
        - transaction_history: list[dict] — Historical transactions
        - customer_profile: dict — Customer info
        - dbt_data: dict — DBT linkage information
        - kyc_data: dict — KYC status and expiry
        - prior_reactivation_attempts: list[dict] — Previous outreach history
        """
        account = agent_input.input_data.get("account", {})
        transaction_history = agent_input.input_data.get("transaction_history", [])
        customer_profile = agent_input.input_data.get("customer_profile", {})
        dbt_data = agent_input.input_data.get("dbt_data", {})
        kyc_data = agent_input.input_data.get("kyc_data", {})
        prior_attempts = agent_input.input_data.get("prior_reactivation_attempts", [])

        reasoning_chain = []
        reasoning_chain.append(self.add_reasoning_step(
            "Loading account signals for diagnosis",
            {
                "account_number": account.get("account_number", "unknown")[-4:] + "****",
                "account_type": account.get("account_type"),
                "current_balance": str(account.get("current_balance", 0)),
                "last_transaction": account.get("last_transaction_at"),
                "transaction_count": len(transaction_history),
                "dbt_linked": dbt_data.get("linked", False),
            }
        ))

        # Build comprehensive signal description
        txn_summary = "No transactions found."
        if transaction_history:
            txn_count = len(transaction_history)
            recent_txns = transaction_history[:5]
            txn_entries = [
                f"  - {t.get('date', 'unknown')}: {t.get('type', 'unknown')} "
                f"₹{t.get('amount', 0)} ({t.get('description', '')})"
                for t in recent_txns
            ]
            txn_summary = f"{txn_count} total transactions. Most recent:\n" + "\n".join(txn_entries)

        user_message = f"""Diagnose the cause of dormancy for this account:

ACCOUNT DATA:
- Type: {account.get('account_type', 'unknown')}
- Status: {account.get('status', 'unknown')}
- Current Balance: ₹{account.get('current_balance', 0)}
- Opened: {account.get('opened_at', 'unknown')}
- Last Transaction: {account.get('last_transaction_at', 'never')}
- Branch: {account.get('branch_code', 'unknown')}
- RuPay Card: {'Issued' if account.get('rupay_card_issued') else 'Not issued'}
- RuPay Last Used: {account.get('rupay_last_used_at', 'never')}
- Has Prior KCC: {account.get('has_prior_kcc', False)}
- Has Prior Overdraft: {account.get('has_prior_overdraft', False)}

TRANSACTION HISTORY:
{txn_summary}

DBT DATA:
- Linked: {dbt_data.get('linked', False)}
- Schemes: {dbt_data.get('scheme_count', 0)}
- Last DBT Credit: {dbt_data.get('last_credit_at', 'never')}

CUSTOMER PROFILE:
- Location: {customer_profile.get('city', 'unknown')}, {customer_profile.get('state', 'unknown')}
- Pincode: {customer_profile.get('pincode', 'unknown')}

KYC STATUS:
- Status: {kyc_data.get('status', 'unknown')}
- Expiry: {kyc_data.get('expiry_date', 'unknown')}

PRIOR REACTIVATION ATTEMPTS: {len(prior_attempts)}
{chr(10).join([f"  - {a.get('date', 'unknown')}: {a.get('channel', 'unknown')} — {a.get('result', 'unknown')}" for a in prior_attempts]) if prior_attempts else 'None'}

Diagnose the primary cause of dormancy using all available signals."""

        try:
            llm = ProviderFactory.get_chat_model(
                temperature=0.1,
                structured_output=DormancyDiagnosis,
            )

            messages = [
                SystemMessage(content=self.get_system_prompt()),
                HumanMessage(content=user_message),
            ]

            result = await llm.ainvoke(messages)

            if isinstance(result, DormancyDiagnosis):
                diagnosis = result
            else:
                import json
                diagnosis = DormancyDiagnosis(**json.loads(result.content))

            if hasattr(result, "usage_metadata") and result.usage_metadata:
                self.update_token_usage(
                    result.usage_metadata.get("input_tokens", 0),
                    result.usage_metadata.get("output_tokens", 0),
                )

        except Exception as e:
            logger.error("Dormancy diagnosis failed", error=str(e))
            return AgentOutput(
                task_id=agent_input.task_id,
                agent_type=self.config.agent_type.value,
                status="failed",
                errors=[str(e)],
                reasoning_chain=reasoning_chain,
            )

        reasoning_chain.append(self.add_reasoning_step(
            "Diagnosis complete",
            {
                "primary_cause": diagnosis.primary_cause,
                "confidence": diagnosis.primary_cause_confidence,
                "should_pursue": diagnosis.should_pursue_reactivation,
                "difficulty": diagnosis.estimated_reactivation_difficulty,
            }
        ))

        return AgentOutput(
            task_id=agent_input.task_id,
            agent_type=self.config.agent_type.value,
            status="completed",
            confidence=diagnosis.confidence,
            output_data=diagnosis.model_dump(),
            structured_output=diagnosis.model_dump(),
            reasoning_chain=reasoning_chain,
            decision_explanation=(
                f"Dormancy cause: {diagnosis.primary_cause} "
                f"(confidence: {diagnosis.primary_cause_confidence:.0%}). "
                f"{'Reactivation recommended' if diagnosis.should_pursue_reactivation else 'Outreach suppressed'}: "
                f"{diagnosis.recommended_approach}"
            ),
            next_agent=(
                AgentType.READINESS.value
                if diagnosis.should_pursue_reactivation
                else None
            ),
        )
