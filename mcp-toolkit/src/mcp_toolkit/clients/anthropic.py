"""
Anthropic MCP Client

A drop-in MCP client that uses Anthropic's Claude API for tool calling.
Handles the full tool-calling loop automatically.
"""

from __future__ import annotations

import os
from typing import Any

from mcp_toolkit.clients.base import BaseMCPClient
from mcp_toolkit.converters import mcp_to_anthropic


class AnthropicMCPClient(BaseMCPClient):
    """MCP client powered by Anthropic Claude.

    Connects to any MCP server and uses Claude's tool use feature
    to automatically invoke tools as needed.

    Example:
        >>> async with AnthropicMCPClient(server_script="server.py") as client:
        ...     response = await client.chat("What's the weather in London?")
        ...     print(response)
    """

    def __init__(
        self,
        *,
        model: str = "claude-sonnet-4-20250514",
        api_key: str | None = None,
        temperature: float = 0,
        max_tokens: int = 1024,
        **kwargs,
    ):
        """Initialize the Anthropic MCP client.

        Args:
            model: Claude model name (default: claude-sonnet-4-20250514).
            api_key: Anthropic API key. Falls back to ANTHROPIC_API_KEY env var.
            temperature: Sampling temperature (0 = deterministic).
            max_tokens: Maximum tokens in response.
            **kwargs: Passed to BaseMCPClient (server_script, server_url, etc.)
        """
        super().__init__(**kwargs)
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

        resolved_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not resolved_key:
            raise ValueError(
                "Anthropic API key required. Pass api_key= or set ANTHROPIC_API_KEY env var."
            )

        try:
            from anthropic import Anthropic
        except ImportError as e:
            raise ImportError(
                "Anthropic client requires the 'anthropic' extra. "
                "Install with: pip install 'mcp-toolkit[anthropic]'"
            ) from e

        self._anthropic = Anthropic(api_key=resolved_key)

    async def chat(self, message: str) -> str:
        """Send a message and get a response with automatic tool execution.

        The client will:
        1. Send your message to Claude with available MCP tools
        2. If Claude requests tool use, execute tools via MCP
        3. Feed results back to Claude
        4. Repeat until a final text response is produced

        Args:
            message: User message.

        Returns:
            The model's final text response.
        """
        tools = mcp_to_anthropic(self._mcp_tools)
        messages = [{"role": "user", "content": message}]

        while True:
            response = self._anthropic.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=self.system_prompt,
                tools=tools,
                messages=messages,
                temperature=self.temperature,
            )

            # Check if model wants to use tools
            if response.stop_reason != "tool_use":
                # Extract final text
                text_parts = [
                    block.text
                    for block in response.content
                    if block.type == "text"
                ]
                return "\n".join(text_parts)

            # Process tool use blocks
            assistant_content = response.content
            messages.append({"role": "assistant", "content": assistant_content})

            tool_results = []
            for block in assistant_content:
                if block.type != "tool_use":
                    continue

                tool_name = block.name
                tool_args = block.input

                try:
                    result = await self.call_tool(tool_name, tool_args)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    })
                except Exception as e:
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": f"Error: {e}",
                        "is_error": True,
                    })

            messages.append({"role": "user", "content": tool_results})
