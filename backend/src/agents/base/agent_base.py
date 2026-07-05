"""
SBI Vishwas — Agent Base Class

Abstract base class that every agent must implement.
Defines the full agent contract: purpose, state, tools, outputs,
retry strategy, confidence thresholds, escalation logic, metrics, and audit.
"""

from __future__ import annotations

import time
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Generic, TypeVar

import structlog
from pydantic import BaseModel, Field

from src.config.constants import AgentStatus, AgentType, AuditAction
from src.config.settings import get_settings
from src.agents.memory.core import memory_manager

logger = structlog.get_logger(__name__)

# Type variable for agent-specific state
StateT = TypeVar("StateT", bound=BaseModel)
OutputT = TypeVar("OutputT", bound=BaseModel)


class AgentConfig(BaseModel):
    """Configuration for an agent instance."""
    agent_type: AgentType
    name: str
    description: str
    phase: str  # "A" or "B" or "shared"
    version: str = "1.0.0"

    # LLM configuration
    model_provider: str | None = None  # Override default provider
    model_name: str | None = None  # Override default model
    temperature: float | None = None
    max_tokens: int | None = None

    # Execution
    max_iterations: int = 10
    timeout_seconds: int = 120
    confidence_threshold: float = 0.85
    max_retries: int = 3
    retry_delay_seconds: float = 1.0

    # Tools
    available_tools: list[str] = Field(default_factory=list)

    # Escalation
    requires_human_approval: bool = False
    escalation_on_low_confidence: bool = True
    escalation_threshold: float = 0.6

    # Memory
    use_short_term_memory: bool = True
    use_long_term_memory: bool = True
    use_semantic_memory: bool = False
    memory_window: int = 20  # Number of recent messages to include


class AgentInput(BaseModel):
    """Standard input to any agent."""
    task_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    customer_id: uuid.UUID | None = None
    conversation_id: uuid.UUID | None = None
    workflow_id: uuid.UUID | None = None
    input_data: dict[str, Any] = Field(default_factory=dict)
    context: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class AgentOutput(BaseModel):
    """Standard output from any agent."""
    task_id: uuid.UUID
    agent_type: str
    status: str = AgentStatus.COMPLETED.value
    confidence: float = 0.0
    output_data: dict[str, Any] = Field(default_factory=dict)
    structured_output: dict[str, Any] | None = None
    reasoning_chain: list[dict[str, Any]] = Field(default_factory=list)
    decision_explanation: str = ""
    tool_calls: list[dict[str, Any]] = Field(default_factory=list)
    requires_approval: bool = False
    approval_context: dict[str, Any] | None = None
    next_agent: str | None = None
    errors: list[str] = Field(default_factory=list)

    # Metrics
    model_provider: str | None = None
    model_name: str | None = None
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0
    latency_ms: int = 0


class AgentMetrics(BaseModel):
    """Runtime metrics for an agent execution."""
    start_time: float = 0.0
    end_time: float = 0.0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    tool_call_count: int = 0
    retry_count: int = 0
    iteration_count: int = 0


class BaseAgent(ABC):
    """
    Abstract base agent that all SBI Vishwas agents must implement.

    Provides:
    - Standardized execution lifecycle (prepare → execute → evaluate → audit)
    - Retry logic with exponential backoff
    - Confidence-based escalation
    - Metrics collection
    - Audit logging
    - Memory integration points
    """

    def __init__(self, config: AgentConfig) -> None:
        self.config = config
        self.settings = get_settings()
        self._metrics = AgentMetrics()

    @property
    def agent_type(self) -> AgentType:
        return self.config.agent_type

    @property
    def name(self) -> str:
        return self.config.name

    # -------------------------------------------------------------------------
    # Abstract methods — every agent must implement these
    # -------------------------------------------------------------------------

    @abstractmethod
    def get_system_prompt(self) -> str:
        """Return the system prompt for this agent."""
        ...

    @abstractmethod
    async def execute(self, agent_input: AgentInput) -> AgentOutput:
        """
        Core execution logic. Must be implemented by each agent.
        This is called by run() after preparation and before evaluation.
        """
        ...

    @abstractmethod
    def get_structured_output_schema(self) -> type[BaseModel] | None:
        """
        Return the Pydantic model for structured output, or None if not applicable.
        Used to constrain LLM output to a specific schema.
        """
        ...

    # -------------------------------------------------------------------------
    # Execution lifecycle
    # -------------------------------------------------------------------------

    async def run(self, agent_input: AgentInput) -> AgentOutput:
        """
        Full execution lifecycle with retry, metrics, and audit.

        1. Prepare (load context, memory)
        2. Execute (with retries)
        3. Evaluate (confidence check, escalation)
        4. Audit (log everything)
        """
        self._metrics = AgentMetrics(start_time=time.time())

        logger.info(
            "Agent starting",
            agent_type=self.config.agent_type.value,
            task_id=str(agent_input.task_id),
            customer_id=str(agent_input.customer_id) if agent_input.customer_id else None,
        )

        output: AgentOutput | None = None
        last_error: Exception | None = None

        for attempt in range(1, self.config.max_retries + 1):
            try:
                # Prepare context
                prepared_input = await self.prepare(agent_input)

                # Execute
                output = await self.execute(prepared_input)
                output.task_id = agent_input.task_id
                output.agent_type = self.config.agent_type.value

                # Evaluate
                output = await self.evaluate(output)

                # Success — break retry loop
                break

            except Exception as e:
                last_error = e
                self._metrics.retry_count = attempt
                logger.warning(
                    "Agent execution failed, retrying",
                    agent_type=self.config.agent_type.value,
                    attempt=attempt,
                    max_retries=self.config.max_retries,
                    error=str(e),
                )

                if attempt < self.config.max_retries:
                    import asyncio
                    await asyncio.sleep(self.config.retry_delay_seconds * attempt)

        # If all retries failed
        if output is None:
            output = AgentOutput(
                task_id=agent_input.task_id,
                agent_type=self.config.agent_type.value,
                status=AgentStatus.FAILED.value,
                confidence=0.0,
                errors=[str(last_error)] if last_error else ["Unknown error"],
                decision_explanation=f"Agent failed after {self.config.max_retries} retries",
            )

        # Record metrics
        self._metrics.end_time = time.time()
        output.latency_ms = int((self._metrics.end_time - self._metrics.start_time) * 1000)
        output.prompt_tokens = self._metrics.prompt_tokens
        output.completion_tokens = self._metrics.completion_tokens
        output.total_tokens = self._metrics.total_tokens

        # Audit
        await self.audit(agent_input, output)

        logger.info(
            "Agent completed",
            agent_type=self.config.agent_type.value,
            status=output.status,
            confidence=output.confidence,
            latency_ms=output.latency_ms,
            total_tokens=output.total_tokens,
        )

        # Memory storage (Episodic/Semantic)
        if output.status == AgentStatus.COMPLETED.value and agent_input.customer_id:
            await self._store_memory(agent_input, output)

        return output

    async def _store_memory(self, agent_input: AgentInput, output: AgentOutput) -> None:
        """Store the execution result in the memory system."""
        if not self.config.use_semantic_memory and not self.config.use_long_term_memory:
            return

        content = (
            f"Agent {self.config.name} execution completed. "
            f"Decision: {output.decision_explanation}. "
        )
        
        if self.config.use_semantic_memory:
            await memory_manager.remember(
                agent_input.customer_id, 
                content, 
                memory_type="episodic",
                importance=0.6,
                timestamp=datetime.now(timezone.utc).isoformat()
            )

    async def prepare(self, agent_input: AgentInput) -> AgentInput:
        """
        Prepare agent input by loading context, memory, and relevant data.
        Override in subclasses to add agent-specific preparation.
        """
        if self.config.use_semantic_memory and agent_input.customer_id:
            # Quick semantic recall based on recent conversation context
            query = ""
            if "current_message" in agent_input.input_data:
                query = agent_input.input_data["current_message"]
                
            if query:
                memories = await memory_manager.recall(agent_input.customer_id, query)
                if memories:
                    agent_input.context["semantic_memory"] = memories
                    
        return agent_input

    async def evaluate(self, output: AgentOutput) -> AgentOutput:
        """
        Evaluate agent output — check confidence, decide on escalation.
        """
        # Check confidence threshold
        if output.confidence < self.config.escalation_threshold:
            if self.config.escalation_on_low_confidence:
                output.requires_approval = True
                output.approval_context = {
                    "reason": "low_confidence",
                    "confidence": output.confidence,
                    "threshold": self.config.escalation_threshold,
                    "agent_type": self.config.agent_type.value,
                    "explanation": output.decision_explanation,
                }
                logger.info(
                    "Agent output requires approval (low confidence)",
                    agent_type=self.config.agent_type.value,
                    confidence=output.confidence,
                )

        # Check if agent type requires human approval
        if self.config.requires_human_approval:
            output.requires_approval = True
            if output.approval_context is None:
                output.approval_context = {}
            output.approval_context["reason"] = "required_by_policy"

        return output

    async def audit(self, agent_input: AgentInput, output: AgentOutput) -> None:
        """
        Record audit log for this agent execution.
        Override to add agent-specific audit data.
        """
        # Audit logging will write to the audit_logs table
        # This is a hook — the actual DB write happens in the orchestrator
        logger.info(
            "Agent audit recorded",
            agent_type=self.config.agent_type.value,
            action=AuditAction.AGENT_COMPLETED.value if output.status == AgentStatus.COMPLETED.value
            else AuditAction.AGENT_FAILED.value,
            confidence=output.confidence,
            tool_calls=len(output.tool_calls),
            requires_approval=output.requires_approval,
        )

    # -------------------------------------------------------------------------
    # Utility methods available to all agents
    # -------------------------------------------------------------------------

    def record_tool_call(self, tool_name: str, input_data: dict, output_data: dict, latency_ms: int = 0) -> dict:
        """Record a tool call for audit and metrics."""
        self._metrics.tool_call_count += 1
        call_record = {
            "tool_name": tool_name,
            "input": input_data,
            "output": output_data,
            "latency_ms": latency_ms,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        return call_record

    def add_reasoning_step(self, step: str, data: dict | None = None) -> dict:
        """Add a step to the reasoning chain for explainability."""
        return {
            "step": step,
            "data": data or {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def update_token_usage(self, prompt_tokens: int, completion_tokens: int) -> None:
        """Update token usage metrics."""
        self._metrics.prompt_tokens += prompt_tokens
        self._metrics.completion_tokens += completion_tokens
        self._metrics.total_tokens = self._metrics.prompt_tokens + self._metrics.completion_tokens
