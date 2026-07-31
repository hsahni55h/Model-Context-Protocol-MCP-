"""
Gemini MCP Client

A drop-in MCP client that uses Google's Gemini API for tool calling.
Handles the full tool-calling loop automatically.
"""

from __future__ import annotations

import os
from typing import Any

from mcp_toolkit.clients.base import BaseMCPClient, _extract_tool_text
from mcp_toolkit.converters import clean_schema


class GeminiMCPClient(BaseMCPClient):
    """MCP client powered by Google Gemini.

    Connects to any MCP server and uses Gemini's function calling
    to automatically invoke tools as needed.

    Example:
        >>> async with GeminiMCPClient(server_script="server.py") as client:
        ...     response = await client.chat("What's the weather in Tokyo?")
        ...     print(response)
    """

    def __init__(
        self,
        *,
        model: str = "gemini-2.0-flash-001",
        api_key: str | None = None,
        **kwargs,
    ):
        """Initialize the Gemini MCP client.

        Args:
            model: Gemini model name (default: gemini-2.0-flash-001).
            api_key: Google API key. Falls back to GEMINI_API_KEY env var.
            **kwargs: Passed to BaseMCPClient (server_script, server_url, etc.)
        """
        super().__init__(**kwargs)
        self.model = model

        resolved_key = api_key or os.getenv("GEMINI_API_KEY")
        if not resolved_key:
            raise ValueError(
                "Gemini API key required. Pass api_key= or set GEMINI_API_KEY env var."
            )

        try:
            from google import genai
            from google.genai import types
        except ImportError as e:
            raise ImportError(
                "Gemini client requires the 'gemini' extra. "
                "Install with: pip install 'mcp-toolkit[gemini]'"
            ) from e

        self._genai_client = genai.Client(api_key=resolved_key)
        self._types = types

    def _build_tool_declarations(self):
        """Convert MCP tools to Gemini FunctionDeclaration format."""
        types = self._types
        declarations = []
        for tool in self._mcp_tools:
            parameters = clean_schema(tool.inputSchema) if tool.inputSchema else {}
            declarations.append(
                types.FunctionDeclaration(
                    name=tool.name,
                    description=tool.description or "",
                    parameters=parameters,
                )
            )
        return [types.Tool(function_declarations=declarations)]

    async def chat(self, message: str) -> str:
        """Send a message and get a response with automatic tool execution.

        The client will:
        1. Send your message to Gemini with available MCP tools
        2. If Gemini requests function calls, execute them via MCP
        3. Feed results back to Gemini
        4. Repeat until a final text response is produced

        Args:
            message: User message.

        Returns:
            The model's final text response.
        """
        types = self._types
        tools = self._build_tool_declarations()

        user_content = types.Content(
            role="user",
            parts=[types.Part.from_text(text=message)],
        )

        response = self._genai_client.models.generate_content(
            model=self.model,
            contents=[user_content],
            config=types.GenerateContentConfig(
                tools=tools,
                system_instruction=self.system_prompt,
            ),
        )

        final_text = []

        for candidate in response.candidates:
            if not candidate.content.parts:
                continue

            for part in candidate.content.parts:
                if not isinstance(part, types.Part):
                    continue

                if part.function_call:
                    tool_name = part.function_call.name
                    tool_args = dict(part.function_call.args) if part.function_call.args else {}

                    # Execute tool via MCP
                    try:
                        result = await self.call_tool(tool_name, tool_args)
                        function_response = {"result": result}
                    except Exception as e:
                        function_response = {"error": str(e)}

                    # Send tool result back to Gemini
                    function_response_part = types.Part.from_function_response(
                        name=tool_name,
                        response=function_response,
                    )
                    function_response_content = types.Content(
                        role="tool",
                        parts=[function_response_part],
                    )

                    response = self._genai_client.models.generate_content(
                        model=self.model,
                        contents=[user_content, part, function_response_content],
                        config=types.GenerateContentConfig(
                            tools=tools,
                            system_instruction=self.system_prompt,
                        ),
                    )

                    # Extract text from follow-up response
                    for c in response.candidates:
                        for p in c.content.parts:
                            if hasattr(p, "text") and p.text:
                                final_text.append(p.text)
                else:
                    if hasattr(part, "text") and part.text:
                        final_text.append(part.text)

        return "\n".join(final_text)
