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
)
from mcp_toolkit.config import MCPConfig, MCPServerConfig, load_config, load_config_from_dict
from mcp_toolkit.transports import connect

__version__ = "0.1.0"

__all__ = [
    # Converters
    "clean_schema",
    "mcp_to_openai",
    "mcp_to_openai_chat",
    "mcp_to_gemini",
    "mcp_to_anthropic",
    # Config
    "MCPConfig",
    "MCPServerConfig",
    "load_config",
    "load_config_from_dict",
    # Transport
    "connect",
]
