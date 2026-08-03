"""
Example: Using the transport abstraction directly

Shows how to use mcp_toolkit.connect() for low-level MCP access
without the full client wrapper.
"""

import asyncio

from mcp_toolkit import connect


async def main():
    # Connect to a server via stdio
    async with connect(script="../../examples/weather/server.py") as session:
        # List available tools
        response = await session.list_tools()
        print("Available tools:")
        for tool in response.tools:
            print(f"  - {tool.name}: {tool.description}")

        # Call a tool directly
        result = await session.call_tool("check_weather", {"city": "Paris"})
        print(f"\nWeather in Paris: {result.content}")

    # Or connect via SSE (uncomment if you have an SSE server running)
    # async with connect(url="http://localhost:8000/sse") as session:
    #     result = await session.call_tool("check_weather", {"city": "Tokyo"})
    #     print(f"Weather in Tokyo: {result.content}")


if __name__ == "__main__":
    asyncio.run(main())
