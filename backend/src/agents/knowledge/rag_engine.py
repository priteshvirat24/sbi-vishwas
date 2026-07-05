"""
SBI Vishwas — RAG Engine

Orchestrator for Retrieval-Augmented Generation. Provides formatted
policy context for the Policy Compliance Agent.
"""

from __future__ import annotations

import structlog

from src.agents.knowledge.retrieval import RetrievalPipeline

logger = structlog.get_logger(__name__)


class RAGEngine:
    """Retrieval-Augmented Generation engine for policy compliance."""

    def __init__(self):
        self.retrieval = RetrievalPipeline()

    async def get_policy_context(
        self,
        statement: str,
        context: str = "",
        limit: int = 4
    ) -> list[str]:
        """
        Get formatted policy context relevant to a statement.
        
        Args:
            statement: The customer or staff statement to check
            context: Additional context to improve search relevance
            limit: Maximum number of policy chunks to return
            
        Returns:
            List of formatted strings containing policy text and citations
        """
        # Enhance query with context
        query = statement
        if context:
            query = f"Context: {context}\nStatement: {statement}"

        # Fetch relevant chunks
        results = await self.retrieval.search_policies(
            query=query,
            limit=limit,
        )

        if not results:
            return []

        # Format with citations
        formatted_context = []
        for res in results:
            citation = f"SOURCE: {res['title']} ({res['category']})"
            content = res['text'].strip()
            
            # Format nicely for the LLM prompt
            formatted_chunk = f"{citation}\nCONTENT:\n{content}"
            formatted_context.append(formatted_chunk)

        return formatted_context

# Global instance for easy import
rag_engine = RAGEngine()
