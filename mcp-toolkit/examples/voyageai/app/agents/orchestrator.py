"""VoyageAI Orchestrator Agent.

The main agent that coordinates travel planning using MCP tools.
Uses mcp-toolkit's MultiServerClient to connect to all MCP servers
and OpenAI's tool-calling API to intelligently plan trips.
"""

import json
from openai import AsyncOpenAI

from mcp_toolkit.clients.multi import MultiServerClient
from mcp_toolkit.converters import mcp_to_openai

from app.config import OPENAI_API_KEY, OPENAI_MODEL, get_mcp_config

SYSTEM_PROMPT = """\
You are VoyageAI, an expert travel planning assistant. You help users plan trips by:

1. Searching for flights between cities
2. Finding hotels and attractions at the destination
3. Checking weather forecasts for travel dates
4. Converting currencies for budget planning

When a user asks about a trip, gather relevant information using your tools:
- Use weather tools to check conditions at the destination
- Use flight tools to find available flights
- Use tavily_search to find hotels, restaurants, and attractions
- Use currency tools to help with budget conversion

Provide well-organized, helpful travel plans. Be concise but thorough.
If you don't have enough info, ask the user for clarification.
Always format your final response in a clear, readable way.
"""

MAX_TOOL_ROUNDS = 10


class TravelOrchestrator:
    """Orchestrates travel planning using MCP tools + OpenAI."""

    def __init__(self):
        self._mcp_client: MultiServerClient | None = None
        self._openai: AsyncOpenAI | None = None
        self._tools_openai: list[dict] = []

    async def initialize(self) -> None:
        """Connect to all MCP servers and prepare tools."""
        config = get_mcp_config()
        servers = config.get("mcpServers", config)
        client = MultiServerClient.from_dict(servers)
        self._mcp_client = await client.__aenter__()
        self._openai = AsyncOpenAI(api_key=OPENAI_API_KEY)

        # Convert MCP tools to OpenAI format
        self._tools_openai = mcp_to_openai(self._mcp_client._all_mcp_tools)

    async def close(self) -> None:
        """Disconnect from all servers."""
        if self._mcp_client:
            await self._mcp_client.__aexit__(None, None, None)
            self._mcp_client = None

    async def chat(self, user_message: str, history: list[dict] = None) -> str:
        """Process a user message and return the agent's response.

        Args:
            user_message: The user's travel query.
            history: Optional conversation history (list of message dicts).

        Returns:
            The agent's response text.
        """
        if not self._mcp_client or not self._openai:
            raise RuntimeError("Orchestrator not initialized. Call initialize() first.")

        # Build messages
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": user_message})

        # Tool-calling loop
        for _ in range(MAX_TOOL_ROUNDS):
            response = await self._openai.chat.completions.create(
                model=OPENAI_MODEL,
                messages=messages,
                tools=self._tools_openai if self._tools_openai else None,
            )

            choice = response.choices[0]
            message = choice.message

            # If no tool calls, we're done
            if not message.tool_calls:
                return message.content or ""

            # Add assistant message with tool calls
            messages.append(message.model_dump())

            # Execute each tool call
            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                try:
                    tool_args = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError:
                    tool_args = {}

                try:
                    result = await self._mcp_client.call_tool(tool_name, tool_args)
                except Exception as e:
                    result = f"Error calling {tool_name}: {e}"

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result,
                })

        # If we hit max rounds, return what we have
        final = await self._openai.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
        )
        return final.choices[0].message.content or ""
