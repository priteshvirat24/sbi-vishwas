"""
SBI Vishwas — Core Banking System (CBS) Tools

Tools for reading account and transaction data from the CBS.
Uses the simulated DataFactory for safe data access.
"""

from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, Field

from src.adapters.cbs_adapter import cbs_data_factory
from src.agents.tools.core import BaseTool, register_tool


class CBSAccountInput(BaseModel):
    account_number: str = Field(description="The account number to query.")


@register_tool
class CBSAccountTool(BaseTool):
    """Tool to fetch account details from CBS."""
    
    name = "cbs_account_query"
    description = "Fetch account balance, status, DBT linkage, and basic details from the Core Banking System."
    args_schema = CBSAccountInput

    async def arun(self, account_number: str) -> str:
        """Fetch account data via data factory simulation."""
        # For simulation, we generate a consistent profile based on account length
        is_dormant = len(account_number) % 2 == 0
        data = cbs_data_factory.generate_complete_customer_data(force_dormant=is_dormant)
        
        # Override the generated account number with the requested one
        data["account"]["account_number"] = account_number
        
        # Strip transactions for this specific tool to save tokens
        del data["transaction_history"]
        
        return json.dumps(data, indent=2, default=str)


class CBSTransactionInput(BaseModel):
    account_number: str = Field(description="The account number to query.")
    limit: int = Field(default=10, description="Number of recent transactions to fetch.")


@register_tool
class CBSTransactionTool(BaseTool):
    """Tool to fetch transaction history from CBS."""
    
    name = "cbs_transaction_query"
    description = "Fetch recent transaction history for an account from the Core Banking System."
    args_schema = CBSTransactionInput

    async def arun(self, account_number: str, limit: int = 10) -> str:
        """Fetch transactions via data factory simulation."""
        is_dormant = len(account_number) % 2 == 0
        account = cbs_data_factory.generate_account(force_dormant=is_dormant)
        transactions = cbs_data_factory.generate_transactions(account, count=limit)
        
        result = [t.model_dump(mode="json") for t in transactions]
        return json.dumps(result, indent=2, default=str)
