"""
Quickstart: Anthropic Claude + MCP Server

Connect to any MCP server and chat with Claude in 5 lines.

Usage:
    python quickstart_anthropic.py path/to/your_server.py
"""

import asyncio
import sys

from mcp_toolkit.clients import AnthropicMCPClient


async def main():
    if len(sys.argv) < 2:
        print("Usage: python quickstart_anthropic.py <path_to_server.py>")
        sys.exit(1)

    server_script = sys.argv[1]

    async with AnthropicMCPClient(server_script=server_script) as client:
        await client.chat_loop()


if __name__ == "__main__":
    asyncio.run(main())
