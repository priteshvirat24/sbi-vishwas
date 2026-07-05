"""
SBI Vishwas — Core Memory System

Base interfaces and orchestration for the multi-tiered memory system.
"""

from __future__ import annotations

import abc
import uuid
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class BaseMemoryProvider(abc.ABC):
    """Abstract base class for memory tiers."""

    @abc.abstractmethod
    async def add_memory(self, customer_id: uuid.UUID, content: str, **kwargs) -> bool:
        """Add a memory to this tier."""
        pass

    @abc.abstractmethod
    async def get_memories(self, customer_id: uuid.UUID, query: str | None = None, limit: int = 5) -> list[dict]:
        """Retrieve memories from this tier."""
        pass


class MemoryManager:
    """
    Orchestrates memory operations across all tiers:
    - Short-term (conversation state)
    - Semantic (vector database)
    - Long-term (PostgreSQL)
    """

    def __init__(self):
        # We'll inject specific providers here
        self._providers = {}

    def register_provider(self, name: str, provider: BaseMemoryProvider) -> None:
        """Register a memory provider tier."""
        self._providers[name] = provider

    async def remember(self, customer_id: uuid.UUID, content: str, memory_type: str = "general", **kwargs) -> bool:
        """Store a memory in the appropriate tier(s)."""
        logger.info("Storing memory", customer_id=str(customer_id), memory_type=memory_type)
        
        success = True
        for name, provider in self._providers.items():
            # In a full implementation, we'd route based on memory_type or rules
            try:
                res = await provider.add_memory(customer_id, content, memory_type=memory_type, **kwargs)
                if not res:
                    success = False
            except Exception as e:
                logger.error("Memory storage failed for provider", provider=name, error=str(e))
                success = False
                
        return success

    async def recall(self, customer_id: uuid.UUID, query: str, limit: int = 5) -> list[str]:
        """Recall relevant memories across all tiers based on a query."""
        logger.info("Recalling memories", customer_id=str(customer_id), query=query[:30])
        
        all_memories = []
        for name, provider in self._providers.items():
            try:
                memories = await provider.get_memories(customer_id, query, limit=limit)
                all_memories.extend(memories)
            except Exception as e:
                logger.error("Memory recall failed for provider", provider=name, error=str(e))

        # Deduplicate and sort by relevance/importance if we had score data
        # For now, just return formatted strings
        
        formatted = []
        for m in all_memories[:limit]:
            formatted.append(f"[{m.get('source', 'Unknown')}] {m.get('content', '')}")
            
        return formatted

# Global manager instance
memory_manager = MemoryManager()
