"""
SBI Vishwas — Core Tool Framework

Abstract base classes and registry for tools. Tools provide agents
with safe, structured access to external systems.
"""

from __future__ import annotations

import abc
import inspect
from typing import Any, Callable, Type

import structlog
from pydantic import BaseModel
from langchain_core.tools import BaseTool as LangChainBaseTool
from langchain_core.tools import StructuredTool

logger = structlog.get_logger(__name__)


class BaseTool(abc.ABC):
    """
    Abstract base class for all Vishwas tools.
    Designed to easily convert into LangChain tools.
    """

    name: str
    description: str
    args_schema: Type[BaseModel]

    @abc.abstractmethod
    async def arun(self, **kwargs) -> Any:
        """Async implementation of the tool execution."""
        pass

    def run(self, **kwargs) -> Any:
        """Sync fallback (rarely used)."""
        import asyncio
        return asyncio.run(self.arun(**kwargs))

    def as_langchain_tool(self) -> LangChainBaseTool:
        """Convert to a LangChain StructuredTool for easy binding."""
        return StructuredTool.from_function(
            func=self.run,
            coroutine=self.arun,
            name=self.name,
            description=self.description,
            args_schema=self.args_schema,
        )


class ToolRegistry:
    """Registry for discovering and instantiating tools."""

    def __init__(self):
        self._tools: dict[str, Type[BaseTool]] = {}
        self._instances: dict[str, BaseTool] = {}

    def register(self, tool_class: Type[BaseTool]) -> None:
        """Register a tool class."""
        self._tools[tool_class.name] = tool_class
        logger.debug("Tool registered", tool_name=tool_class.name)

    def get_tool(self, name: str) -> BaseTool:
        """Get or create an instance of a tool."""
        if name not in self._tools:
            raise ValueError(f"Tool not found: {name}")
            
        if name not in self._instances:
            self._instances[name] = self._tools[name]()
            
        return self._instances[name]

    def get_all_langchain_tools(self, names: list[str] | None = None) -> list[LangChainBaseTool]:
        """Get a list of LangChain-compatible tools for an agent."""
        tool_names = names or list(self._tools.keys())
        lc_tools = []
        for name in tool_names:
            try:
                tool = self.get_tool(name)
                lc_tools.append(tool.as_langchain_tool())
            except ValueError as e:
                logger.warning(f"Could not load tool: {e}")
        return lc_tools

# Global registry
tool_registry = ToolRegistry()


def register_tool(cls: Type[BaseTool]) -> Type[BaseTool]:
    """Decorator to easily register tools."""
    tool_registry.register(cls)
    return cls
