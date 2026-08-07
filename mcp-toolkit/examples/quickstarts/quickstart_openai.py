"""
Quickstart: OpenAI + MCP Server

Connect to any MCP server and chat with OpenAI in 5 lines.

Usage:
    # Use the bundled demo server (no setup needed)
    python quickstart_openai.py

    # Or point at your own server
    python quickstart_openai.py path/to/your_server.py
"""

import asyncio
import sys
from pathlib import Path

from mcp_toolkit.clients import OpenAIMCPClient

DEMO_SERVER = Path(__file__).parent / "demo_server.py"


async def main():
    server_script = sys.argv[1] if len(sys.argv) > 1 else str(DEMO_SERVER)

    async with OpenAIMCPClient(server_script=server_script) as client:
        await client.chat_loop()


if __name__ == "__main__":
    asyncio.run(main())
