"""
OpenAI MCP Client

A drop-in MCP client that uses OpenAI's API for tool calling.
Handles the full tool-calling loop automatically.
"""

from __future__ import annotations

import json
import os
from typing import Any

from mcp_toolkit.clients.base import BaseMCPClient, _extract_tool_text
from mcp_toolkit.converters import mcp_to_openai


class OpenAIMCPClient(BaseMCPClient):
    """MCP client powered by OpenAI.

    Connects to any MCP server and uses OpenAI's function calling
    to automatically invoke tools as needed.

    Example:
        >>> async with OpenAIMCPClient(server_script="server.py") as client:
        ...     response = await client.chat("What's the weather in Paris?")
        ...     print(response)
    """

    def __init__(
        self,
        *,
        model: str = "gpt-4o-mini",
        api_key: str | None = None,
        temperature: float = 0,
        **kwargs,
    ):
        """Initialize the OpenAI MCP client.

        Args:
            model: OpenAI model name (default: gpt-4o-mini).
            api_key: OpenAI API key. Falls back to OPENAI_API_KEY env var.
            temperature: Sampling temperature (0 = deterministic).
            **kwargs: Passed to BaseMCPClient (server_script, server_url, etc.)
        """
        super().__init__(**kwargs)
        self.model = model
        self.temperature = temperature

        resolved_key = api_key or os.getenv("OPENAI_API_KEY")
        if not resolved_key:
            raise ValueError(
                "OpenAI API key required. Pass api_key= or set OPENAI_API_KEY env var."
            )

        try:
            from openai import OpenAI
        except ImportError as e:
            raise ImportError(
                "OpenAI client requires the 'openai' extra. "
                "Install with: pip install 'mcp-toolkit[openai]'"
            ) from e

        self._openai = OpenAI(api_key=resolved_key)

    async def chat(self, message: str) -> str:
        """Send a message and get a response with automatic tool execution.

        The client will:
        1. Send your message to OpenAI with available MCP tools
        2. If OpenAI requests tool calls, execute them via MCP
        3. Feed results back to OpenAI
        4. Repeat until a final text response is produced

        Args:
            message: User message.

        Returns:
            The model's final text response.
        """
        tools = mcp_to_openai(self._mcp_tools)
        input_list: list[dict[str, Any]] = [
            {"role": "developer", "content": self.system_prompt},
            {"role": "user", "content": message},
        ]

        while True:
            response = self._openai.responses.create(
                model=self.model,
                tools=tools,
                input=input_list,
                temperature=self.temperature,
            )

            tool_calls_found = False

            for item in response.output:
                item_type = getattr(item, "type", None)

                if item_type == "reasoning":
                    input_list.append(item.model_dump())
                    continue

                if item_type == "function_call":
                    tool_calls_found = True
                    tool_name = item.name
                    try:
                        tool_args = json.loads(item.arguments or "{}")
                    except (json.JSONDecodeError, TypeError):
                        tool_args = {}

                    input_list.append(item.model_dump())

                    # Execute tool via MCP
                    try:
                        result = await self.call_tool(tool_name, tool_args)
                        output_payload = json.dumps({"result": result})
                    except Exception as e:
                        output_payload = json.dumps({"error": str(e)})

                    input_list.append({
                        "type": "function_call_output",
                        "call_id": item.call_id,
                        "output": output_payload,
                    })

            if not tool_calls_found:
                return response.output_text or ""
