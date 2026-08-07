"""
MCP Toolkit — BaseAgent

Reusable agent base class for building specialized agents on top of a
MultiServerClient. Provides a complete OpenAI Chat Completions tool-calling
loop with per-server tool filtering built in.

Typical usage:

    from mcp_toolkit.agents import BaseAgent
    from mcp_toolkit.clients import MultiServerClient

    class WeatherAgent(BaseAgent):
        server_names = ["weather"]
        system_prompt = "You are a weather research specialist."

    class FlightAgent(BaseAgent):
        server_names = ["flights"]
        system_prompt = "You are a flight search specialist."

    async with MultiServerClient.from_config("mcp_servers.json") as mcp:
        openai_client = AsyncOpenAI()
        weather = WeatherAgent(mcp, openai_client)
        flights = FlightAgent(mcp, openai_client)

        # Run agents concurrently
        weather_result, flight_result = await asyncio.gather(
            weather.run("Weather in Tokyo next week?"),
            flights.run("Flights from London to Tokyo?"),
        )
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from openai import AsyncOpenAI
    from mcp_toolkit.clients.multi import MultiServerClient

from mcp_toolkit.converters import mcp_to_openai_completions


class BaseAgent:
    """Reusable agent base class for multi-server MCP applications.

    Subclass this and set ``server_names`` and ``system_prompt`` as class
    attributes to create a specialized agent that only sees tools from its
    designated MCP servers.

    If ``server_names`` is empty (the default), the agent has access to
    tools from *all* connected servers.

    Attributes:
        system_prompt: The LLM system prompt for this agent.
        server_names: Names of the MCP servers whose tools this agent uses.
            Must match keys defined in your ``mcp_servers.json`` config.
        max_tool_rounds: Maximum tool-calling iterations before forcing a
            final response. Guards against infinite loops.

    Example — single-server specialist agent::

        class CurrencyAgent(BaseAgent):
            server_names = ["currency"]
            system_prompt = \"\"\"You are a currency specialist.
            Convert budgets and explain exchange rates concisely.\"\"\"

    Example — agent with access to all tools::

        class GeneralistAgent(BaseAgent):
            system_prompt = "You are a helpful assistant with many tools."
    """

    system_prompt: str = "You are a helpful assistant with access to tools."
    server_names: list[str] = []
    max_tool_rounds: int = 10

    def __init__(
        self,
        mcp_client: "MultiServerClient",
        openai_client: "AsyncOpenAI",
        model: str = "gpt-4o-mini",
    ):
        """Initialize the agent.

        Args:
            mcp_client: A connected ``MultiServerClient`` instance (already
                entered as an async context manager).
            openai_client: An ``AsyncOpenAI`` client instance.
            model: The OpenAI model to use for this agent.
        """
        self._mcp = mcp_client
        self._openai = openai_client
        self.model = model
        self._tools: list[dict[str, Any]] = []
        self._setup_tools()

    def _setup_tools(self) -> None:
        """Build the filtered tool list for this agent's servers.

        Filters ``mcp_client.all_tools`` to only the tools belonging to
        ``server_names``. If ``server_names`` is empty, all tools are used.
        """
        if not self.server_names:
            raw_tools = self._mcp.all_tools
        else:
            tool_names: set[str] = set()
            for server in self.server_names:
                tool_names.update(self._mcp.get_tools_by_server(server))
            raw_tools = [t for t in self._mcp.all_tools if t.name in tool_names]

        self._tools = mcp_to_openai_completions(raw_tools)

    @property
    def tool_names(self) -> list[str]:
        """Names of tools available to this agent."""
        return [t["function"]["name"] for t in self._tools]

    async def run(self, query: str, history: list[dict[str, Any]] | None = None) -> str:
        """Run the agent on a query, calling tools as many times as needed.

        The agent sends the query to the LLM, executes any requested tool
        calls via the MCP client, feeds the results back, and repeats until
        the LLM returns a plain text response.

        Args:
            query: The question or task for this agent.
            history: Optional prior conversation messages to include for
                context. Each item should be a ``{"role": ..., "content": ...}``
                dict.

        Returns:
            The agent's final text response after all tool calls complete.

        Raises:
            RuntimeError: If ``max_tool_rounds`` is exceeded (the agent is
                stuck in a tool-call loop).
        """
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": self.system_prompt}
        ]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": query})

        for _ in range(self.max_tool_rounds):
            response = await self._openai.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=self._tools if self._tools else None,
            )

            msg = response.choices[0].message

            # No tool calls → model is done
            if not msg.tool_calls:
                return msg.content or ""

            # Append the assistant's tool-calling turn to history
            messages.append(msg.model_dump())

            # Execute each tool call and append the results
            for tc in msg.tool_calls:
                try:
                    args = json.loads(tc.function.arguments)
                except json.JSONDecodeError:
                    args = {}

                try:
                    result = await self._mcp.call_tool(tc.function.name, args)
                except Exception as e:
                    result = f"Error calling {tc.function.name}: {e}"

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result,
                })

        # Max rounds reached — ask for a final answer without tools
        final = await self._openai.chat.completions.create(
            model=self.model,
            messages=messages,
        )
        return final.choices[0].message.content or ""
