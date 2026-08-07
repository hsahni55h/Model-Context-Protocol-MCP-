# MCP Toolkit

**Plug-and-play utilities for building MCP clients, servers, and agents with any LLM provider.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

---

## What is this?

[Model Context Protocol (MCP)](https://modelcontextprotocol.io/) is an open standard that lets LLMs call external tools — APIs, databases, file systems, or any custom logic — in a structured way.

MCP Toolkit gives you **pre-built, configurable components** so you can connect any LLM to any MCP server in a few lines of code instead of writing connection management, tool discovery, and tool-calling loops from scratch.

```python
from mcp_toolkit.clients import OpenAIMCPClient

async with OpenAIMCPClient(server_script="my_server.py") as client:
    response = await client.chat("What's the weather in Paris?")
    print(response)
```

That one block handles: launching the server subprocess, establishing the MCP session, discovering all available tools, sending your message to the LLM with those tools attached, executing any tool calls the LLM requests, feeding results back, and repeating until a final answer is produced. All you write is the `async with` block.

---

## Table of Contents

1. [Installation](#installation)
2. [30-Second Quick Start](#30-second-quick-start)
3. [Core Concepts](#core-concepts)
4. [Module Reference](#module-reference)
   - [clients](#mcp_toolkitclients)
   - [agents](#mcp_toolkitagents)
   - [converters](#mcp_toolkitconverters)
   - [config](#mcp_toolkitconfig)
   - [transports](#mcp_toolkittransports)
   - [server](#mcp_toolkitserver)
5. [Building an MCP Server](#building-an-mcp-server)
6. [Configuration Reference](#configuration-reference)
7. [Examples](#examples)
8. [Project Structure](#project-structure)
9. [Running Tests](#running-tests)

---

## Installation

```bash
# Core only (converters, config, transports — no LLM provider)
pip install mcp-toolkit

# With your LLM provider
pip install "mcp-toolkit[openai]"      # OpenAI (gpt-4o, gpt-4o-mini, etc.)
pip install "mcp-toolkit[gemini]"      # Google Gemini
pip install "mcp-toolkit[anthropic]"   # Anthropic Claude
pip install "mcp-toolkit[langchain]"   # LangChain + LangGraph agent

# Everything at once
pip install "mcp-toolkit[all]"
```

**From source (recommended for development or running examples):**

```bash
git clone https://github.com/hsahni55h/Model-Context-Protocol-MCP-.git
cd Model-Context-Protocol-MCP-/mcp-toolkit
pip install -e ".[all,dev]"
```

---

## 30-Second Quick Start

The toolkit ships with a zero-config demo server (`examples/quickstarts/demo_server.py`) so you can verify your install immediately — no API keys, no external services needed for the server side.

```bash
cd mcp-toolkit
pip install -e ".[openai]"
export OPENAI_API_KEY=sk-...

# Run the interactive demo — no extra arguments needed
python examples/quickstarts/quickstart_openai.py
```

```
MCP Client ready! Tools: ['echo', 'add', 'greet']
You: add 15 and 27
Assistant: The result is 42.
You: greet Himanshu
Assistant: Hello, Himanshu! Welcome to MCP Toolkit.
You: quit
```

Once that works, replace `demo_server.py` with your own:

```bash
python examples/quickstarts/quickstart_openai.py path/to/your_server.py
```

---

## Core Concepts

Before diving into the API, here are the three things worth understanding:

### 1. Transport = how the client talks to the server

MCP supports three transports. The toolkit handles all of them automatically:

| Transport | When to use | Example |
|-----------|-------------|---------|
| **stdio** | Local server scripts you run as a subprocess | `server_script="weather.py"` |
| **SSE** | Self-hosted HTTP servers | `server_url="http://localhost:8000/sse"` |
| **streamable_http** | Hosted MCP services (Tavily, etc.) | `url` + `"transport": "streamable_http"` in config |

The client auto-detects the transport from what you provide — you rarely need to specify it explicitly.

### 2. The tool-calling loop

Every client runs this loop automatically inside `chat()`:

```
You send a message
    → LLM decides which tool(s) to call
    → Client executes those tools via MCP
    → Results fed back to LLM
    → LLM decides: call more tools, or answer?
    → Loop until final text answer
    → Return the answer to you
```

### 3. Single server vs. multi-server

- **Single server** (`OpenAIMCPClient`, `GeminiMCPClient`, etc.) — connect to one MCP server, chat with the LLM using those tools.
- **Multi-server** (`MultiServerClient`) — connect to N servers at once. The LLM can call any tool from any server. Tool routing is handled automatically.
- **Multi-agent** (`BaseAgent` + `MultiServerClient`) — connect N servers, then give each specialist agent a filtered subset of tools. Agents can run in parallel.

---

## Module Reference

### `mcp_toolkit.clients`

Pre-built, ready-to-use clients for every major LLM provider. Each one:
- Manages the server connection lifecycle (connect on enter, disconnect on exit)
- Discovers all available tools on connection
- Runs the full tool-calling loop inside `chat()`
- Provides `chat_loop()` for interactive terminal sessions

#### Available clients

| Class | Provider | Notes |
|-------|----------|-------|
| `OpenAIMCPClient` | OpenAI | Chat Completions API (`gpt-4o-mini` default) |
| `GeminiMCPClient` | Google Gemini | `gemini-2.0-flash-001` default |
| `AnthropicMCPClient` | Anthropic Claude | `claude-sonnet-4-20250514` default |
| `LangChainMCPClient` | OpenAI via LangGraph | React agent; needs `langchain` extra |
| `MultiServerClient` | OpenAI | Aggregates tools from N servers |

#### Connection options (all single-server clients)

All clients accept the same three ways to specify a server. Use whichever fits your setup:

```python
from mcp_toolkit.clients import OpenAIMCPClient

# Option 1 — stdio: path to a local server script
# The interpreter is auto-detected: .py → python, .js → node, .ts → npx
async with OpenAIMCPClient(server_script="my_server.py") as client:
    ...

# Option 2 — SSE: an HTTP endpoint
async with OpenAIMCPClient(server_url="http://localhost:8000/sse") as client:
    ...

# Option 3 — MCPServerConfig object (useful for programmatic setup)
from mcp_toolkit.config import MCPServerConfig
cfg = MCPServerConfig(name="weather", command="python", args=["weather_server.py"])
async with OpenAIMCPClient(server_config=cfg) as client:
    ...
```

#### OpenAI example

```python
import asyncio
from mcp_toolkit.clients import OpenAIMCPClient

async def main():
    async with OpenAIMCPClient(
        server_script="weather_server.py",
        model="gpt-4o-mini",       # optional, this is the default
        system_prompt="You are a helpful travel weather assistant.",
        temperature=0,             # optional, default 0
    ) as client:
        # Single question
        answer = await client.chat("What's the weather like in Tokyo right now?")
        print(answer)

        # Interactive terminal loop
        await client.chat_loop()

asyncio.run(main())
```

#### Gemini example

```python
from mcp_toolkit.clients import GeminiMCPClient

async with GeminiMCPClient(
    server_script="weather_server.py",
    model="gemini-2.0-flash-001",
) as client:
    print(await client.chat("Will it rain in Sydney this weekend?"))
```

#### Anthropic Claude example

```python
from mcp_toolkit.clients import AnthropicMCPClient

async with AnthropicMCPClient(
    server_script="weather_server.py",
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
) as client:
    print(await client.chat("What should I pack for a trip to London in January?"))
```

#### LangChain example

```python
from mcp_toolkit.clients import LangChainMCPClient

# Uses LangGraph's React agent under the hood
# Requires: pip install "mcp-toolkit[langchain]"
async with LangChainMCPClient(server_script="server.py") as client:
    print(await client.chat("Summarize the README file and list action items"))
```

#### `MultiServerClient` — connecting multiple servers at once

The most powerful client. Connect to N servers simultaneously; all their tools are aggregated into a single pool and the LLM can call any of them.

```python
import asyncio
from mcp_toolkit.clients import MultiServerClient

async def main():
    # From a JSON config file (recommended)
    async with MultiServerClient.from_config("mcp_servers.json") as mcp:

        print(mcp.server_names)            # ['weather', 'math', 'flights']
        print(mcp.tool_names)              # ['get_weather', 'add', 'search_flights', ...]
        print(mcp.get_tools_by_server("weather"))  # ['get_weather', 'get_forecast']

        # The LLM can call tools from any server automatically
        answer = await mcp.chat(
            "What's 15% of 340, and what's the weather in the cheapest city to fly to from NYC?"
        )
        print(answer)

asyncio.run(main())
```

**`mcp_servers.json` format:**

```json
{
  "mcpServers": {
    "weather": {
      "command": "python",
      "args": ["servers/weather_server.py"],
      "env": {
        "OPENWEATHER_API_KEY": "${OPENWEATHER_API_KEY}"
      }
    },
    "math": {
      "command": "python",
      "args": ["servers/math_server.py"]
    },
    "tavily": {
      "url": "https://mcp.tavily.com/mcp/?tavilyApiKey=${TAVILY_API_KEY}",
      "transport": "streamable_http"
    }
  }
}
```

> **`${VAR}` placeholders** in `url` and `env` values are automatically substituted from environment variables when the config is loaded. Unset variables are replaced with an empty string.

You can also build the client from a Python dict without a file:

```python
async with MultiServerClient.from_dict({
    "weather": {"command": "python", "args": ["weather_server.py"]},
    "math":    {"command": "python", "args": ["math_server.py"]},
}) as mcp:
    ...
```

---

### `mcp_toolkit.agents`

`BaseAgent` is a reusable base class for building **specialist agents** on top of `MultiServerClient`. Each agent gets its own system prompt and a filtered view of tools — only the tools from its designated servers.

This is the pattern used by the VoyageAI example where `WeatherAgent`, `FlightAgent`, `HotelAgent`, and `CurrencyAgent` all share the same MCP connection but operate independently.

#### Defining agents

```python
from mcp_toolkit.agents import BaseAgent

class WeatherAgent(BaseAgent):
    server_names = ["weather"]       # only sees tools from the 'weather' server
    system_prompt = """You are a weather research specialist.
    Always include temperature, conditions, and a brief forecast."""
    max_tool_rounds = 5              # optional; default is 10

class FlightAgent(BaseAgent):
    server_names = ["flights"]
    system_prompt = "You are a flight search specialist. Find the best routes."

class GeneralistAgent(BaseAgent):
    server_names = []                # empty = access to ALL tools from all servers
    system_prompt = "You are a helpful assistant with many tools available."
```

#### Running agents

```python
import asyncio
from openai import AsyncOpenAI
from mcp_toolkit.clients import MultiServerClient
from mcp_toolkit.agents import BaseAgent

# Define agents (as above)

async def main():
    openai_client = AsyncOpenAI()

    async with MultiServerClient.from_config("mcp_servers.json") as mcp:
        weather = WeatherAgent(mcp, openai_client)
        flights = FlightAgent(mcp, openai_client)

        # Run a single agent
        result = await weather.run("What's the weather in Tokyo next week?")
        print(result)

        # Run multiple agents in parallel (asyncio.gather)
        weather_result, flight_result = await asyncio.gather(
            weather.run("Weather forecast for Tokyo, 7 days"),
            flights.run("Cheapest flights from London to Tokyo in July"),
        )

asyncio.run(main())
```

#### Multi-turn conversations

Pass `history` to give an agent context from a previous exchange:

```python
history = [
    {"role": "user", "content": "I'm planning a trip to Tokyo in July."},
    {"role": "assistant", "content": "Great choice! Tokyo in July is warm and humid..."},
]

result = await weather.run(
    "Should I pack an umbrella?",
    history=history,   # agent now knows the context
)
```

#### How `BaseAgent` works internally

1. On `__init__`, it filters `mcp_client.all_tools` to only tools from its `server_names`
2. `run(query)` builds a messages list: `[system, ...history, user_query]`
3. Calls `openai.chat.completions.create()` with the filtered tool list
4. If the LLM returns tool calls, executes each one via `mcp_client.call_tool()` (auto-routed to the right server)
5. Appends tool results to the message history and loops
6. Returns the first plain-text response
7. If `max_tool_rounds` is hit, forces a final answer without tools (prevents infinite loops)

---

### `mcp_toolkit.converters`

Convert MCP tool objects to the schema format expected by each LLM provider's API. You need these when calling LLM APIs directly (e.g., when building a custom loop or a low-level integration).

```python
from mcp_toolkit.converters import (
    mcp_to_openai_completions,  # OpenAI Chat Completions API
    mcp_to_openai_responses,    # OpenAI Responses API
    mcp_to_gemini,              # Google Gemini
    mcp_to_anthropic,           # Anthropic Claude
    clean_schema,               # strips 'title' fields from any JSON schema
)
```

All converters call `clean_schema()` internally, so you don't need to call it separately.

#### OpenAI — which converter to use?

OpenAI has two APIs with different tool formats:

| Converter | API | Tool format |
|-----------|-----|-------------|
| `mcp_to_openai_completions()` | `openai.chat.completions.create()` | `{"type": "function", "function": {"name": ..., "parameters": ...}}` |
| `mcp_to_openai_responses()` | `openai.responses.create()` | `{"type": "function", "name": ..., "parameters": ...}` |

**Use `mcp_to_openai_completions()` for most applications** — the Chat Completions API is the standard, supported by every model, and what `BaseAgent`, `OpenAIMCPClient`, and `MultiServerClient` all use internally.

```python
from mcp_toolkit.converters import mcp_to_openai_completions

# In a custom tool-calling loop:
tools = mcp_to_openai_completions(mcp.all_tools)
response = await openai_client.chat.completions.create(
    model="gpt-4o",
    messages=messages,
    tools=tools,
)
```

#### Gemini example

```python
from mcp_toolkit.converters import mcp_to_gemini
from google.genai import types

declarations = mcp_to_gemini(mcp_tools)
gemini_tools = [types.Tool(function_declarations=declarations)]

response = genai_client.models.generate_content(
    model="gemini-2.0-flash-001",
    contents=contents,
    config=types.GenerateContentConfig(tools=gemini_tools),
)
```

#### Anthropic example

```python
from mcp_toolkit.converters import mcp_to_anthropic

tools = mcp_to_anthropic(mcp_tools)
response = anthropic_client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    tools=tools,
    messages=messages,
)
```

#### `clean_schema()` — why it exists

Pydantic and many JSON schema generators add a `"title"` field to every property (e.g., `"title": "City"`). Several LLM provider APIs reject schemas that include `title` keys. `clean_schema()` removes them recursively:

```python
from mcp_toolkit.converters import clean_schema

raw = {
    "title": "SearchInput",
    "type": "object",
    "properties": {
        "query": {"title": "Query", "type": "string", "description": "Search query"}
    }
}

cleaned = clean_schema(raw)
# {"type": "object", "properties": {"query": {"type": "string", "description": "Search query"}}}
```

Note: `clean_schema()` does **not** modify the input — it returns a new dict.

---

### `mcp_toolkit.config`

Loads and validates MCP server configuration. Use this when you need to manage server definitions in code or a JSON file, or when building on top of `MultiServerClient` directly.

#### Loading from a JSON file

```python
from mcp_toolkit.config import load_config

# Explicit path
config = load_config("mcp_servers.json")

# Auto-resolution order (no path given):
# 1. $MCP_CONFIG environment variable
# 2. mcp_servers.json in the current directory
# 3. config.json in the current directory
config = load_config()
```

#### Loading from a dict

```python
from mcp_toolkit.config import load_config_from_dict

config = load_config_from_dict({
    "mcpServers": {
        "weather": {"command": "python", "args": ["weather_server.py"]},
        "search":  {"url": "http://localhost:9000/sse"},
    }
})
```

#### `MCPServerConfig` — programmatic server definition

```python
from mcp_toolkit.config import MCPServerConfig

# Stdio server (local subprocess)
stdio_server = MCPServerConfig(
    name="weather",
    command="python",
    args=["servers/weather_server.py"],
    env={"OPENWEATHER_API_KEY": "abc123"},  # passed to the subprocess
)
print(stdio_server.transport)  # "stdio"

# SSE server (HTTP)
sse_server = MCPServerConfig(
    name="my-api",
    url="http://localhost:8000/sse",
)
print(sse_server.transport)  # "sse" (auto-detected from url)

# Streamable HTTP (modern hosted MCP services)
remote_server = MCPServerConfig(
    name="tavily",
    url="https://mcp.tavily.com/mcp/?tavilyApiKey=xyz",
    transport_type="streamable_http",  # must be explicit for streamable_http
)
print(remote_server.transport)  # "streamable_http"
```

**Transport auto-detection rules:**
- `transport_type` set → uses that value exactly
- `url` provided, no `transport_type` → `"sse"`
- `command` provided, no `url` → `"stdio"`

#### `${VAR}` placeholder resolution

Any `${ENV_VAR_NAME}` in `url` or `env` values is automatically resolved from the environment when `load_config()` or `load_config_from_dict()` is called:

```json
{
  "mcpServers": {
    "search": {
      "url": "https://mcp.example.com/?key=${SEARCH_API_KEY}",
      "transport": "streamable_http"
    },
    "myserver": {
      "command": "python",
      "args": ["server.py"],
      "env": { "DB_URL": "${DATABASE_URL}" }
    }
  }
}
```

Unset variables resolve to an empty string — your server code should validate required keys on startup (see `get_env_or_raise()` below).

---

### `mcp_toolkit.transports`

Low-level connection layer. Use this when you need direct access to the raw MCP `ClientSession` — for example, to call `session.list_tools()` or `session.call_tool()` without a full LLM client wrapper.

```python
from mcp_toolkit import connect

# stdio — local script (interpreter auto-detected from extension)
async with connect(script="my_server.py") as session:
    # session is a fully-initialized mcp.ClientSession
    response = await session.list_tools()
    for tool in response.tools:
        print(f"{tool.name}: {tool.description}")

    result = await session.call_tool("get_weather", {"city": "Paris"})
    print(result.content[0].text)

# SSE
async with connect(url="http://localhost:8000/sse") as session:
    ...

# Streamable HTTP (from config object)
from mcp_toolkit.config import MCPServerConfig
cfg = MCPServerConfig(name="t", url="https://api.example.com/mcp", transport_type="streamable_http")
async with connect(config=cfg) as session:
    ...

# Explicit command + args
async with connect(command="node", args=["server.js"]) as session:
    ...
```

The `connect()` function handles MCP session initialization (`session.initialize()`) before yielding, so the session is always ready to use inside the `async with` block.

---

### `mcp_toolkit.server`

Utility helpers for building your MCP servers. These solve common boilerplate problems.

```python
from mcp_toolkit.server import load_env, openai_helper, get_env_or_raise
```

#### `load_env()` — find your `.env` file automatically

When an MCP server is launched as a subprocess, its working directory might be different from where your `.env` file lives. `load_env()` solves this by walking up the directory tree until it finds a `.env` file:

```python
# my_server.py
from mcp_toolkit.server import load_env

load_env()  # finds .env anywhere up the directory tree — no path math needed
```

This replaces the common brittle pattern:
```python
# The old way — breaks if you move the file
load_dotenv(Path(__file__).parent.parent.parent / ".env")
```

#### `get_env_or_raise()` — required environment variables

```python
from mcp_toolkit.server import get_env_or_raise

# Raises ValueError with a clear message if not set
api_key = get_env_or_raise("OPENWEATHER_API_KEY")
db_url   = get_env_or_raise("DATABASE_URL", "Add DATABASE_URL to your .env file")
```

#### `openai_helper()` — quick AI calls inside tool implementations

When your MCP tool needs to call OpenAI for processing (summarization, extraction, classification), use this helper instead of repeating the client setup:

```python
from mcp_toolkit.server import openai_helper

@mcp.tool()
def summarize_document(text: str) -> str:
    """Summarize a document using AI."""
    return openai_helper(
        f"Summarize this in 3 bullet points:\n\n{text}",
        system="You are a concise summarizer.",
        model="gpt-4o-mini",
        max_tokens=200,
    )
```

> **Why only an OpenAI helper and not Gemini/Anthropic?**
>
> OpenAI's Python SDK provides a **synchronous** client (`openai.OpenAI`) — no `await` needed — making it safe to call from a plain `def` function.
>
> Gemini and Anthropic are **async-only** — they require `await`. Calling `asyncio.run()` inside an already-running async MCP server crashes with `RuntimeError: This event loop is already running`.
>
> For those providers, use their async clients directly inside an `async def` tool:
>
> ```python
> from anthropic import AsyncAnthropic
>
> _client = AsyncAnthropic()
>
> @mcp.tool()
> async def summarize_with_claude(text: str) -> str:
>     """Summarize using Claude."""
>     response = await _client.messages.create(
>         model="claude-sonnet-4-20250514",
>         max_tokens=200,
>         messages=[{"role": "user", "content": f"Summarize: {text}"}],
>     )
>     return response.content[0].text
> ```

---

## Building an MCP Server

The toolkit works with **any** MCP server. Here's a complete example of a server that uses several toolkit helpers:

```python
# product_server.py
import httpx
from mcp.server.fastmcp import FastMCP
from mcp_toolkit.server import load_env, get_env_or_raise, openai_helper

# Load .env from project root (wherever the server is run from)
load_env()

mcp = FastMCP("product-tools")


@mcp.tool()
async def search_products(query: str, max_results: int = 5) -> str:
    """Search the product catalog.

    Args:
        query: Search query string.
        max_results: Maximum number of results to return (default 5).
    """
    api_key = get_env_or_raise("CATALOG_API_KEY")
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://api.mystore.com/search",
            params={"q": query, "limit": max_results},
            headers={"Authorization": f"Bearer {api_key}"},
        )
        data = resp.json()

    lines = [f"- {p['name']} (${p['price']}): {p['sku']}" for p in data["products"]]
    return "\n".join(lines) if lines else "No products found."


@mcp.tool()
def summarize_product_reviews(product_id: str, reviews: str) -> str:
    """Summarize customer reviews for a product.

    Args:
        product_id: The product SKU or ID.
        reviews: Raw review text to summarize.
    """
    return openai_helper(
        f"Summarize these customer reviews for product {product_id}:\n\n{reviews}",
        system="You are a product analyst. Summarize reviews in 2-3 sentences covering sentiment, key positives, and key negatives.",
        max_tokens=150,
    )


if __name__ == "__main__":
    mcp.run()
```

Connect with any toolkit client:

```python
async with OpenAIMCPClient(server_script="product_server.py") as client:
    print(await client.chat("Find me a laptop under $800 and summarize its reviews"))
```

---

## Configuration Reference

### Required environment variables

| Variable | Provider / Component |
|----------|----------------------|
| `OPENAI_API_KEY` | `OpenAIMCPClient`, `MultiServerClient`, `LangChainMCPClient`, `BaseAgent`, `openai_helper()` |
| `GEMINI_API_KEY` | `GeminiMCPClient` |
| `ANTHROPIC_API_KEY` | `AnthropicMCPClient` |
| `MCP_CONFIG` | `load_config()` — alternative to passing a file path |

### Client constructor parameters

All single-server clients share these parameters (pass as keyword args):

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `server_script` | `str` | — | Path to a `.py`/`.js`/`.ts` server file (stdio) |
| `server_url` | `str` | — | HTTP endpoint URL (SSE transport) |
| `server_config` | `MCPServerConfig` | — | Pre-built config object |
| `command` | `str` | auto-detected | Override the interpreter command |
| `args` | `list[str]` | auto-detected | Override the command arguments |
| `system_prompt` | `str` | `"You are a helpful assistant..."` | LLM system prompt |
| `model` | `str` | provider default | Model name |
| `temperature` | `float` | `0` | Sampling temperature |
| `api_key` | `str` | from env var | API key override |

Provider defaults:

| Client | Default model |
|--------|--------------|
| `OpenAIMCPClient` | `gpt-4o-mini` |
| `GeminiMCPClient` | `gemini-2.0-flash-001` |
| `AnthropicMCPClient` | `claude-sonnet-4-20250514` |
| `LangChainMCPClient` | `gpt-4o-mini` |
| `MultiServerClient` | `gpt-4o-mini` |

### `MCPServerConfig` fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Human-readable server name |
| `command` | `str` | Command to run the server (`"python"`, `"node"`, `"uv"`) |
| `args` | `list[str]` | Arguments to the command |
| `env` | `dict[str, str]` | Environment variables for the subprocess |
| `url` | `str` | HTTP endpoint for SSE or streamable_http |
| `transport_type` | `str` | Explicit transport: `"stdio"`, `"sse"`, `"streamable_http"` |

### `BaseAgent` class attributes

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `server_names` | `list[str]` | `[]` | MCP server names whose tools this agent can use. Empty = all tools. |
| `system_prompt` | `str` | `"You are a helpful assistant..."` | System prompt for the LLM |
| `max_tool_rounds` | `int` | `10` | Max tool-calling iterations before forcing a final answer |

---

## Examples

### Quickstarts (no server required)

All quickstarts default to the bundled `demo_server.py` — run them with just an API key set:

```bash
cd mcp-toolkit
pip install -e ".[all]"

# Run with demo server (just set your API key)
python examples/quickstarts/quickstart_openai.py
python examples/quickstarts/quickstart_gemini.py
python examples/quickstarts/quickstart_anthropic.py
python examples/quickstarts/quickstart_langchain.py

# Or point at your own server
python examples/quickstarts/quickstart_openai.py path/to/your_server.py

# Multi-server (needs mcp_servers.json in current directory)
python examples/quickstarts/quickstart_multi.py

# BaseAgent parallel pattern (needs mcp_servers.json)
python examples/quickstarts/quickstart_agents.py

# Low-level connect() demo
python examples/quickstarts/direct_transport.py
```

### VoyageAI — full multi-agent showcase

`examples/voyageai/` is a complete FastAPI web application that demonstrates the multi-agent pattern at production scale:

- **4 specialist agents** — Weather, Flights, Hotels, Currency — each owning tools from their server
- **Parallel execution** — all agents run simultaneously with `asyncio.gather()`
- **Orchestrator** — parses user intent, dispatches to agents, synthesizes results
- **React frontend** — built with Vite + React
- **SQLite session store** — conversation history across page reloads

```bash
cd mcp-toolkit/examples/voyageai
cp .env.example .env       # fill in your API keys
pip install -e "../../.[all]"
pip install fastapi uvicorn

# Development (hot-reload backend + frontend)
uvicorn app.main:app --reload        # Terminal 1
cd frontend && npm install && npm run dev  # Terminal 2

# Production (single server)
cd frontend && npm run build
cd .. && uvicorn app.main:app
```

See [`examples/voyageai/README.md`](examples/voyageai/README.md) for the full setup guide.

---

## Project Structure

```
mcp-toolkit/
├── pyproject.toml                    # Package config and optional extras
├── README.md
│
├── src/mcp_toolkit/
│   ├── __init__.py                   # Top-level public API re-exports
│   │
│   ├── converters.py                 # mcp_to_openai_completions()
│   │                                 # mcp_to_openai_responses()
│   │                                 # mcp_to_gemini(), mcp_to_anthropic()
│   │                                 # clean_schema()
│   │
│   ├── config.py                     # load_config(), load_config_from_dict()
│   │                                 # MCPServerConfig, MCPConfig
│   │                                 # ${VAR} placeholder resolution
│   │
│   ├── transports.py                 # connect() — stdio / SSE / streamable_http
│   │
│   ├── clients/
│   │   ├── base.py                   # BaseMCPClient — connection lifecycle, call_tool()
│   │   ├── openai.py                 # OpenAIMCPClient
│   │   ├── gemini.py                 # GeminiMCPClient
│   │   ├── anthropic.py              # AnthropicMCPClient
│   │   ├── langchain.py              # LangChainMCPClient
│   │   └── multi.py                  # MultiServerClient
│   │
│   ├── agents/
│   │   └── base.py                   # BaseAgent — subclass with server_names
│   │                                 # + system_prompt for a ready-made agent
│   │
│   └── server/
│       └── helpers.py                # load_env(), openai_helper(), get_env_or_raise()
│
├── examples/
│   ├── quickstarts/
│   │   ├── demo_server.py            # Zero-config demo server (echo, add, greet)
│   │   ├── quickstart_openai.py
│   │   ├── quickstart_gemini.py
│   │   ├── quickstart_anthropic.py
│   │   ├── quickstart_langchain.py
│   │   ├── quickstart_multi.py
│   │   ├── quickstart_agents.py
│   │   └── direct_transport.py
│   └── voyageai/                     # Full multi-agent travel planner app
│
└── tests/
    ├── test_config.py
    ├── test_converters.py
    └── test_transports.py
```

---

## Running Tests

```bash
cd mcp-toolkit
pip install -e ".[dev]"

# Run all tests
pytest

# Verbose output
pytest -v

# Specific module
pytest tests/test_converters.py -v
pytest tests/test_config.py -v
```

---

## License

MIT — see [LICENSE](../LICENSE) for details.
