"""
SBI Vishwas — Readiness Agent (Agent 6)

Computes a Day-1 financial-readiness score from existing historical CBS data
(DBT receipt regularity, past overdraft/KCC conduct, prior RuPay usage).

The technical unlock: demoable immediately from historical data rather than
requiring months of new data collection.

NEVER approves anything — only classifies readiness with an explainability note.
"""

from __future__ import annotations

import structlog
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from src.agents.base.agent_base import AgentConfig, AgentInput, AgentOutput, BaseAgent
from src.agents.providers.provider_factory import ProviderFactory
from src.config.constants import READINESS_SCORE_WEIGHTS, AgentType, CreditProduct

logger = structlog.get_logger(__name__)


class ReadinessScore(BaseModel):
    """Structured output from the Readiness Agent."""

    # Overall score
    overall_score: float = Field(
        description="Overall readiness score (0.0 to 1.0)"
    )
    readiness_tier: str = Field(
        description="not_ready, emerging, ready, strong"
    )

    # Component scores
    dbt_regularity_score: float = Field(
        description="Score for DBT receipt regularity (0.0 to 1.0)"
    )
    account_balance_trend_score: float = Field(
        description="Score for account balance trend (0.0 to 1.0)"
    )
    transaction_frequency_score: float = Field(
        description="Score for transaction frequency (0.0 to 1.0)"
    )
    prior_credit_conduct_score: float = Field(
        description="Score for prior KCC/overdraft conduct (0.0 to 1.0)"
    )
    digital_engagement_score: float = Field(
        description="Score for digital engagement / RuPay usage (0.0 to 1.0)"
    )
    kyc_completeness_score: float = Field(
        description="Score for KYC completeness (0.0 to 1.0)"
    )

    # Explainability
    score_explanation: str = Field(
        description="Plain-language explanation of how the score was computed"
    )
    strengths: list[str] = Field(description="Financial strengths identified")
    risk_factors: list[str] = Field(description="Risk factors or gaps identified")

    # Product recommendation (advisory only — never approves)
    recommended_products: list[str] = Field(
        description="Credit products this customer may be ready for"
    )
    recommended_ticket_size: float = Field(
        description="Suggested maximum ticket size in INR"
    )
    product_rationale: str = Field(
        description="Why these products are recommended"
    )

    # Meta
    data_quality_score: float = Field(
        description="Quality of input data used (0.0 to 1.0) — flags if insufficient data"
    )
    data_gaps: list[str] = Field(description="Missing data that would improve the score")
    confidence: float = Field(description="Confidence in the overall assessment")


class ReadinessAgent(BaseAgent):
    """
    Readiness Agent — Day-1 credit readiness scoring from historical data.

    Responsibilities:
    - Compute readiness score from existing CBS data signals
    - Weight components: DBT regularity, balance trend, transactions,
      prior credit conduct, digital engagement, KYC
    - Provide explainable score breakdown
    - Recommend appropriate credit products (advisory only)
    - NEVER approve any credit — only classify readiness
    - Identify data gaps that would improve scoring
    - Continuously refine as post-reactivation data accrues
    """

    def __init__(self) -> None:
        config = AgentConfig(
            agent_type=AgentType.READINESS,
            name="Readiness Agent",
            phase="B",
            description="Day-1 financial readiness scoring from historical CBS data",
            max_iterations=3,
            timeout_seconds=45,
            confidence_threshold=0.75,
            max_retries=3,
            available_tools=["cbs_adapter"],
            requires_human_approval=False,
            temperature=0.0,  # Deterministic scoring
        )
        super().__init__(config)

    def get_system_prompt(self) -> str:
        weights = READINESS_SCORE_WEIGHTS
        return f"""You are the Readiness Agent for SBI Vishwas Phase B.

YOUR MISSION:
Compute a Day-1 financial readiness score for dormant/reactivated Jan Dhan account holders using EXISTING historical data. This score determines whether a customer is ready for a first formal credit product.

CRITICAL RULE: You NEVER approve credit. You CLASSIFY readiness. A human always makes the final credit decision.

SCORING COMPONENTS (with weights):
1. DBT Regularity (weight: {weights['dbt_regularity']:.0%}): How regularly does the customer receive Direct Benefit Transfer credits? Regular DBT = stable income signal.
2. Account Balance Trend (weight: {weights['account_balance_trend']:.0%}): Is the average balance stable, growing, or declining? Savings behavior signal.
3. Transaction Frequency (weight: {weights['transaction_frequency']:.0%}): How actively does the customer use the account? Digital and branch transactions.
4. Prior Credit Conduct (weight: {weights['prior_credit_conduct']:.0%}): Has the customer had a KCC, overdraft, or other credit? How was it conducted?
5. Digital Engagement (weight: {weights['digital_engagement']:.0%}): RuPay card usage, YONO activity, UPI transactions. Digital readiness signal.
6. KYC Completeness (weight: {weights['kyc_completeness']:.0%}): Is KYC current and complete? Required for any credit product.

READINESS TIERS:
- not_ready (0.0-0.39): Insufficient signals or high risk factors
- emerging (0.40-0.59): Some positive signals but gaps exist
- ready (0.60-0.79): Good signals, suitable for small-ticket credit
- strong (0.80-1.0): Strong history, suitable for standard credit products

CREDIT PRODUCTS (recommend only if ready/strong):
- KCC (Kisan Credit Card) — for agricultural customers
- KCC top-up — for existing KCC holders
- Mudra loan — for micro-enterprise customers
- Personal loan (small-ticket) — for salaried/steady income
- Overdraft — for accounts with consistent balance

EXPLAINABILITY:
Every score must come with a plain-language explanation that a branch manager or the customer can understand. No black-box scoring.

OUTPUT: Structured readiness score with full component breakdown and explanation."""

    def get_structured_output_schema(self) -> type[BaseModel] | None:
        return ReadinessScore

    async def execute(self, agent_input: AgentInput) -> AgentOutput:
        """
        Compute readiness score for an account.

        Expected input_data:
        - account: dict — Account data with balances, transaction summaries
        - transaction_history: list[dict] — Historical transactions
        - dbt_data: dict — DBT receipt history
        - kyc_data: dict — KYC status
        - prior_credit: dict — Prior credit product history
        - diagnosis: dict — Diagnosis agent output (dormancy cause)
        """
        account = agent_input.input_data.get("account", {})
        transaction_history = agent_input.input_data.get("transaction_history", [])
        dbt_data = agent_input.input_data.get("dbt_data", {})
        kyc_data = agent_input.input_data.get("kyc_data", {})
        prior_credit = agent_input.input_data.get("prior_credit", {})
        diagnosis = agent_input.input_data.get("diagnosis", {})

        reasoning_chain = []
        reasoning_chain.append(self.add_reasoning_step(
            "Loading data signals for readiness scoring",
            {
                "account_type": account.get("account_type"),
                "balance": str(account.get("current_balance", 0)),
                "dbt_linked": dbt_data.get("linked", False),
                "kyc_status": kyc_data.get("status"),
                "has_prior_credit": bool(prior_credit),
                "dormancy_cause": diagnosis.get("primary_cause"),
            }
        ))

        # Build comprehensive data for LLM analysis
        txn_summary = "No transaction data available."
        if transaction_history:
            # Aggregate transaction patterns
            total_credits = sum(t.get("amount", 0) for t in transaction_history if t.get("type") == "credit")
            total_debits = sum(t.get("amount", 0) for t in transaction_history if t.get("type") == "debit")
            txn_count = len(transaction_history)

            txn_summary = (
                f"Total transactions: {txn_count}\n"
                f"Total credits: ₹{total_credits:,.2f}\n"
                f"Total debits: ₹{total_debits:,.2f}\n"
                f"Transaction period: {transaction_history[-1].get('date', 'unknown')} to {transaction_history[0].get('date', 'unknown')}"
            )

        user_message = f"""Compute a credit readiness score for this account:

ACCOUNT DATA:
- Type: {account.get('account_type', 'unknown')}
- Current Balance: ₹{account.get('current_balance', 0):,.2f}
- Average Monthly Balance: ₹{account.get('avg_monthly_balance', 0):,.2f}
- Total Credits (12m): ₹{account.get('total_credits_12m', 0):,.2f}
- Total Debits (12m): ₹{account.get('total_debits_12m', 0):,.2f}
- Transaction Count (12m): {account.get('transaction_count_12m', 0)}
- RuPay Card Issued: {account.get('rupay_card_issued', False)}
- RuPay Last Used: {account.get('rupay_last_used_at', 'never')}

TRANSACTION HISTORY SUMMARY:
{txn_summary}

DBT DATA:
- Linked: {dbt_data.get('linked', False)}
- Scheme Count: {dbt_data.get('scheme_count', 0)}
- Last DBT Credit: {dbt_data.get('last_credit_at', 'never')}
- DBT Frequency: {dbt_data.get('frequency', 'unknown')}

KYC DATA:
- Status: {kyc_data.get('status', 'unknown')}
- Expiry: {kyc_data.get('expiry_date', 'unknown')}
- Aadhaar Linked: {kyc_data.get('aadhaar_linked', False)}
- PAN Available: {kyc_data.get('pan_available', False)}

PRIOR CREDIT:
- Has Prior KCC: {prior_credit.get('has_kcc', False)}
- KCC Conduct: {prior_credit.get('kcc_conduct', 'N/A')}
- Has Prior Overdraft: {prior_credit.get('has_overdraft', False)}
- Overdraft Conduct: {prior_credit.get('overdraft_conduct', 'N/A')}

DIAGNOSIS:
- Dormancy Cause: {diagnosis.get('primary_cause', 'unknown')}
- Reactivation Difficulty: {diagnosis.get('estimated_reactivation_difficulty', 'unknown')}

Compute the readiness score with full component breakdown and explanation."""

        try:
            llm = ProviderFactory.get_chat_model(
                temperature=0.0,
                structured_output=ReadinessScore,
            )

            messages = [
                SystemMessage(content=self.get_system_prompt()),
                HumanMessage(content=user_message),
            ]

            result = await llm.ainvoke(messages)

            if isinstance(result, ReadinessScore):
                score = result
            else:
                import json
                score = ReadinessScore(**json.loads(result.content))

            if hasattr(result, "usage_metadata") and result.usage_metadata:
                self.update_token_usage(
                    result.usage_metadata.get("input_tokens", 0),
                    result.usage_metadata.get("output_tokens", 0),
                )

        except Exception as e:
            logger.error("Readiness scoring failed", error=str(e))
            return AgentOutput(
                task_id=agent_input.task_id,
                agent_type=self.config.agent_type.value,
                status="failed",
                errors=[str(e)],
                reasoning_chain=reasoning_chain,
            )

        reasoning_chain.append(self.add_reasoning_step(
            "Readiness score computed",
            {
                "overall_score": score.overall_score,
                "readiness_tier": score.readiness_tier,
                "recommended_products": score.recommended_products,
                "data_quality": score.data_quality_score,
            }
        ))

        # Route to Graduation Agent if score is above threshold
        settings = self.settings
        next_agent = None
        if score.overall_score >= settings.credit_readiness_min_score and score.readiness_tier in ("ready", "strong"):
            next_agent = AgentType.GRADUATION.value

        return AgentOutput(
            task_id=agent_input.task_id,
            agent_type=self.config.agent_type.value,
            status="completed",
            confidence=score.confidence,
            output_data=score.model_dump(),
            structured_output=score.model_dump(),
            reasoning_chain=reasoning_chain,
            decision_explanation=(
                f"Readiness: {score.readiness_tier} ({score.overall_score:.0%}). "
                f"Strengths: {', '.join(score.strengths[:3])}. "
                f"Products: {', '.join(score.recommended_products) if score.recommended_products else 'none yet'}. "
                f"Data quality: {score.data_quality_score:.0%}."
            ),
            next_agent=next_agent,
        )
