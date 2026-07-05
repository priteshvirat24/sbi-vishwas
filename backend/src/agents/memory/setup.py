"""SBI Vishwas — Memory Systems Registration."""

from __future__ import annotations

from src.agents.memory.core import memory_manager
from src.agents.memory.semantic import SemanticMemory
from src.agents.memory.long_term import LongTermMemory

def initialize_memory_system():
    """Register all memory tier providers."""
    memory_manager.register_provider("semantic", SemanticMemory())
    memory_manager.register_provider("long_term", LongTermMemory())
    
    import structlog
    logger = structlog.get_logger(__name__)
    logger.info("Memory system initialized with semantic and long-term tiers")
