"""
Multi-Server MCP Client

Connect to multiple MCP servers simultaneously and expose all their tools
to a single LLM agent. The model decides which tools to call.
"""

from __future__ import annotations

import json
import os
from contextlib import AsyncExitStack
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from mcp_toolkit.config import MCPConfig, MCPServerConfig, load_config, load_config_from_dict
from mcp_toolkit.converters import mcp_to_openai_completions
from mcp_toolkit.transports import _detect_command


class MultiServerClient:
    """MCP client that aggregates tools from multiple servers.

    Connects to multiple MCP servers (defined in a config file or dict)
    and exposes all their tools to a single LLM for unified access.

    Example:
        >>> async with MultiServerClient.from_config("mcp_servers.json") as client:
        ...     response = await client.chat("Calculate 2+2 and check weather in NYC")
    """

    def __init__(
        self,
        config: MCPConfig,
        *,
        model: str = "gpt-4o-mini",
        api_key: str | None = None,
        temperature: float = 0,
        system_prompt: str = "You are a helpful assistant with access to multiple tool servers.",
    ):
        """Initialize the multi-server client.

        Args:
            config: MCPConfig with server definitions.
            model: OpenAI model name.
            api_key: OpenAI API key. Falls back to OPENAI_API_KEY env var.
            temperature: Sampling temperature.
            system_prompt: System prompt for the LLM.
        """
        self._config = config
        self.model = model
        self.temperature = temperature
        self.system_prompt = system_prompt

        resolved_key = api_key or os.getenv("OPENAI_API_KEY")
        if not resolved_key:
            raise ValueError(
                "OpenAI API key required. Pass api_key= or set OPENAI_API_KEY env var."
            )

        try:
            from openai import AsyncOpenAI
        except ImportError as e:
            raise ImportError(
                "MultiServerClient requires the 'openai' extra. "
                "Install with: pip install 'mcp-toolkit[openai]'"
            ) from e

        self._openai = AsyncOpenAI(api_key=resolved_key)
        self._exit_stack = AsyncExitStack()
        self._sessions: dict[str, ClientSession] = {}
        self._all_mcp_tools: list = []
        self._tool_to_server: dict[str, str] = {}

    @classmethod
    def from_config(
        cls,
        path: str | None = None,
        **kwargs,
    ) -> MultiServerClient:
        """Create a MultiServerClient from a config file.

        Args:
            path: Path to config JSON file. Uses default resolution if None.
            **kwargs: Passed to __init__ (model, api_key, etc.)

        Returns:
            MultiServerClient instance (not yet connected — use async with).
        """
        config = load_config(path)
        return cls(config, **kwargs)

    @classmethod
    def from_dict(
        cls,
        servers: dict[str, dict[str, Any]],
        **kwargs,
    ) -> MultiServerClient:
        """Create a MultiServerClient from a Python dict.

        Args:
            servers: Dict mapping server names to their config.
                Example: {"math": {"command": "python", "args": ["math_server.py"]}}
            **kwargs: Passed to __init__ (model, api_key, etc.)

        Returns:
            MultiServerClient instance (not yet connected — use async with).
        """
        config = load_config_from_dict({"mcpServers": servers})
        return cls(config, **kwargs)

    async def __aenter__(self):
        await self._connect_all()
        return self

    async def __aexit__(self, *exc):
        await self._exit_stack.aclose()

    async def _connect_all(self) -> None:
        """Connect to all configured servers."""
        for name, server_cfg in self._config.servers.items():
            try:
                session = await self._connect_one(server_cfg)
                self._sessions[name] = session

                # Load tools from this server
                response = await session.list_tools()
                for tool in response.tools:
                    self._all_mcp_tools.append(tool)
                    self._tool_to_server[tool.name] = name

            except Exception as e:
                print(f"Warning: Failed to connect to server '{name}': {e}")

        if not self._all_mcp_tools:
            raise RuntimeError("No tools loaded from any server.")

    async def _connect_one(self, cfg: MCPServerConfig) -> ClientSession:
        """Connect to a single server."""
        if cfg.transport == "streamable_http":
            from mcp.client.streamable_http import streamable_http_client
            transport = await self._exit_stack.enter_async_context(
                streamable_http_client(url=cfg.url)
            )
            read_stream, write_stream, _get_session_id = transport
        elif cfg.transport == "sse":
            from mcp.client.sse import sse_client
            transport = await self._exit_stack.enter_async_context(
                sse_client(url=cfg.url)
            )
            read_stream, write_stream = transport
        else:
            server_params = StdioServerParameters(
                command=cfg.command,
                args=cfg.args,
                env=cfg.env or None,
            )
            transport = await self._exit_stack.enter_async_context(
                stdio_client(server_params)
            )
            read_stream, write_stream = transport

        session = await self._exit_stack.enter_async_context(
            ClientSession(read_stream, write_stream)
        )
        await session.initialize()
        return session

    @property
    def all_tools(self) -> list:
        """All MCP tool objects across every connected server."""
        return self._all_mcp_tools

    @property
    def tool_names(self) -> list[str]:
        """Names of all available tools across all servers."""
        return [t.name for t in self._all_mcp_tools]

    @property
    def server_names(self) -> list[str]:
        """Names of connected servers."""
        return list(self._sessions.keys())

    def get_tools_by_server(self, server_name: str) -> list[str]:
        """Get tool names for a specific server.

        Args:
            server_name: Name of the server as defined in config.

        Returns:
            List of tool names from that server.
        """
        return [
            name for name, server in self._tool_to_server.items()
            if server == server_name
        ]

    async def call_tool_on_server(
        self, server_name: str, tool_name: str, arguments: dict[str, Any] = None
    ) -> str:
        """Call a specific tool on a specific server.

        Useful when you know which server owns the tool and want to bypass lookup.

        Args:
            server_name: Target server name.
            tool_name: Tool name on that server.
            arguments: Tool arguments.

        Returns:
            Tool result as text.
        """
        session = self._sessions.get(server_name)
        if not session:
            raise ValueError(f"Server '{server_name}' not connected. Available: {self.server_names}")

        result = await session.call_tool(tool_name, arguments or {})

        if hasattr(result, "content"):
            if isinstance(result.content, list):
                return "\n".join(
                    getattr(part, "text", str(part)) for part in result.content
                )
            return str(result.content)
        return str(result)

    async def call_tool(self, name: str, arguments: dict[str, Any] = None) -> str:
        """Execute a tool on the appropriate server.

        Args:
            name: Tool name.
            arguments: Tool arguments.

        Returns:
            Tool result as text.
        """
        server_name = self._tool_to_server.get(name)
        if not server_name:
            raise ValueError(f"Unknown tool: {name}")

        session = self._sessions[server_name]
        result = await session.call_tool(name, arguments or {})

        if hasattr(result, "content"):
            if isinstance(result.content, list):
                return "\n".join(
                    getattr(part, "text", str(part)) for part in result.content
                )
            return str(result.content)
        return str(result)

    async def chat(self, message: str) -> str:
        """Send a message and get a response with automatic multi-server tool use.

        The LLM can call tools from any connected server. Tool routing
        is handled automatically based on which server provides each tool.

        Args:
            message: User message.

        Returns:
            The model's final text response.
        """
        tools = mcp_to_openai_completions(self._all_mcp_tools)
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": message},
        ]

        while True:
            response = await self._openai.chat.completions.create(
                model=self.model,
                tools=tools,
                messages=messages,
                temperature=self.temperature,
            )

            msg = response.choices[0].message

            if not msg.tool_calls:
                return msg.content or ""

            messages.append(msg.model_dump())

            for tc in msg.tool_calls:
                try:
                    tool_args = json.loads(tc.function.arguments or "{}")
                except (json.JSONDecodeError, TypeError):
                    tool_args = {}

                try:
                    result = await self.call_tool(tc.function.name, tool_args)
                except Exception as e:
                    result = f"Error: {e}"

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result,
                })

    async def chat_loop(self) -> None:
        """Run an interactive terminal chat session."""
        print(f"\nMulti-Server MCP Client ready!")
        print(f"Connected servers: {self.server_names}")
        print(f"Available tools: {self.tool_names}")
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
