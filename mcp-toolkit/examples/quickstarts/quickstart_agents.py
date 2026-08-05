"""
Quickstart: Multi-Agent Pattern with BaseAgent

Shows how to build specialized agents that each own a subset of tools
from a MultiServerClient, then run them in parallel.

This demonstrates the mcp_toolkit.agents.BaseAgent boilerplate — the same
pattern used in the VoyageAI example, but distilled to its essentials.

Prerequisites:
    pip install "mcp-toolkit[openai]"
    export OPENAI_API_KEY=sk-...

Run from the mcp-toolkit/ directory:
    python examples/quickstarts/quickstart_agents.py

Config file format (mcp_servers.json):
    {
      "mcpServers": {
        "weather": {
          "command": "python",
          "args": ["weather_server.py"],
          "env": { "OPENWEATHER_API_KEY": "${OPENWEATHER_API_KEY}" }
        },
        "math": {
          "command": "python",
          "args": ["math_server.py"]
        }
      }
    }
"""

import asyncio

from openai import AsyncOpenAI

from mcp_toolkit.clients import MultiServerClient
from mcp_toolkit.agents import BaseAgent


# ── Define your specialist agents ─────────────────────────────────────────────

class WeatherAgent(BaseAgent):
    """Only has access to tools from the 'weather' MCP server."""
    server_names = ["weather"]
    system_prompt = """\
You are a weather research specialist.
Answer weather questions concisely using your tools.
Always include temperature and conditions in your response."""


class MathAgent(BaseAgent):
    """Only has access to tools from the 'math' MCP server."""
    server_names = ["math"]
    system_prompt = """\
You are a precise mathematical calculation specialist.
Use your tools to compute results accurately.
Show the calculation steps briefly."""


class GeneralistAgent(BaseAgent):
    """Has access to ALL tools across all connected servers."""
    # server_names left empty → uses all tools
    system_prompt = "You are a helpful assistant with access to multiple tools."


# ── Main ──────────────────────────────────────────────────────────────────────

async def main():
    openai_client = AsyncOpenAI()  # reads OPENAI_API_KEY from env

    async with MultiServerClient.from_config("mcp_servers.json") as mcp:
        print(f"Connected servers: {mcp.server_names}")
        print(f"All available tools: {mcp.tool_names}\n")

        # Instantiate agents — they share the same MCP + OpenAI connections
        weather_agent = WeatherAgent(mcp, openai_client)
        math_agent = MathAgent(mcp, openai_client)
        generalist = GeneralistAgent(mcp, openai_client)

        print(f"WeatherAgent tools: {weather_agent.tool_names}")
        print(f"MathAgent tools:    {math_agent.tool_names}")
        print(f"Generalist tools:   {generalist.tool_names}\n")

        # Run specialist agents in parallel
        weather_result, math_result = await asyncio.gather(
            weather_agent.run("What is the current weather in Tokyo?"),
            math_agent.run("What is 15% of 847, rounded to 2 decimal places?"),
        )

        print("=== Weather Agent ===")
        print(weather_result)
        print("\n=== Math Agent ===")
        print(math_result)

        # Run generalist on a follow-up
        followup = await generalist.run(
            "Based on the weather in Tokyo, should I pack an umbrella?",
            history=[
                {"role": "assistant", "content": weather_result},
            ],
        )
        print("\n=== Generalist follow-up ===")
        print(followup)


if __name__ == "__main__":
    asyncio.run(main())
