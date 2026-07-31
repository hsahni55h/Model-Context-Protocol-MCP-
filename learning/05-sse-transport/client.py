"""
MCP Client — SSE Transport (OpenAI)

Connects to an MCP server over SSE (HTTP) instead of stdio (subprocess).
Uses OpenAI gpt-4o-mini for tool-calling, same as 01-basics.

The key difference from 01-basics/client/openai_client.py:
  - stdio_client spawns a subprocess → only works locally
  - sse_client connects to a URL → works over the network

Usage:
    # Start the SSE server first (in another terminal):
    uv run python learning/05-sse-transport/server.py

    # Then run this client:
    uv run python learning/05-sse-transport/client.py http://localhost:8000/sse
"""

import asyncio
import os
import sys
import json
from pathlib import Path
from typing import Optional

from mcp import ClientSession
from mcp.client.sse import sse_client  # SSE transport (vs stdio_client)

from openai import OpenAI
from dotenv import load_dotenv

# Resolve .env from repo root
load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")


class MCPClient:
    def __init__(self):
        """Initialize the MCP client with OpenAI."""
        self.session: Optional[ClientSession] = None
        self._streams_context = None
        self._session_context = None

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found. Add it to your .env file.")

        self.openai_client = OpenAI(api_key=api_key)
        self.model_name = "gpt-4o-mini"
        self.tools = []

    async def connect(self, server_url: str):
        """Connect to an MCP server over SSE.

        Args:
            server_url: The SSE endpoint URL (e.g. http://localhost:8000/sse)
        """
        # sse_client returns an async context manager that yields (read, write) streams
        # — same interface as stdio_client, but over HTTP instead of subprocess pipes
        self._streams_context = sse_client(url=server_url)
        streams = await self._streams_context.__aenter__()

        self._session_context = ClientSession(*streams)
        self.session = await self._session_context.__aenter__()

        await self.session.initialize()

        response = await self.session.list_tools()
        mcp_tools = response.tools
        print(f"\nConnected to SSE server at {server_url}")
        print(f"Available tools: {[t.name for t in mcp_tools]}")

        self.tools = _convert_mcp_tools_to_openai(mcp_tools)

    async def process_query(self, query: str) -> str:
        """Send a query to OpenAI with MCP tool access.

        OpenAI decides whether to call tools. If it does, we execute them
        via the MCP session and feed results back until we get a final answer.
        """
        input_list = [{"role": "user", "content": query}]

        while True:
            response = self.openai_client.responses.create(
                model=self.model_name,
                tools=self.tools,
                input=input_list,
            )

            tool_calls_found = False

            for item in response.output:
                if getattr(item, "type", None) == "function_call":
                    tool_calls_found = True
                    tool_name = item.name
                    tool_args = json.loads(item.arguments or "{}")

                    print(f"\n[Calling tool: {tool_name}({tool_args})]")
                    input_list.append(item.model_dump())

                    try:
                        result = await self.session.call_tool(tool_name, tool_args)
                        tool_text = "\n".join(
                            getattr(part, "text", str(part))
                            for part in result.content
                        ) if isinstance(result.content, list) else str(result.content)
                        output = json.dumps({"result": tool_text})
                    except Exception as e:
                        output = json.dumps({"error": str(e)})

                    input_list.append({
                        "type": "function_call_output",
                        "call_id": item.call_id,
                        "output": output,
                    })
                elif getattr(item, "type", None) not in ("function_call",):
                    input_list.append(item.model_dump())

            if not tool_calls_found:
                return response.output_text or ""

    async def chat_loop(self):
        """Interactive chat — type queries, get responses. Type 'quit' to exit."""
        print("\nMCP SSE Client Started! Type 'quit' to exit.")

        while True:
            query = input("\nQuery: ").strip()
            if query.lower() == "quit":
                break
            response = await self.process_query(query)
            print("\n" + response)

    async def cleanup(self):
        """Close the SSE connection and MCP session."""
        if self._session_context:
            await self._session_context.__aexit__(None, None, None)
        if self._streams_context:
            await self._streams_context.__aexit__(None, None, None)


# --- Helpers ---

def _clean_schema(schema):
    """Recursively remove 'title' fields from JSON schema (OpenAI doesn't need them)."""
    if isinstance(schema, dict):
        schema.pop("title", None)
        for k, v in list(schema.items()):
            schema[k] = _clean_schema(v)
        return schema
    if isinstance(schema, list):
        return [_clean_schema(x) for x in schema]
    return schema


def _convert_mcp_tools_to_openai(mcp_tools):
    """Convert MCP tool definitions to OpenAI function calling format."""
    return [
        {
            "type": "function",
            "name": tool.name,
            "description": tool.description,
            "parameters": _clean_schema(tool.inputSchema),
        }
        for tool in mcp_tools
    ]


# --- Entry point ---

async def main():
    if len(sys.argv) < 2:
        print("Usage: uv run python learning/05-sse-transport/client.py <server_url>")
        print("Example: uv run python learning/05-sse-transport/client.py http://localhost:8000/sse")
        sys.exit(1)

    client = MCPClient()
    try:
        await client.connect(sys.argv[1])
        await client.chat_loop()
    finally:
        await client.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
