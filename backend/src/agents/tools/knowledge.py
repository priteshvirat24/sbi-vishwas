"""
SBI Vishwas — Knowledge & Info Tools

Tools for querying the CRM, knowledge base, and policy engine.
"""

from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, Field

from src.agents.knowledge.rag_engine import rag_engine
from src.agents.tools.core import BaseTool, register_tool


class KnowledgeSearchInput(BaseModel):
    query: str = Field(description="The question or statement to check against policies.")
    context: str = Field(default="", description="Additional context to refine the search.")


@register_tool
class KnowledgeSearchTool(BaseTool):
    """Explicit knowledge base search tool."""
    
    name = "knowledge_search"
    description = "Search the official RBI and SBI policy knowledge base for rules and guidelines."
    args_schema = KnowledgeSearchInput

    async def arun(self, query: str, context: str = "") -> str:
        """Query the RAG engine."""
        results = await rag_engine.get_policy_context(query, context)
        if not results:
            return "No relevant policy documents found."
            
        return "\n\n".join(results)


class CRMQueryInput(BaseModel):
    customer_id: str = Field(description="UUID of the customer to look up.")
    include_history: bool = Field(default=True, description="Whether to include past conversation history.")


@register_tool
class CRMQueryTool(BaseTool):
    """Tool to lookup customer details from CRM."""
    
    name = "crm_tool"
    description = "Lookup customer profile, relationship value, and past interactions."
    args_schema = CRMQueryInput

    async def arun(self, customer_id: str, include_history: bool = True) -> str:
        """Fetch CRM data (simulated integration)."""
        # In production, this calls the actual CRM DB or API
        from sqlalchemy import select
        from src.database.engine import get_transactional_session
        from src.database.models.customer import Customer
        import uuid

        try:
            cid = uuid.UUID(customer_id)
            async with get_transactional_session() as session:
                result = await session.execute(select(Customer).where(Customer.id == cid))
                customer = result.scalar_one_or_none()
                
                if not customer:
                    return f"Customer {customer_id} not found."
                    
                data = {
                    "customer_id": str(customer.id),
                    "name": "REDACTED" if customer.full_name_encrypted else "Unknown",
                    "type": customer.customer_type,
                    "risk_rating": customer.risk_rating,
                    "segment": customer.segment,
                }
                
                return json.dumps(data, indent=2)
                
        except Exception as e:
            return f"Error querying CRM: {str(e)}"
