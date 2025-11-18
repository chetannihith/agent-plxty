"""
A2A Protocol Implementation
Agent-to-Agent communication following official A2A specification
"""

from .agent_card import AgentCard, RESUME_OPTIMIZER_AGENT_CARD
from .messages import (
    A2AMessage,
    A2ATask,
    JSONRPCRequest,
    JSONRPCResponse,
    MessageRole,
    TaskStatus,
)
from .client import A2AClient

__all__ = [
    "AgentCard",
    "RESUME_OPTIMIZER_AGENT_CARD",
    "A2AMessage",
    "A2ATask",
    "JSONRPCRequest",
    "JSONRPCResponse",
    "MessageRole",
    "TaskStatus",
    "A2AClient",
]
