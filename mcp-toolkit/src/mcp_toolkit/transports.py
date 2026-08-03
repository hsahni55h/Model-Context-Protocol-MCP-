"""
MCP Transport Abstraction

Provides a unified interface for connecting to MCP servers regardless of
transport type (stdio subprocess or SSE over HTTP).
"""

from __future__ import annotations

import sys
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from mcp_toolkit.config import MCPServerConfig


@asynccontextmanager
async def connect(
    *,
    script: str | None = None,
    url: str | None = None,
    command: str | None = None,
    args: list[str] | None = None,
    env: dict[str, str] | None = None,
    config: MCPServerConfig | None = None,
) -> AsyncGenerator[ClientSession, None]:
    """Connect to an MCP server and yield an initialized ClientSession.

    Automatically selects the correct transport based on parameters:
    - If `url` is provided → SSE or streamable_http transport (HTTP)
    - If `script` is provided → stdio transport (subprocess)
    - If `config` is provided → uses config.transport to decide

    Args:
        script: Path to a server script (.py or .js). Auto-detects interpreter.
        url: Endpoint URL (for SSE or streamable_http).
        command: Explicit command override (default: auto-detected from script extension).
        args: Explicit args override.
        env: Environment variables for the subprocess.
        config: An MCPServerConfig object (alternative to individual params).

    Yields:
        An initialized ClientSession ready for tool calls.

    Example:
        >>> async with connect(script="my_server.py") as session:
        ...     tools = await session.list_tools()

        >>> async with connect(url="http://localhost:8000/sse") as session:
        ...     result = await session.call_tool("greet", {"name": "World"})
    """
    transport_type = None

    # Resolve from config object if provided
    if config:
        transport_type = config.transport
        if transport_type in ("sse", "streamable_http"):
            url = config.url
        else:
            command = config.command
            args = config.args
            env = config.env or None
            if not script and args:
                script = args[0] if len(args) == 1 else None

    if url:
        if transport_type == "streamable_http":
            async with _connect_streamable_http(url) as session:
                yield session
        else:
            async with _connect_sse(url) as session:
                yield session
    elif script:
        resolved_command = command or _detect_command(script)
        resolved_args = args if args is not None else [script]
        async with _connect_stdio(resolved_command, resolved_args, env) as session:
            yield session
    elif command and args:
        async with _connect_stdio(command, args, env) as session:
            yield session
    else:
        raise ValueError(
            "Must provide one of: script (path), url (SSE/streamable_http endpoint), "
            "or config (MCPServerConfig)"
        )


@asynccontextmanager
async def _connect_stdio(
    command: str, args: list[str], env: dict[str, str] | None
) -> AsyncGenerator[ClientSession, None]:
    """Connect via stdio (subprocess) transport."""
    server_params = StdioServerParameters(
        command=command,
        args=args,
        env=env,
    )
    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            yield session


@asynccontextmanager
async def _connect_sse(url: str) -> AsyncGenerator[ClientSession, None]:
    """Connect via SSE (HTTP) transport."""
    try:
        from mcp.client.sse import sse_client
    except ImportError as e:
        raise ImportError(
            "SSE transport requires the 'sse' extra. "
            "Install with: pip install 'mcp-toolkit[sse]' or pip install 'mcp[cli]'"
        ) from e

    async with sse_client(url=url) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            yield session


@asynccontextmanager
async def _connect_streamable_http(url: str) -> AsyncGenerator[ClientSession, None]:
    """Connect via streamable HTTP transport.

    This is the newer MCP transport used by services like Tavily.
    It uses standard HTTP POST/GET with optional SSE streaming.
    """
    try:
        from mcp.client.streamable_http import streamable_http_client
    except ImportError as e:
        raise ImportError(
            "Streamable HTTP transport requires mcp>=1.25.0. "
            "Install with: pip install 'mcp[cli]>=1.25.0'"
        ) from e

    async with streamable_http_client(url=url) as (read_stream, write_stream, _get_session_id):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            yield session


def _detect_command(script: str) -> str:
    """Auto-detect the interpreter command from script extension."""
    if script.endswith(".py"):
        return sys.executable
    if script.endswith((".js", ".mjs")):
        return "node"
    if script.endswith(".ts"):
        return "npx"
    return sys.executable  # Default to Python
