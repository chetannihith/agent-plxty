"""
MCP Client Module for Resume Optimizer
Handles Model Context Protocol connections and tool invocations
"""
from .connection import MCPClientManager, mcp_client

__all__ = ["MCPClientManager", "mcp_client"]
