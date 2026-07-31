# Weather MCP Server

A simple MCP server demonstrating **tools** and **resources** using the free [wttr.in](https://wttr.in) API. No API keys required — the simplest possible MCP example to start with.

---

## Architecture

```
┌────────────────────┐       stdio (JSON-RPC)       ┌──────────────────────┐
│   MCP Inspector    │ ◄──────────────────────────► │   server.py (MCP)    │
│   (or any client)  │                              │                      │
└────────────────────┘                              │  ┌────────────────┐  │
                                                    │  │  check_weather │──┼──► wttr.in API
                                                    │  │  get_forecast  │──┼──► wttr.in API
                                                    │  │  compare_weather│─┼──► wttr.in API
                                                    │  └────────────────┘  │
                                                    │  ┌────────────────┐  │
                                                    │  │  Resource:     │  │
                                                    │  │  weather://    │  │
                                                    │  │  favorites     │  │
                                                    │  └────────────────┘  │
                                                    └──────────────────────┘
```

**Server (`server.py`):** A single-file MCP server built with `FastMCP`. It registers 3 tools and 1 resource, then communicates over stdio using the MCP protocol (JSON-RPC). Any MCP-compatible client can connect.

**Client:** The MCP Inspector (launched via `mcp dev`) or any LLM client that supports MCP (Claude Desktop, a custom LangChain agent, etc.).

---

## How MCP works here

1. The client spawns `server.py` as a subprocess and communicates over **stdio** (stdin/stdout)
2. On startup the server registers its tools and resources with the MCP protocol
3. The client calls `list_tools()` to discover what's available
4. When the user (or LLM) invokes a tool, the client sends a `CallToolRequest` over JSON-RPC
5. The server executes the tool function, calls the wttr.in API, and returns the result
6. The client can also call `read_resource("weather://favorites")` to get static context data

---

## MCP features demonstrated

| Feature | What it shows |
|---|---|
| **Multiple tools** | `check_weather`, `get_forecast`, `compare_weather` — LLM picks the right one based on the user query |
| **Resources** | `weather://favorites` — static data the LLM can read for context without using a tool |
| **Typed parameters** | `days: int = 3` — optional params with defaults; MCP schema auto-generated from type hints |
| **No auth needed** | Simplest possible setup — no `.env` file, no API keys |

---

## Tools

| Tool | Parameters | Description |
|---|---|---|
| `check_weather` | `city: str` | Current weather: condition, temperature, wind |
| `get_forecast` | `city: str`, `days: int = 3` | 1-3 day forecast with highs/lows |
| `compare_weather` | `city1: str`, `city2: str` | Side-by-side comparison of two cities |

## Resources

| URI | Description |
|---|---|
| `weather://favorites` | List of example cities to try (Paris, Sydney, Gothenburg, etc.) |

---

## Setup

```bash
# Install core dependencies (from repo root)
uv sync

# No .env file needed — wttr.in is completely free
```

---

## Running

### MCP Inspector

```bash
# From repo root
uv run mcp dev examples/weather/server.py
```

Open the Inspector URL in your browser, then:
1. Click **Tools** → select `check_weather` → enter `city: "Tokyo"` → Run
2. Click **Resources** → see `weather://favorites`
3. Try `compare_weather` with `city1: "London"`, `city2: "Sydney"`
4. Try `get_forecast` with `city: "Paris"`, `days: 2`

### Programmatic client (Python)

```python
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    params = StdioServerParameters(
        command="uv", args=["run", "python", "examples/weather/server.py"]
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # List available tools
            tools = await session.list_tools()
            print([t.name for t in tools.tools])

            # Call a tool
            result = await session.call_tool("check_weather", {"city": "London"})
            print(result.content[0].text)

            # Read a resource
            res = await session.read_resource("weather://favorites")
            print(res.contents[0].text)

asyncio.run(main())
```

---

## Example output

```
> check_weather("London")
London: ⛅ +18°C →11km/h

> get_forecast("Paris", days=2)
Forecast for Paris (2 days):
  2026-07-30: Partly Cloudy, 19°C - 28°C
  2026-07-31: Sunny, 21°C - 31°C

> compare_weather("Tokyo", "New York")
Tokyo: ☁️ +29°C ↗15km/h
New York: 🌧 +22°C →20km/h
```

---

## File structure

```
weather/
  server.py     ← MCP server with 3 tools + 1 resource (single file, ~95 lines)
  README.md
```

---

## Key takeaways

- **One file** is all you need for an MCP server — `FastMCP` handles all the protocol complexity
- **`@mcp.tool()`** decorator turns any function into an MCP tool with auto-generated JSON schema
- **`@mcp.resource()`** exposes static data that clients/LLMs can read for context
- **No client code needed** — the MCP Inspector acts as a universal test client
- Tools are **stateless** — each call is independent, making them easy to test and compose
