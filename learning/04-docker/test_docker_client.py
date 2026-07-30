"""
Test client for the Dockerized MCP terminal server.

This script connects to the terminal server running inside a Docker container
and lets you interact with it via OpenAI (gpt-4o-mini) — same as the client
in 01-mcp-basics, but launching Docker instead of Python.

Usage (from repo root):
    uv run python learning/04-docker/test_docker_client.py
"""

import asyncio
import os
import sys
import json
from typing import Optional
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Path to repo root (go up 2 dirs from this script)
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
WORKSPACE_PATH = os.path.join(REPO_ROOT, "learning", "01-mcp-basics", "workspace")


async def main():
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # Launch the MCP server via Docker instead of Python
    server_params = StdioServerParameters(
        command="docker",
        args=[
            "run", "-i", "--rm", "--init",
            "-e", "DOCKER_CONTAINER=true",
            "-v", f"{WORKSPACE_PATH}:/workspace",
            "terminal_server_docker",
        ],
    )

    async with AsyncExitStack() as stack:
        transport = await stack.enter_async_context(stdio_client(server_params))
        read, write = transport
        session = await stack.enter_async_context(ClientSession(read, write))
        await session.initialize()

        # List available tools
        response = await session.list_tools()
        print("Connected to Docker MCP server with tools:", [t.name for t in response.tools])

        # Convert tools to OpenAI format
        tools = [
            {
                "type": "function",
                "name": t.name,
                "description": t.description,
                "parameters": t.inputSchema,
            }
            for t in response.tools
        ]

        print("\nDocker MCP Client Started! Type 'quit' to exit.")
        while True:
            query = input("\nQuery: ").strip()
            if query.lower() == "quit":
                break

            messages = [{"role": "user", "content": query}]

            while True:
                resp = openai_client.responses.create(
                    model="gpt-4o-mini", tools=tools, input=messages,
                )

                tool_called = False
                for item in resp.output:
                    if getattr(item, "type", None) == "function_call":
                        tool_called = True
                        args = json.loads(item.arguments or "{}")
                        print(f"[Tool call: {item.name} args={args}]")

                        messages.append(item.model_dump())
                        result = await session.call_tool(item.name, args)
                        tool_text = "\n".join(
                            getattr(p, "text", str(p)) for p in result.content
                        ) if isinstance(result.content, list) else str(result.content)

                        messages.append({
                            "type": "function_call_output",
                            "call_id": item.call_id,
                            "output": json.dumps({"result": tool_text}),
                        })

                if not tool_called:
                    print("\n" + (resp.output_text or ""))
                    break


if __name__ == "__main__":
    asyncio.run(main())
