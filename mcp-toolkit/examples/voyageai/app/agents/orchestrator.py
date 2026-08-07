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
from contextlib import AsyncExitStack
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
        self._exit_stack: AsyncExitStack | None = None

    async def initialize(self) -> None:
        """Connect to all MCP servers and set up specialist agents."""
        self._exit_stack = AsyncExitStack()
        config = get_mcp_config()
        client = MultiServerClient(config, api_key=OPENAI_API_KEY)
        self._mcp_client = await self._exit_stack.enter_async_context(client)
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
        if self._exit_stack:
            await self._exit_stack.aclose()
            self._exit_stack = None
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

    async def plan(self, trip: dict) -> dict:
        """Plan a trip from structured input. Deterministically selects agents.

        Unlike chat(), this never uses an LLM to guess which agents to call —
        agents are selected based purely on which fields the user filled in.

        Args:
            trip: Dict with keys:
                destination    (required)
                origin         (optional) — triggers FlightAgent
                departure_date (optional)
                return_date    (optional)
                home_currency  (optional) — triggers CurrencyAgent

        Returns:
            Dict: agents_called (list), results (per-agent markdown), summary (str)
        """
        destination = trip.get("destination", "").strip()
        origin = trip.get("origin", "").strip()
        departure_date = trip.get("departure_date", "").strip()
        return_date = trip.get("return_date", "").strip()
        home_currency = trip.get("home_currency", "").strip()

        # Build targeted task strings
        tasks: dict[str, str] = {
            "weather": (
                f"Get current weather and forecast for {destination}"
                + (f" from {departure_date} to {return_date}" if departure_date and return_date
                   else f" around {departure_date}" if departure_date
                   else "")
            ),
            "hotels": (
                f"Find the top 5 hotels (with approximate price range per night) and top 5 "
                f"must-see attractions or activities in {destination}. Be specific with names."
            ),
        }
        if origin:
            date_str = f"departing {departure_date}" if departure_date else ""
            return_str = f", returning {return_date}" if return_date else ""
            tasks["flights"] = (
                f"Find 5 flight options from {origin} to {destination} {date_str}{return_str}. "
                "Include airline names, approximate duration, and IATA airport codes."
            )
        if home_currency:
            tasks["currency"] = (
                f"Get the current exchange rate from {home_currency} to the local currency "
                f"used in {destination}. Show converted amounts for 50, 100, 500, "
                f"and 1000 {home_currency}."
            )

        results = await self._run_agents(tasks)
        summary = await self._synthesize_plan(trip, results)

        return {
            "agents_called": list(results.keys()),
            "results": results,
            "summary": summary,
        }

    async def _synthesize_plan(self, trip: dict, results: dict) -> str:
        """Combine structured agent results into a travel itinerary."""
        destination = trip.get("destination", "")
        origin = trip.get("origin", "")
        departure_date = trip.get("departure_date", "")
        return_date = trip.get("return_date", "")

        trip_desc = f"{origin} → {destination}" if origin else f"Trip to {destination}"
        dates = ""
        if departure_date and return_date:
            dates = f" ({departure_date} to {return_date})"
        elif departure_date:
            dates = f" (from {departure_date})"

        research = "\n\n".join(
            f"=== {name.upper()} ===\n{content}"
            for name, content in results.items()
        )

        response = await self._openai.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": PLAN_PROMPT},
                {
                    "role": "user",
                    "content": f"Trip: {trip_desc}{dates}\n\nAgent research:\n\n{research}",
                },
            ],
        )
        return response.choices[0].message.content or ""



PLAN_PROMPT = """\
You are VoyageAI, an expert travel planner. Research from specialist agents is below.
Create a concise, practical travel itinerary using that research.

Use markdown with these sections:
## ✈️ Trip Overview
## 📅 Suggested Day-by-Day Plan
## 🌤 Weather & What to Pack
## 💰 Budget Tips

Be specific and practical. If some research is missing, note it briefly and continue.
"""



