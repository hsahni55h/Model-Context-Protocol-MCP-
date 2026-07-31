"""
Quickstart: LangChain Agent + MCP Server

Connect to any MCP server and let LangChain's React agent handle tool calling.

Usage:
    python quickstart_langchain.py path/to/your_server.py
"""

import asyncio
import sys

from mcp_toolkit.clients import LangChainMCPClient


async def main():
    if len(sys.argv) < 2:
        print("Usage: python quickstart_langchain.py <path_to_server.py>")
        sys.exit(1)

    server_script = sys.argv[1]

    async with LangChainMCPClient(server_script=server_script) as client:
        await client.chat_loop()


if __name__ == "__main__":
    asyncio.run(main())
