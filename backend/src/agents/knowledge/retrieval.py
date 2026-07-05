"""
SBI Vishwas — Knowledge Retrieval Pipeline

Performs semantic search on the Qdrant vector store to fetch relevant
policy clauses and documents.
"""

from __future__ import annotations

import structlog
from qdrant_client.http import models as rest

from src.agents.providers.provider_factory import ProviderFactory
from src.database.vector_store import POLICIES_COLLECTION, vector_store

logger = structlog.get_logger(__name__)


class RetrievalPipeline:
    """Retrieves context from the knowledge base using semantic search."""

    async def search_policies(
        self,
        query: str,
        limit: int = 5,
        categories: list[str] | None = None,
        score_threshold: float = 0.70,
    ) -> list[dict]:
        """
        Search for relevant policy documents.
        
        Args:
            query: The search query string
            limit: Maximum number of chunks to return
            categories: Optional list of policy categories to filter by
            score_threshold: Minimum similarity score (0-1)
            
        Returns:
            List of dictionaries containing chunk text and metadata
        """
        logger.info("Semantic search initiated", query=query[:50], limit=limit)

        try:
            # 1. Embed the query
            embeddings_model = ProviderFactory.get_embedding_model()
            query_vector = await embeddings_model.aembed_query(query)

            # 2. Build filter conditions if needed
            filter_conditions = None
            if categories:
                filter_conditions = rest.Filter(
                    must=[
                        rest.FieldCondition(
                            key="category",
                            match=rest.MatchAny(any=categories)
                        )
                    ]
                )

            # 3. Search Qdrant
            results = await vector_store.search(
                collection_name=POLICIES_COLLECTION,
                query_vector=query_vector,
                limit=limit,
                filter_conditions=filter_conditions,
                score_threshold=score_threshold,
            )

            # 4. Format results
            formatted_results = []
            for hit in results:
                payload = hit.payload or {}
                formatted_results.append({
                    "text": payload.get("text", ""),
                    "title": payload.get("title", "Unknown Policy"),
                    "source_type": payload.get("source_type", "Unknown"),
                    "category": payload.get("category", "Unknown"),
                    "score": hit.score,
                    "entry_id": payload.get("entry_id"),
                })

            logger.info("Search complete", results_found=len(formatted_results))
            return formatted_results

        except Exception as e:
            logger.error("Search failed", error=str(e))
            return []
