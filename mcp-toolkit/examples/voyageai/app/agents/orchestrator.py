"""VoyageAI Orchestrator Agent.

Coordinates travel planning by running specialized agents in parallel,
then synthesizing their results into a coherent response.

Architecture:
    User query → Orchestrator parses intent
                → WeatherAgent  ┐
                → FlightAgent   │ asyncio.gather (parallel)
                → HotelAgent    │
                → CurrencyAgent ┘
                → Planner synthesizes all results → final response
"""

import asyncio
import json
from openai import AsyncOpenAI

from mcp_toolkit.clients.multi import MultiServerClient

from app.config import OPENAI_API_KEY, OPENAI_MODEL, get_mcp_config
from app.agents.base import BaseAgent
from app.agents.weather import WeatherAgent
from app.agents.flight import FlightAgent
from app.agents.hotel import HotelAgent
from app.agents.currency import CurrencyAgent

SYSTEM_PROMPT = """\
You are VoyageAI, an expert travel planning assistant.
You coordinate multiple specialist agents to plan trips.

Given a user's travel query, determine what information is needed and
create specific task descriptions for your specialist agents:
- Weather: destination weather and forecast
- Flights: flight routes and airport info
- Hotels: accommodation and attractions
- Currency: exchange rates and budget conversion

Respond ONLY with a JSON object (no markdown, no code fences) containing
task descriptions for relevant agents. Use null for agents not needed.

Example: {"weather": "Check weather in Tokyo for next week",
          "flights": "Find flights from London to Tokyo",
          "hotels": "Find hotels and attractions in Tokyo",
          "currency": "Convert 2000 GBP to JPY"}
"""

PLANNER_PROMPT = """\
You are VoyageAI, an expert travel planner. You've received research from
specialist agents. Synthesize their findings into a clear, well-organized
travel plan for the user.

Structure your response with clear sections. Be helpful and concise.
If some research returned errors or no data, acknowledge it gracefully
and work with what you have."""


class _GeneralistAgent(BaseAgent):
    """Fallback agent with access to all tools, for simple or unclassified queries."""

    server_names: list[str] = []
    system_prompt = (
        "You are VoyageAI, a travel planning assistant. "
        "Use your tools to help the user."
    )


class TravelOrchestrator:
    """Orchestrates travel planning with parallel specialist agents."""

    def __init__(self):
        self._mcp_client: MultiServerClient | None = None
        self._openai: AsyncOpenAI | None = None
        self._agents: dict[str, BaseAgent] = {}

    async def initialize(self) -> None:
        """Connect to all MCP servers and set up specialist agents."""
        config = get_mcp_config()
        client = MultiServerClient(config, api_key=OPENAI_API_KEY)
        self._mcp_client = await client.__aenter__()
        self._openai = AsyncOpenAI(api_key=OPENAI_API_KEY)

        # Create specialist agents (all share the same MCP + OpenAI clients)
        self._agents = {
            "weather": WeatherAgent(self._mcp_client, self._openai),
            "flights": FlightAgent(self._mcp_client, self._openai),
            "hotels": HotelAgent(self._mcp_client, self._openai),
            "currency": CurrencyAgent(self._mcp_client, self._openai),
            "generalist": _GeneralistAgent(self._mcp_client, self._openai),
        }

    async def close(self) -> None:
        """Disconnect from all servers."""
        if self._mcp_client:
            await self._mcp_client.__aexit__(None, None, None)
            self._mcp_client = None

    async def chat(self, user_message: str, history: list[dict] = None) -> str:
        """Process a user message using parallel specialist agents.

        Flow:
            1. Parse user intent → create agent task descriptions
            2. Run relevant agents in parallel
            3. Synthesize results into final response
        """
        if not self._mcp_client or not self._openai:
            raise RuntimeError("Orchestrator not initialized.")

        # Step 1: Parse intent — ask LLM to create agent tasks
        tasks = await self._parse_intent(user_message, history)

        # If we couldn't parse structured tasks, fall back to generalist agent
        if not tasks:
            return await self._agents["generalist"].run(user_message, history)

        # Step 2: Run agents in parallel
        results = await self._run_agents(tasks)

        # Step 3: Synthesize into final response
        return await self._synthesize(user_message, results, history)

    async def _parse_intent(self, message: str, history: list[dict] = None) -> dict | None:
        """Use LLM to parse user intent into agent task descriptions."""
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": message})

        response = await self._openai.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
        )

        content = response.choices[0].message.content or ""
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return None

    async def _run_agents(self, tasks: dict) -> dict[str, str]:
        """Run specialist agents in parallel for the given tasks."""
        async def _run_one(name: str, query: str) -> tuple[str, str]:
            try:
                result = await self._agents[name].run(query)
                return name, result
            except Exception as e:
                return name, f"Error: {e}"

        # Build coroutines for non-null tasks
        coros = []
        for name in ("weather", "flights", "hotels", "currency"):
            query = tasks.get(name)
            if query and name in self._agents:
                coros.append(_run_one(name, query))

        # Run in parallel
        pairs = await asyncio.gather(*coros)
        return {name: result for name, result in pairs}

    async def _synthesize(
        self, user_message: str, results: dict[str, str], history: list[dict] = None
    ) -> str:
        """Combine agent results into a final travel plan."""
        # Build research summary
        research_parts = []
        for name, result in results.items():
            research_parts.append(f"=== {name.upper()} RESEARCH ===\n{result}")
        research = "\n\n".join(research_parts)

        messages = [
            {"role": "system", "content": PLANNER_PROMPT},
        ]
        if history:
            messages.extend(history)
        messages.append({
            "role": "user",
            "content": (
                f"User's request: {user_message}\n\n"
                f"Research from specialist agents:\n\n{research}\n\n"
                "Please synthesize this into a helpful travel plan."
            ),
        })

        response = await self._openai.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
        )
        return response.choices[0].message.content or ""


