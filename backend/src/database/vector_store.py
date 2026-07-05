"""
SBI Vishwas — Vector Store (Qdrant)

Manages connections and collections in Qdrant for semantic search.
Supports both policy knowledge base and agent semantic memory.
"""

from __future__ import annotations

import structlog
from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models as rest

from src.config.settings import get_settings

logger = structlog.get_logger(__name__)

# Constants
POLICIES_COLLECTION = "sbi_policies"
MEMORIES_COLLECTION = "agent_memories"
EMBEDDING_DIMENSIONS = {
    "text-embedding-004": 768,  # Gemini default
    "text-embedding-3-small": 1536,  # OpenAI default
    "all-MiniLM-L6-v2": 384,  # Local default
}


class VectorStoreManager:
    """Manages Qdrant collections and operations."""

    def __init__(self):
        settings = get_settings()
        self.client = AsyncQdrantClient(
            url=f"http://{settings.qdrant_host}:{settings.qdrant_port}",
            timeout=10,
        )
        self.vector_size = EMBEDDING_DIMENSIONS.get(settings.embedding_model, 768)

    async def initialize_collections(self) -> None:
        """Create collections if they don't exist."""
        try:
            collections = await self.client.get_collections()
            collection_names = [c.name for c in collections.collections]

            for col_name in [POLICIES_COLLECTION, MEMORIES_COLLECTION]:
                if col_name not in collection_names:
                    logger.info("Creating Qdrant collection", collection=col_name)
                    await self.client.create_collection(
                        collection_name=col_name,
                        vectors_config=rest.VectorParams(
                            size=self.vector_size,
                            distance=rest.Distance.COSINE,
                        ),
                    )
        except Exception as e:
            logger.error("Failed to initialize Qdrant collections", error=str(e))
            raise

    async def upsert_vectors(
        self,
        collection_name: str,
        points: list[rest.PointStruct],
    ) -> bool:
        """Upsert vectors into a collection."""
        try:
            await self.client.upsert(
                collection_name=collection_name,
                points=points,
            )
            return True
        except Exception as e:
            logger.error("Failed to upsert vectors", collection=collection_name, error=str(e))
            return False

    async def search(
        self,
        collection_name: str,
        query_vector: list[float],
        limit: int = 5,
        filter_conditions: rest.Filter | None = None,
        score_threshold: float = 0.5,
    ) -> list[rest.ScoredPoint]:
        """Perform similarity search with optional filtering."""
        try:
            results = await self.client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=limit,
                query_filter=filter_conditions,
                score_threshold=score_threshold,
                with_payload=True,
            )
            return results
        except Exception as e:
            logger.error("Semantic search failed", collection=collection_name, error=str(e))
            return []


# Global instance
vector_store = VectorStoreManager()
