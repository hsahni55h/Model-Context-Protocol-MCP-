"""
MCP Toolkit Clients

Pre-built MCP clients for various LLM providers.
Each client handles the full tool-calling loop automatically.

Usage:
    >>> from mcp_toolkit.clients import OpenAIMCPClient, GeminiMCPClient
"""

from mcp_toolkit.clients.base import BaseMCPClient

__all__ = ["BaseMCPClient"]

# Lazy imports to avoid requiring all provider SDKs at once


def __getattr__(name: str):
    """Lazy-load provider clients to avoid import errors for uninstalled extras."""
    if name == "OpenAIMCPClient":
        from mcp_toolkit.clients.openai import OpenAIMCPClient
        return OpenAIMCPClient
    if name == "GeminiMCPClient":
        from mcp_toolkit.clients.gemini import GeminiMCPClient
        return GeminiMCPClient
    if name == "AnthropicMCPClient":
        from mcp_toolkit.clients.anthropic import AnthropicMCPClient
        return AnthropicMCPClient
    if name == "LangChainMCPClient":
        from mcp_toolkit.clients.langchain import LangChainMCPClient
        return LangChainMCPClient
    if name == "MultiServerClient":
        from mcp_toolkit.clients.multi import MultiServerClient
        return MultiServerClient
    raise AttributeError(f"module 'mcp_toolkit.clients' has no attribute {name!r}")
