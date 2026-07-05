"""
SBI Vishwas — Long-Term Memory

Persistent storage of key facts and relationship history in PostgreSQL.
"""

from __future__ import annotations

import uuid
from typing import Any

import structlog
from sqlalchemy import select

from src.agents.memory.core import BaseMemoryProvider
from src.database.engine import get_transactional_session
from src.database.models.domain import AgentMemory

logger = structlog.get_logger(__name__)


class LongTermMemory(BaseMemoryProvider):
    """PostgreSQL-backed persistent long-term memory."""

    async def add_memory(self, customer_id: uuid.UUID, content: str, **kwargs) -> bool:
        """Store a fact in PostgreSQL."""
        try:
            async with get_transactional_session() as session:
                memory = AgentMemory(
                    customer_id=customer_id,
                    memory_type=kwargs.get("memory_type", "fact"),
                    content=content,
                    importance_score=kwargs.get("importance", 0.5),
                    key=kwargs.get("key"),  # E.g., 'preferred_language'
                )
                session.add(memory)
                # Let session commit handle the rest
            return True
        except Exception as e:
            logger.error("Failed to add long-term memory", error=str(e))
            return False

    async def get_memories(self, customer_id: uuid.UUID, query: str | None = None, limit: int = 5) -> list[dict]:
        """Retrieve recent high-importance facts."""
        try:
            async with get_transactional_session() as session:
                # Basic retrieval - order by importance and recency
                # A more advanced implementation would use pgvector or text search
                stmt = select(AgentMemory).where(
                    AgentMemory.customer_id == customer_id,
                    AgentMemory.is_deleted == False
                ).order_by(
                    AgentMemory.importance_score.desc(),
                    AgentMemory.created_at.desc()
                ).limit(limit)
                
                result = await session.execute(stmt)
                memories = result.scalars().all()

                formatted = []
                for m in memories:
                    formatted.append({
                        "source": f"Fact ({m.memory_type})",
                        "content": m.content,
                        "importance": m.importance_score,
                    })

                return formatted
                
        except Exception as e:
            logger.error("Long-term memory retrieval failed", error=str(e))
            return []
