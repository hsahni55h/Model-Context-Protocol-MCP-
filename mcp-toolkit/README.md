# MCP Toolkit

**Plug-and-play utilities for building MCP clients and servers with any LLM provider.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

---

## What is this?

MCP Toolkit gives you **pre-built, configurable components** for the [Model Context Protocol](https://modelcontextprotocol.io/) — so you can connect any LLM to any MCP server in a few lines of code instead of writing boilerplate from scratch.

```python
from mcp_toolkit.clients import OpenAIMCPClient

async with OpenAIMCPClient(server_script="my_server.py") as client:
    response = await client.chat("What's the weather in Paris?")
    print(response)
```

That's it. The client handles connection, tool discovery, the full tool-calling loop, and cleanup.

---

## Installation

```bash
# Core (converters, config, transport abstraction)
pip install mcp-toolkit

# With your preferred LLM provider
pip install "mcp-toolkit[openai]"      # OpenAI
pip install "mcp-toolkit[gemini]"      # Google Gemini
pip install "mcp-toolkit[anthropic]"   # Anthropic Claude
pip install "mcp-toolkit[langchain]"   # LangChain agent

# Everything
pip install "mcp-toolkit[all]"
```

Or install from source:
```bash
cd mcp-toolkit
pip install -e ".[all,dev]"
```

---

## Quick Start

### 1. Single Server + OpenAI

```python
import asyncio
from mcp_toolkit.clients import OpenAIMCPClient

async def main():
    async with OpenAIMCPClient(server_script="weather_server.py") as client:
        print(await client.chat("Compare weather in London and Tokyo"))

asyncio.run(main())
```

### 2. Single Server + Gemini

```python
from mcp_toolkit.clients import GeminiMCPClient

async with GeminiMCPClient(server_script="weather_server.py") as client:
    print(await client.chat("What's the forecast for Sydney?"))
```

### 3. Single Server + Claude

```python
from mcp_toolkit.clients import AnthropicMCPClient

async with AnthropicMCPClient(server_script="weather_server.py") as client:
    print(await client.chat("Is it raining in Berlin?"))
```

### 4. Multiple Servers

```python
from mcp_toolkit.clients import MultiServerClient

# From a config file
async with MultiServerClient.from_config("mcp_servers.json") as client:
    # The model can call tools from ANY connected server
    print(await client.chat("What's 2+2 and what's the weather in NYC?"))
```

Config file format (`mcp_servers.json`):
```json
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
```

### 5. LangChain Agent

```python
from mcp_toolkit.clients import LangChainMCPClient

async with LangChainMCPClient(server_script="server.py") as client:
    print(await client.chat("Read the file and summarize it"))
```

### 6. Low-Level Transport Access

```python
from mcp_toolkit import connect

async with connect(script="server.py") as session:
    tools = await session.list_tools()
    result = await session.call_tool("check_weather", {"city": "Paris"})
```

---

## Modules

| Module | Purpose |
|--------|---------|
| `mcp_toolkit.clients` | Pre-built clients for OpenAI, Gemini, Claude, LangChain, Multi-server |
| `mcp_toolkit.converters` | Convert MCP tools to OpenAI/Gemini/Anthropic formats |
| `mcp_toolkit.config` | Load and validate server configurations |
| `mcp_toolkit.transports` | Unified `connect()` abstraction over stdio/SSE |
| `mcp_toolkit.server` | Helpers for building MCP servers (env loading, OpenAI helper) |

---

## API Reference

### Converters

```python
from mcp_toolkit.converters import mcp_to_openai, mcp_to_gemini, mcp_to_anthropic, clean_schema

# Convert MCP tools to provider-specific formats
openai_tools = mcp_to_openai(mcp_tools)
gemini_decls = mcp_to_gemini(mcp_tools)
claude_tools = mcp_to_anthropic(mcp_tools)

# Strip 'title' fields from schemas (many LLMs reject them)
cleaned = clean_schema(raw_schema)
```

### Configuration

```python
from mcp_toolkit.config import load_config, load_config_from_dict, MCPServerConfig

# From file (auto-detects mcp_servers.json, config.json, or $MCP_CONFIG)
config = load_config("path/to/config.json")

# From dict
config = load_config_from_dict({
    "mcpServers": {"my_server": {"command": "python", "args": ["server.py"]}}
})

# Programmatic
server = MCPServerConfig(name="weather", command="python", args=["weather.py"])
```

### Server Helpers

```python
from mcp_toolkit.server import openai_helper, load_env, get_env_or_raise

# Auto-find and load .env from any parent directory
load_env()

# Quick OpenAI call inside your tool implementations
summary = openai_helper("Summarize this text", system="You are a summarizer")

# Get env vars with helpful error messages
api_key = get_env_or_raise("MY_API_KEY")
```

---

## Configuration

### Environment Variables

| Variable | Used By | Required |
|----------|---------|----------|
| `OPENAI_API_KEY` | OpenAI client, Multi-server, LangChain, server helpers | For OpenAI-based features |
| `GEMINI_API_KEY` | Gemini client | For Gemini features |
| `ANTHROPIC_API_KEY` | Anthropic client | For Claude features |
| `MCP_CONFIG` | Config loader | Optional (alternative to file path) |

### Client Options

All clients accept:
- `server_script` — Path to a .py/.js MCP server file (stdio transport)
- `server_url` — SSE endpoint URL (SSE transport)  
- `system_prompt` — Custom system prompt for the LLM

Provider-specific options:
- `model` — Model name (each has sensible defaults)
- `temperature` — Sampling temperature (default: 0)
- `api_key` — API key override

---

## Building Your Own MCP Server

MCP Toolkit works with **any** MCP server. Here's a minimal example:

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("my-tools")

@mcp.tool()
def greet(name: str) -> str:
    """Greet someone by name."""
    return f"Hello, {name}!"

# Run with: python my_server.py
```

Then connect with any toolkit client:
```python
async with OpenAIMCPClient(server_script="my_server.py") as client:
    print(await client.chat("Greet Alice"))
    # → "Hello, Alice!"
```

---

## Project Structure

```
mcp-toolkit/
├── pyproject.toml              # Package configuration
├── src/mcp_toolkit/
│   ├── __init__.py             # Public API exports
│   ├── converters.py           # Tool format converters
│   ├── config.py               # Configuration loading
│   ├── transports.py           # Transport abstraction
│   ├── clients/
│   │   ├── base.py             # Shared client logic
│   │   ├── openai.py           # OpenAI client
│   │   ├── gemini.py           # Gemini client
│   │   ├── anthropic.py        # Claude client
│   │   ├── langchain.py        # LangChain agent client
│   │   └── multi.py            # Multi-server client
│   └── server/
│       └── helpers.py          # Server-side utilities
├── examples/                   # Usage examples
└── tests/                      # Test suite
```

---

## Development

```bash
# Install in dev mode
cd mcp-toolkit
pip install -e ".[all,dev]"

# Run tests
pytest

# Run a specific test
pytest tests/test_converters.py -v
```

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Make your changes
4. Run tests (`pytest`)
5. Commit and push
6. Open a Pull Request

---

## License

MIT — see [LICENSE](../LICENSE) for details.
