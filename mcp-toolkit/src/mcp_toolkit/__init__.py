"""
MCP Toolkit — Plug-and-play utilities for building MCP clients and servers.

Quick start:
    >>> from mcp_toolkit.clients import OpenAIMCPClient
    >>> async with OpenAIMCPClient(server_script="my_server.py") as client:
    ...     print(await client.chat("Hello!"))
"""

from mcp_toolkit.converters import (
    clean_schema,
    mcp_to_anthropic,
    mcp_to_gemini,
    mcp_to_openai,
    mcp_to_openai_chat,
    mcp_to_openai_completions,
    mcp_to_openai_responses,
)
from mcp_toolkit.config import MCPConfig, MCPServerConfig, load_config, load_config_from_dict
from mcp_toolkit.transports import connect
from mcp_toolkit.agents import BaseAgent

__version__ = "0.1.0"

__all__ = [
    # Converters
    "clean_schema",
    "mcp_to_openai_responses",
    "mcp_to_openai_completions",
    "mcp_to_gemini",
    "mcp_to_anthropic",
    # Backward-compat aliases
    "mcp_to_openai",
    "mcp_to_openai_chat",
    # Config
    "MCPConfig",
    "MCPServerConfig",
    "load_config",
    "load_config_from_dict",
    # Transport
    "connect",
    # Agents
    "BaseAgent",
    # Clients (lazy — require provider extras)
    "MultiServerClient",
]


def __getattr__(name: str):
    """Lazy-load provider-specific clients that require optional extras."""
    if name == "MultiServerClient":
        from mcp_toolkit.clients.multi import MultiServerClient
        return MultiServerClient
    raise AttributeError(f"module 'mcp_toolkit' has no attribute {name!r}")
