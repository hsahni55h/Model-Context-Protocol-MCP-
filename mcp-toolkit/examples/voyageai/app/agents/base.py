"""Base agent with OpenAI tool-calling loop.

Shared by all specialized agents — each one provides its own
system prompt and tool subset.
"""

import json
from openai import AsyncOpenAI

from mcp_toolkit.clients.multi import MultiServerClient
from mcp_toolkit.converters import mcp_to_openai_chat

from app.config import OPENAI_MODEL

MAX_TOOL_ROUNDS = 10


class BaseAgent:
    """Base class for specialized travel agents.

    Each agent gets:
    - A shared MultiServerClient (already connected)
    - A shared AsyncOpenAI client
    - A filtered subset of tools (by server name)
    - Its own system prompt
    """

    system_prompt: str = "You are a helpful assistant."
    server_names: list[str] = []  # Which MCP servers this agent uses

    def __init__(self, mcp_client: MultiServerClient, openai_client: AsyncOpenAI):
        self._mcp = mcp_client
        self._openai = openai_client
        self._tools: list[dict] = []
        self._setup_tools()

    def _setup_tools(self) -> None:
        """Filter tools to only those from this agent's servers.

        If server_names is empty, grants access to all available tools.
        """
        if not self.server_names:
            raw_tools = self._mcp.all_tools
        else:
            tool_names = set()
            for server in self.server_names:
                tool_names.update(self._mcp.get_tools_by_server(server))
            raw_tools = [t for t in self._mcp.all_tools if t.name in tool_names]
        self._tools = mcp_to_openai_chat(raw_tools)

    async def run(self, query: str, history: list[dict] | None = None) -> str:
        """Run the agent with a query, executing tools as needed.

        Args:
            query: The task/question for this agent.
            history: Optional prior conversation messages for context.

        Returns:
            Agent's text response after tool execution.
        """
        messages = [
            {"role": "system", "content": self.system_prompt},
        ]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": query})

        for _ in range(MAX_TOOL_ROUNDS):
            response = await self._openai.chat.completions.create(
                model=OPENAI_MODEL,
                messages=messages,
                tools=self._tools if self._tools else None,
            )

            msg = response.choices[0].message

            if not msg.tool_calls:
                return msg.content or ""

            messages.append(msg.model_dump())

            for tc in msg.tool_calls:
                try:
                    args = json.loads(tc.function.arguments)
                except json.JSONDecodeError:
                    args = {}

                try:
                    result = await self._mcp.call_tool(tc.function.name, args)
                except Exception as e:
                    result = f"Error: {e}"

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result,
                })

        # Max rounds reached — get final answer
        final = await self._openai.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
        )
        return final.choices[0].message.content or ""
