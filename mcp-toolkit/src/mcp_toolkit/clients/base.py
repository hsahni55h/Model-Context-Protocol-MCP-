"""
Base MCP Client

Shared connection management and tool execution logic for all LLM-specific clients.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from contextlib import AsyncExitStack
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from mcp_toolkit.config import MCPServerConfig
from mcp_toolkit.transports import _detect_command


class BaseMCPClient(ABC):
    """Abstract base class for MCP clients.

    Handles server connection lifecycle and tool execution.
    Subclasses implement LLM-specific chat logic.

    Usage as async context manager:
        >>> async with MyClient(server_script="server.py") as client:
        ...     response = await client.chat("Hello")
    """

    def __init__(
        self,
        *,
        server_script: str | None = None,
        server_url: str | None = None,
        server_config: MCPServerConfig | None = None,
        command: str | None = None,
        args: list[str] | None = None,
        system_prompt: str = "You are a helpful assistant with access to tools.",
    ):
        """Initialize the MCP client.

        Provide ONE of:
            - server_script: Path to a .py/.js server file (stdio transport)
            - server_url: SSE endpoint URL (SSE transport)
            - server_config: MCPServerConfig object

        Args:
            server_script: Path to server script (auto-detects interpreter).
            server_url: SSE endpoint URL.
            server_config: Pre-built config object.
            command: Override the interpreter command.
            args: Override the command arguments.
            system_prompt: System prompt for the LLM.
        """
        self._server_script = server_script
        self._server_url = server_url
        self._server_config = server_config
        self._command = command
        self._args = args
        self.system_prompt = system_prompt

        self._exit_stack = AsyncExitStack()
        self._session: ClientSession | None = None
        self._mcp_tools: list = []

    async def __aenter__(self):
        await self._connect()
        return self

    async def __aexit__(self, *exc):
        await self._exit_stack.aclose()

    async def _connect(self) -> None:
        """Establish connection to the MCP server."""
        if self._server_url:
            await self._connect_sse(self._server_url)
        elif self._server_script:
            cmd = self._command or _detect_command(self._server_script)
            args = self._args or [self._server_script]
            await self._connect_stdio(cmd, args)
        elif self._server_config:
            cfg = self._server_config
            if cfg.transport == "streamable_http":
                await self._connect_streamable_http(cfg.url)
            elif cfg.transport == "sse":
                await self._connect_sse(cfg.url)
            else:
                await self._connect_stdio(cfg.command, cfg.args)
        else:
            raise ValueError(
                "Must provide server_script, server_url, or server_config"
            )

        # Fetch available tools
        response = await self._session.list_tools()
        self._mcp_tools = response.tools

    async def _connect_stdio(self, command: str, args: list[str]) -> None:
        """Connect via stdio transport."""
        server_params = StdioServerParameters(command=command, args=args)
        transport = await self._exit_stack.enter_async_context(
            stdio_client(server_params)
        )
        read_stream, write_stream = transport
        self._session = await self._exit_stack.enter_async_context(
            ClientSession(read_stream, write_stream)
        )
        await self._session.initialize()

    async def _connect_sse(self, url: str) -> None:
        """Connect via SSE transport."""
        try:
            from mcp.client.sse import sse_client
        except ImportError as e:
            raise ImportError(
                "SSE transport requires 'mcp[cli]'. Install with: pip install 'mcp[cli]'"
            ) from e

        transport = await self._exit_stack.enter_async_context(sse_client(url=url))
        read_stream, write_stream = transport
        self._session = await self._exit_stack.enter_async_context(
            ClientSession(read_stream, write_stream)
        )
        await self._session.initialize()

    async def _connect_streamable_http(self, url: str) -> None:
        """Connect via streamable HTTP transport."""
        try:
            from mcp.client.streamable_http import streamable_http_client
        except ImportError as e:
            raise ImportError(
                "Streamable HTTP transport requires mcp>=1.25.0. "
                "Install with: pip install 'mcp[cli]>=1.25.0'"
            ) from e

        transport = await self._exit_stack.enter_async_context(
            streamable_http_client(url=url)
        )
        read_stream, write_stream, _get_session_id = transport
        self._session = await self._exit_stack.enter_async_context(
            ClientSession(read_stream, write_stream)
        )
        await self._session.initialize()

    @property
    def session(self) -> ClientSession:
        """The active MCP session."""
        if not self._session:
            raise RuntimeError("Not connected. Use 'async with' or call _connect().")
        return self._session

    @property
    def mcp_tools(self) -> list:
        """List of MCP tool objects from the connected server."""
        return self._mcp_tools

    @property
    def tool_names(self) -> list[str]:
        """Names of available tools."""
        return [t.name for t in self._mcp_tools]

    async def call_tool(self, name: str, arguments: dict[str, Any] = None) -> str:
        """Execute an MCP tool and return the result as text.

        Args:
            name: Tool name.
            arguments: Tool arguments dict.

        Returns:
            Tool result as a string.
        """
        result = await self.session.call_tool(name, arguments or {})
        return _extract_tool_text(result)

    @abstractmethod
    async def chat(self, message: str) -> str:
        """Send a message and get a response (with automatic tool use).

        Args:
            message: User message.

        Returns:
            The LLM's final text response after any tool calls.
        """
        ...

    async def chat_loop(self) -> None:
        """Run an interactive terminal chat session."""
        print(f"\nMCP Client ready! Tools: {self.tool_names}")
        print("Type 'quit' to exit.\n")

        while True:
            try:
                query = input("You: ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            if query.lower() in ("quit", "exit", "q"):
                break
            if not query:
                continue

            response = await self.chat(query)
            print(f"\nAssistant: {response}\n")


def _extract_tool_text(result: Any) -> str:
    """Extract text content from an MCP tool result."""
    if hasattr(result, "content"):
        if isinstance(result.content, list):
            return "\n".join(
                getattr(part, "text", str(part)) for part in result.content
            )
        return str(result.content)
    return str(result)
