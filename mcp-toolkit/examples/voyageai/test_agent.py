#!/usr/bin/env python3
"""Test individual VoyageAI agents from the command line.

Run from examples/voyageai/:

    python test_agent.py weather "What's the weather in Tokyo?"
    python test_agent.py flights "Flights from London to New York"
    python test_agent.py hotels "Best hotels in Barcelona"
    python test_agent.py currency "Convert 500 USD to EUR"
    python test_agent.py all "Plan a trip to Paris"

Each run connects only to the servers that agent actually needs,
so you can diagnose which agent or server is failing in isolation.
"""

import asyncio
import sys
from contextlib import AsyncExitStack

from openai import AsyncOpenAI

from mcp_toolkit.clients.multi import MultiServerClient

from app.config import OPENAI_API_KEY, get_mcp_config
from app.agents.weather import WeatherAgent
from app.agents.flight import FlightAgent
from app.agents.hotel import HotelAgent
from app.agents.currency import CurrencyAgent

AGENTS = {
    "weather": WeatherAgent,
    "flights": FlightAgent,
    "hotels": HotelAgent,
    "currency": CurrencyAgent,
}


async def run(agent_name: str, query: str) -> None:
    names_to_run = list(AGENTS.keys()) if agent_name == "all" else [agent_name]

    # Collect only the server names this agent (or set of agents) needs
    servers_needed: set[str] = set()
    for name in names_to_run:
        servers_needed.update(AGENTS[name].server_names)

    # Load full config then trim to only required servers — avoids
    # connecting to (and needing API keys for) unrelated servers
    config = get_mcp_config()
    config.servers = {k: v for k, v in config.servers.items() if k in servers_needed}

    async with AsyncExitStack() as stack:
        client = MultiServerClient(config, api_key=OPENAI_API_KEY)
        mcp_client = await stack.enter_async_context(client)
        openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)

        print(f"\nServers  : {mcp_client.server_names}")
        print(f"Tools    : {mcp_client.tool_names}")
        print(f"Query    : {query}\n")

        for name in names_to_run:
            agent = AGENTS[name](mcp_client, openai_client)
            print(f"{'='*60}")
            print(f"  {name.upper()} AGENT")
            print(f"{'='*60}")
            result = await agent.run(query)
            print(result)
            print()


def main() -> None:
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    agent_name = sys.argv[1].lower()
    query = " ".join(sys.argv[2:])  # allow multi-word queries without quotes

    if agent_name not in AGENTS and agent_name != "all":
        print(f"Unknown agent '{agent_name}'. Choose from: {', '.join(AGENTS)} or 'all'")
        sys.exit(1)

    asyncio.run(run(agent_name, query))


if __name__ == "__main__":
    main()
