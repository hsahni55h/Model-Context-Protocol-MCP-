# MCP Toolkit

**Plug-and-play utilities for building MCP clients, servers, and agents with any LLM provider.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

---

## What is this?

MCP Toolkit gives you **pre-built, configurable components** for the [Model Context Protocol](https://modelcontextprotocol.io/) — so you can wire any LLM to any MCP server in a few lines of code instead of writing boilerplate from scratch.

```python
from mcp_toolkit.clients import OpenAIMCPClient

async with OpenAIMCPClient(server_script="my_server.py") as client:
    response = await client.chat("What's the weather in Paris?")
    print(response)
```

That's it. The client handles connection, tool discovery, the full tool-calling loop, and cleanup automatically.

---

## Installation

```bash
# Core (converters, config, transport abstraction)
pip install mcp-toolkit

# With your preferred LLM provider
pip install "mcp-toolkit[openai]"      # OpenAI
pip install "mcp-toolkit[gemini]"      # Google Gemini
pip install "mcp-toolkit[anthropic]"   # Anthropic Claude
pip install "mcp-toolkit[langchain]"   # LangChain + LangGraph agent

# Everything
pip install "mcp-toolkit[all]"
```

Or install from source (recommended for development):
```bash
cd mcp-toolkit
pip install -e ".[all,dev]"
```

---

## Quick Start

### 1. OpenAI

```python
import asyncio
from mcp_toolkit.clients import OpenAIMCPClient

async def main():
    async with OpenAIMCPClient(server_script="weather_server.py") as client:
        print(await client.chat("Compare weather in London and Tokyo"))

asyncio.run(main())
```

### 2. Google Gemini

```python
from mcp_toolkit.clients import GeminiMCPClient

async with GeminiMCPClient(server_script="weather_server.py") as client:
    print(await client.chat("What's the forecast for Sydney?"))
```

### 3. Anthropic Claude

```python
from mcp_toolkit.clients import AnthropicMCPClient

async with AnthropicMCPClient(server_script="weather_server.py") as client:
    print(await client.chat("Is it raining in Berlin?"))
```

### 4. LangChain Agent

```python
from mcp_toolkit.clients import LangChainMCPClient

async with LangChainMCPClient(server_script="server.py") as client:
    print(await client.chat("Summarize the file and answer my question"))
```

### 5. Multiple Servers

```python
from mcp_toolkit.clients import MultiServerClient

async with MultiServerClient.from_config("mcp_servers.json") as client:
    # The model can call tools from ANY connected server
    print(await client.chat("What's 2+2 and what's the weather in NYC?"))
```

`mcp_servers.json` format:
```json
{
  "mcpServers": {
    "weather": {
      "command": "python",
      "args": ["weather_server.py"],
      "env": { "API_KEY": "${OPENWEATHER_API_KEY}" }
    },
    "math": {
      "command": "python",
      "args": ["math_server.py"]
    },
    "tavily": {
      "url": "https://mcp.tavily.com/mcp/?tavilyApiKey=${TAVILY_API_KEY}",
      "transport": "streamable_http"
    }
  }
}
```

> **`${VAR}` placeholders** in `url` and `env` values are automatically resolved from environment variables when the config is loaded.

### 6. Multi-Agent Pattern

Build specialized agents — each owning a subset of tools — that run in parallel:

```python
import asyncio
from openai import AsyncOpenAI
from mcp_toolkit.clients import MultiServerClient
from mcp_toolkit.agents import BaseAgent

class WeatherAgent(BaseAgent):
    server_names = ["weather"]
    system_prompt = "You are a weather research specialist."

class FlightAgent(BaseAgent):
    server_names = ["flights"]
    system_prompt = "You are a flight search specialist."

async def main():
    openai_client = AsyncOpenAI()
    async with MultiServerClient.from_config("mcp_servers.json") as mcp:
        weather = WeatherAgent(mcp, openai_client)
        flights = FlightAgent(mcp, openai_client)

        # Run in parallel
        weather_result, flight_result = await asyncio.gather(
            weather.run("Weather in Tokyo next week?"),
            flights.run("Flights from London to Tokyo?"),
        )

asyncio.run(main())
```

### 7. Low-Level Transport Access

```python
from mcp_toolkit import connect

async with connect(script="server.py") as session:
    tools = await session.list_tools()
    result = await session.call_tool("check_weather", {"city": "Paris"})
```

---

## Architecture

```
Your Application
      │
      ├── mcp_toolkit.clients         ← Pick your LLM provider
      │     ├── OpenAIMCPClient        (openai.responses API)
      │     ├── GeminiMCPClient        (google-genai)
      │     ├── AnthropicMCPClient     (anthropic)
      │     ├── LangChainMCPClient     (langgraph react agent)
      │     └── MultiServerClient      (multiple servers, any LLM)
      │
      ├── mcp_toolkit.agents          ← Reusable agent boilerplate
      │     └── BaseAgent              (OpenAI Chat Completions loop)
      │
      ├── mcp_toolkit.converters      ← Tool schema format conversion
      │     ├── mcp_to_openai()        (Responses API format)
      │     ├── mcp_to_openai_chat()   (Chat Completions format)
      │     ├── mcp_to_gemini()        (FunctionDeclaration dicts)
      │     ├── mcp_to_anthropic()     (Anthropic tool format)
      │     └── clean_schema()         (strips 'title' fields)
      │
      ├── mcp_toolkit.config          ← Config loading
      │     ├── load_config()          (JSON file + ${VAR} resolution)
      │     ├── load_config_from_dict()
      │     ├── MCPConfig
      │     └── MCPServerConfig
      │
      ├── mcp_toolkit.transports      ← Low-level connection abstraction
      │     └── connect()              (stdio / SSE / streamable_http)
      │
      └── mcp_toolkit.server          ← Server-side helpers
            ├── load_env()             (auto-find .env file)
            ├── openai_helper()        (quick OpenAI call in tools)
            └── get_env_or_raise()     (env var with helpful errors)
```

---

## Modules

### `mcp_toolkit.clients`

Pre-built clients that handle the full tool-calling loop. Pick the one matching your LLM.

| Class | Provider | Tool-call loop | Notes |
|-------|----------|---------------|-------|
| `OpenAIMCPClient` | OpenAI | ✅ Full loop | Uses Responses API |
| `GeminiMCPClient` | Google Gemini | ✅ Full loop | Multi-round supported |
| `AnthropicMCPClient` | Anthropic Claude | ✅ Full loop | Handles `tool_use` blocks |
| `LangChainMCPClient` | OpenAI via LangGraph | ✅ React agent | Needs `langchain` extra |
| `MultiServerClient` | OpenAI | ✅ Full loop | Aggregates N servers |

All single-server clients accept the same connection options:

```python
# Option 1: stdio server (subprocess)
async with OpenAIMCPClient(server_script="my_server.py") as client: ...

# Option 2: SSE server (URL)
async with OpenAIMCPClient(server_url="http://localhost:8000/sse") as client: ...

# Option 3: From a config object
from mcp_toolkit.config import MCPServerConfig
cfg = MCPServerConfig(name="s", command="python", args=["server.py"])
async with OpenAIMCPClient(server_config=cfg) as client: ...

# Option 4: Interactive terminal loop
async with OpenAIMCPClient(server_script="server.py") as client:
    await client.chat_loop()
```

#### `MultiServerClient` — connecting multiple servers

```python
from mcp_toolkit.clients import MultiServerClient

# From config file
async with MultiServerClient.from_config("mcp_servers.json") as mcp:
    print(mcp.server_names)   # ['weather', 'math', 'tavily']
    print(mcp.tool_names)     # ['get_weather', 'add', 'tavily_search', ...]
    print(mcp.all_tools)      # raw MCP tool objects (for converters)

    # Tools are automatically routed to the correct server
    result = await mcp.call_tool("get_weather", {"city": "Tokyo"})

    # Get tool names for a specific server
    weather_tools = mcp.get_tools_by_server("weather")

# From a dict
async with MultiServerClient.from_dict({
    "weather": {"command": "python", "args": ["weather_server.py"]},
    "math": {"command": "python", "args": ["math_server.py"]},
}) as mcp: ...
```

---

### `mcp_toolkit.agents`

Reusable `BaseAgent` class for building multi-agent applications on top of `MultiServerClient`.

```python
from mcp_toolkit.agents import BaseAgent

class WeatherAgent(BaseAgent):
    server_names = ["weather"]          # tools this agent can use
    system_prompt = "You are a weather specialist."
    max_tool_rounds = 5                 # optional, default 10

class GeneralistAgent(BaseAgent):
    # empty server_names → access to ALL tools
    system_prompt = "You are a helpful assistant."
```

**How `BaseAgent` works:**
1. On init, filters `mcp_client.all_tools` to tools from its `server_names`
2. `run(query)` sends the query via OpenAI Chat Completions with those tools
3. Executes any tool calls via `mcp_client.call_tool()` (auto-routed to the right server)
4. Loops until the LLM produces a plain-text response
5. Supports optional `history` parameter for multi-turn conversations

```python
# Pass conversation history for context
result = await agent.run(
    "Should I pack an umbrella?",
    history=[
        {"role": "user", "content": "I'm going to Tokyo next week."},
        {"role": "assistant", "content": "Tokyo in July is warm and humid..."},
    ],
)
```

---

### `mcp_toolkit.converters`

Convert MCP tool objects to the format expected by each LLM provider. All converters also call `clean_schema()` to strip `title` fields that many providers reject.

```python
from mcp_toolkit.converters import (
    mcp_to_openai,       # Responses API  — openai.responses.create()
    mcp_to_openai_chat,  # Chat API       — openai.chat.completions.create()
    mcp_to_gemini,       # Gemini         — genai types.Tool(function_declarations=...)
    mcp_to_anthropic,    # Claude         — client.messages.create(tools=...)
    clean_schema,        # Schema cleaner — strips all 'title' keys recursively
)
```

#### Which OpenAI converter to use?

| Converter | API call | Format |
|-----------|----------|--------|
| `mcp_to_openai()` | `openai.responses.create()` | `{"type": "function", "name": ..., "parameters": ...}` |
| `mcp_to_openai_chat()` | `openai.chat.completions.create()` | `{"type": "function", "function": {"name": ..., ...}}` |

Use `mcp_to_openai_chat()` for most real-world applications using `AsyncOpenAI`:

```python
from mcp_toolkit.converters import mcp_to_openai_chat

tools = mcp_to_openai_chat(mcp.all_tools)
response = await openai_client.chat.completions.create(
    model="gpt-4o",
    messages=messages,
    tools=tools,
)
```

---

### `mcp_toolkit.config`

Load and validate MCP server configurations from JSON files or dicts.

```python
from mcp_toolkit.config import load_config, load_config_from_dict, MCPServerConfig

# From a JSON file (auto-resolves ${VAR} placeholders in url and env)
config = load_config("mcp_servers.json")
# Falls back to $MCP_CONFIG env var, then mcp_servers.json in cwd

# From a dict
config = load_config_from_dict({
    "mcpServers": {
        "weather": {"command": "python", "args": ["server.py"]}
    }
})

# Programmatic single server
server = MCPServerConfig(
    name="weather",
    command="python",
    args=["weather_server.py"],
    env={"API_KEY": "abc123"},
)
print(server.transport)  # "stdio"

# SSE server
remote = MCPServerConfig(name="search", url="http://localhost:8000/sse")
print(remote.transport)  # "sse"

# Streamable HTTP (e.g. Tavily, hosted MCP services)
tavily = MCPServerConfig(
    name="tavily",
    url="https://mcp.tavily.com/mcp/?tavilyApiKey=xxx",
    transport_type="streamable_http",
)
```

**`${VAR}` placeholder resolution** happens automatically in `load_config()`. Any `${ENV_VAR_NAME}` in `url` or `env` values is replaced with the corresponding environment variable:

```json
{
  "mcpServers": {
    "search": {
      "url": "https://mcp.example.com/?key=${MY_API_KEY}",
      "transport": "streamable_http"
    },
    "myserver": {
      "command": "python",
      "args": ["server.py"],
      "env": { "SECRET": "${MY_SECRET}" }
    }
  }
}
```

---

### `mcp_toolkit.transports`

Low-level connection abstraction. Use when you need direct `ClientSession` access without the full client wrapper.

```python
from mcp_toolkit import connect

# stdio (subprocess)
async with connect(script="server.py") as session:
    tools = await session.list_tools()
    result = await session.call_tool("my_tool", {"arg": "value"})

# SSE
async with connect(url="http://localhost:8000/sse") as session: ...

# Streamable HTTP
from mcp_toolkit.config import MCPServerConfig
cfg = MCPServerConfig(name="t", url="https://api.example.com/mcp", transport_type="streamable_http")
async with connect(config=cfg) as session: ...

# Explicit command + args
async with connect(command="python", args=["server.py"]) as session: ...
```

Supported transports: `stdio` (subprocess), `sse` (HTTP + Server-Sent Events), `streamable_http` (modern HTTP MCP transport).

---

### `mcp_toolkit.server`

Utility helpers for building MCP servers.

```python
from mcp_toolkit.server import load_env, openai_helper, get_env_or_raise

# Auto-find and load .env from any parent directory
# Useful in servers that are run from arbitrary working directories
load_env()

# Quick OpenAI call inside your tool implementations
# (e.g. for AI-powered summarization, extraction, classification)
summary = openai_helper(
    f"Summarize this job description: {text}",
    system="You are a concise summarizer.",
    model="gpt-4o-mini",
    max_tokens=200,
)

# Get a required env var with a helpful error message
api_key = get_env_or_raise("MY_SERVICE_API_KEY")
```

> **Why only an OpenAI helper and not Gemini/Anthropic?**
>
> OpenAI's Python SDK ships a **synchronous** client (`openai.OpenAI`) that works like a regular function — no `await` needed. This makes it safe to wrap in a plain `def openai_helper(...)`.
>
> Gemini and Anthropic's SDKs are **async-only** — they require `await`. You can't wrap them in a plain function because calling `asyncio.run()` inside an already-running async server crashes with `RuntimeError: This event loop is already running`.
>
> For Gemini or Anthropic inside a tool, just `await` the SDK directly — your MCP tool functions are already `async def`:
>
> ```python
> from anthropic import AsyncAnthropic
>
> client = AsyncAnthropic()
>
> @mcp.tool()
> async def summarize(text: str) -> str:
>     response = await client.messages.create(
>         model="claude-sonnet-4-20250514",
>         max_tokens=200,
>         messages=[{"role": "user", "content": f"Summarize: {text}"}],
>     )
>     return response.content[0].text
> ```

---

## Building Your Own MCP Server

The toolkit works with **any** MCP server — you can build one using `FastMCP`:

```python
# my_server.py
import os
import httpx
from mcp.server.fastmcp import FastMCP
from mcp_toolkit.server import load_env, get_env_or_raise

load_env()  # auto-finds .env file

mcp = FastMCP("my-tools")

@mcp.tool()
async def search_products(query: str, max_results: int = 5) -> str:
    """Search our product catalog.

    Args:
        query: Search query string
        max_results: Maximum number of results to return (default 5)
    """
    api_key = get_env_or_raise("CATALOG_API_KEY")
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://api.mystore.com/search",
            params={"q": query, "limit": max_results},
            headers={"Authorization": f"Bearer {api_key}"},
        )
        data = resp.json()
    return "\n".join(f"- {p['name']}: ${p['price']}" for p in data["products"])

if __name__ == "__main__":
    mcp.run()
```

Connect with any toolkit client:
```python
async with OpenAIMCPClient(server_script="my_server.py") as client:
    print(await client.chat("Find me a red jacket under $100"))
```

---

## Configuration Reference

### Environment Variables

| Variable | Used by | Required for |
|----------|---------|-------------|
| `OPENAI_API_KEY` | OpenAI client, MultiServerClient, LangChain, `openai_helper()` | OpenAI features |
| `GEMINI_API_KEY` | Gemini client | Gemini features |
| `ANTHROPIC_API_KEY` | Anthropic client | Claude features |
| `MCP_CONFIG` | `load_config()` | Alternative to explicit config path |

### All Client Options

All single-server clients share these base options:

| Parameter | Type | Description |
|-----------|------|-------------|
| `server_script` | `str` | Path to a `.py` or `.js` server file (stdio) |
| `server_url` | `str` | HTTP endpoint URL (SSE transport) |
| `server_config` | `MCPServerConfig` | Pre-built config object |
| `command` | `str` | Override the interpreter command |
| `args` | `list[str]` | Override the command arguments |
| `system_prompt` | `str` | LLM system prompt |
| `model` | `str` | Model name (provider-specific defaults) |
| `temperature` | `float` | Sampling temperature (default: `0`) |
| `api_key` | `str` | API key override (falls back to env var) |

Provider defaults:

| Client | Default model |
|--------|--------------|
| `OpenAIMCPClient` | `gpt-4o-mini` |
| `GeminiMCPClient` | `gemini-2.0-flash-001` |
| `AnthropicMCPClient` | `claude-sonnet-4-20250514` |
| `LangChainMCPClient` | `gpt-4o-mini` |
| `MultiServerClient` | `gpt-4o-mini` |

### `MCPServerConfig` Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Human-readable server name |
| `command` | `str` | Command to start the server (e.g. `"python"`, `"node"`) |
| `args` | `list[str]` | Arguments to the command |
| `env` | `dict[str, str]` | Environment variables for the subprocess |
| `url` | `str` | HTTP endpoint for SSE / streamable_http |
| `transport_type` | `str` | Explicit transport override: `"stdio"`, `"sse"`, or `"streamable_http"` |

---

## Project Structure

```
mcp-toolkit/
├── pyproject.toml                  # Package config + optional extras
├── README.md
├── src/mcp_toolkit/
│   ├── __init__.py                 # Top-level public API exports
│   ├── converters.py               # mcp_to_openai, mcp_to_openai_chat,
│   │                               #   mcp_to_gemini, mcp_to_anthropic, clean_schema
│   ├── config.py                   # load_config, MCPServerConfig, MCPConfig
│   │                               #   + ${VAR} env placeholder resolution
│   ├── transports.py               # connect() — unified stdio/SSE/streamable_http
│   ├── clients/
│   │   ├── __init__.py             # Lazy-loaded client exports
│   │   ├── base.py                 # BaseMCPClient — shared connection + call_tool logic
│   │   ├── openai.py               # OpenAIMCPClient
│   │   ├── gemini.py               # GeminiMCPClient
│   │   ├── anthropic.py            # AnthropicMCPClient
│   │   ├── langchain.py            # LangChainMCPClient
│   │   └── multi.py                # MultiServerClient
│   ├── agents/
│   │   ├── __init__.py             # Exports BaseAgent
│   │   └── base.py                 # BaseAgent — subclass with server_names +
│   │                               #   system_prompt for a ready-made agent
│   └── server/
│       ├── __init__.py             # Exports server helpers
│       └── helpers.py              # load_env, openai_helper, get_env_or_raise
├── examples/
│   ├── quickstarts/
│   │   ├── quickstart_openai.py    # OpenAI interactive demo
│   │   ├── quickstart_gemini.py    # Gemini interactive demo
│   │   ├── quickstart_anthropic.py # Claude interactive demo
│   │   ├── quickstart_langchain.py # LangChain interactive demo
│   │   ├── quickstart_multi.py     # Multi-server interactive demo
│   │   ├── quickstart_agents.py    # BaseAgent parallel agents demo
│   │   └── direct_transport.py     # Low-level connect() demo
│   └── voyageai/                   # Full showcase app (multi-agent travel planner)
└── tests/
    ├── test_config.py
    ├── test_converters.py
    └── test_transports.py
```

---

## Running the Examples

```bash
# Install the toolkit in dev mode first
cd mcp-toolkit
pip install -e ".[all,dev]"

# Run any quickstart (from mcp-toolkit/ directory)
python examples/quickstarts/quickstart_openai.py path/to/your_server.py
python examples/quickstarts/quickstart_gemini.py path/to/your_server.py
python examples/quickstarts/quickstart_anthropic.py path/to/your_server.py
python examples/quickstarts/quickstart_langchain.py path/to/your_server.py

# Multi-server (needs mcp_servers.json in cwd)
python examples/quickstarts/quickstart_multi.py

# BaseAgent parallel pattern
python examples/quickstarts/quickstart_agents.py

# Low-level transport
python examples/quickstarts/direct_transport.py

# Full showcase app
cd examples/voyageai
uvicorn app.main:app --reload
```

---

## Development

```bash
cd mcp-toolkit
pip install -e ".[all,dev]"

# Run all tests
pytest

# Run with verbose output
pytest -v

# Run a specific module
pytest tests/test_converters.py -v
pytest tests/test_config.py -v
```

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Make your changes with tests
4. Run the test suite (`pytest`)
5. Commit and push
6. Open a Pull Request

---

## License

MIT — see [LICENSE](../LICENSE) for details.


