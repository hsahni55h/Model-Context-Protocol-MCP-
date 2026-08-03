"""
Quickstart: Multi-Server Client

Connect to multiple MCP servers from a config file and chat with all tools at once.

Usage:
    python quickstart_multi.py

Expects a config file at mcp_servers.json (or set MCP_CONFIG env var):
{
  "mcpServers": {
    "weather": {
      "command": "python",
      "args": ["weather_server.py"]
    },
    "math": {
      "command": "python",
      "args": ["math_server.py"]
    }
  }
}
"""

import asyncio

from mcp_toolkit.clients import MultiServerClient


async def main():
    # Option 1: From config file
    client = MultiServerClient.from_config("mcp_servers.json")

    # Option 2: From a dict (uncomment to use)
    # client = MultiServerClient.from_dict({
    #     "weather": {"command": "python", "args": ["weather_server.py"]},
    #     "math": {"command": "python", "args": ["math_server.py"]},
    # })

    async with client:
        await client.chat_loop()


if __name__ == "__main__":
    asyncio.run(main())
