"""
SBI Vishwas — Semantic Memory

Vector-based retrieval of past interactions or derived insights using Qdrant.
"""

from __future__ import annotations

import uuid
from typing import Any

import structlog
from qdrant_client.http import models as rest

from src.agents.memory.core import BaseMemoryProvider
from src.agents.providers.provider_factory import ProviderFactory
from src.database.vector_store import MEMORIES_COLLECTION, vector_store

logger = structlog.get_logger(__name__)


class SemanticMemory(BaseMemoryProvider):
    """Semantic vector-based memory tier."""

    async def add_memory(self, customer_id: uuid.UUID, content: str, **kwargs) -> bool:
        """Embed and store a memory in Qdrant."""
        try:
            # 1. Embed content
            embeddings_model = ProviderFactory.get_embedding_model()
            embedding = await embeddings_model.aembed_query(content)

            # 2. Store in Qdrant
            point_id = str(uuid.uuid4())
            memory_type = kwargs.get("memory_type", "general")
            
            payload = {
                "customer_id": str(customer_id),
                "memory_type": memory_type,
                "content": content,
                "importance": kwargs.get("importance", 0.5),
                "timestamp": kwargs.get("timestamp", ""),
            }

            point = rest.PointStruct(
                id=point_id,
                vector=embedding,
                payload=payload,
            )

            return await vector_store.upsert_vectors(MEMORIES_COLLECTION, [point])

        except Exception as e:
            logger.error("Failed to add semantic memory", error=str(e))
            return False

    async def get_memories(self, customer_id: uuid.UUID, query: str | None = None, limit: int = 5) -> list[dict]:
        """Retrieve memories by semantic similarity."""
        if not query:
            return []

        try:
            # 1. Embed query
            embeddings_model = ProviderFactory.get_embedding_model()
            query_vector = await embeddings_model.aembed_query(query)

            # 2. Filter by customer ID
            filter_conditions = rest.Filter(
                must=[
                    rest.FieldCondition(
                        key="customer_id",
                        match=rest.MatchValue(value=str(customer_id))
                    )
                ]
            )

            # 3. Search Qdrant
            results = await vector_store.search(
                collection_name=MEMORIES_COLLECTION,
                query_vector=query_vector,
                limit=limit,
                filter_conditions=filter_conditions,
                score_threshold=0.6,
            )

            # 4. Format
            formatted = []
            for hit in results:
                payload = hit.payload or {}
                formatted.append({
                    "source": f"Semantic ({payload.get('memory_type', 'general')})",
                    "content": payload.get("content", ""),
                    "score": hit.score,
                })

            return formatted

        except Exception as e:
            logger.error("Semantic memory search failed", error=str(e))
            return []
