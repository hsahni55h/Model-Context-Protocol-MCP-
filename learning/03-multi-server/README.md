# 03 - Multi-Server MCP Client

Connect to **multiple MCP servers simultaneously** from a single LangChain agent. The agent sees tools from all servers and decides which to use based on the query.

## What's in this folder

| File | Purpose |
|---|---|
| `client.py` | **Config-driven** multi-server client. Reads servers from `config.json`, connects to all of them, aggregates tools into one agent. |
| `client_single.py` | **Single-server** client (same pattern as `02-langchain-adapters`). Takes a server script as CLI argument. Useful for quick testing. |
| `math_server.py` | A simple math MCP server (add, multiply, divide) used as the second server for the demo. |
| `config.json` | Defines which MCP servers to connect to (command + args for each). |

## How it works

```
config.json
  |
  +-- terminal server  -->  run_command tool
  |
  +-- math server      -->  add, multiply, divide tools
  |
  v
client.py  -->  LangChain agent with ALL tools
```

1. `client.py` reads `config.json` to discover servers
2. Connects to each server via stdio and loads its tools
3. Merges all tools into a single LangChain agent
4. The LLM decides which server's tool to call based on your query

## Prerequisites

```bash
# From the repo root
uv sync --extra langchain
```

## Running

### Option A: Multi-server client (recommended)

```bash
# From the repo root
uv run python learning/03-multi-server/client.py
```

This connects to both servers defined in `config.json`:
- **terminal** - our terminal server from `01-mcp-basics` (provides `run_command`)
- **math** - a simple math server in this folder (provides `add`, `multiply`, `divide`)

### Option B: Single-server client

```bash
# From the repo root
uv run python learning/03-multi-server/client_single.py learning/01-mcp-basics/server/main.py
```

## Example session (multi-server)

```
Connecting to MCP Server: terminal...
  Loaded tool: run_command
  1 tools loaded from terminal.

Connecting to MCP Server: math...
  Loaded tool: add
  Loaded tool: multiply
  Loaded tool: divide
  3 tools loaded from math.

MCP Client Ready! Type 'quit' to exit.

Query: List files in the workspace
[calls run_command from terminal server]
Response: The workspace contains: mcp_client_test.txt

Query: What is 42 * 17?
[calls multiply from math server]
Response: 42 * 17 = 714.0

Query: quit
```

## Customizing config.json

Add any MCP server by specifying its `command` and `args`:

```json
{
  "mcpServers": {
    "my_server": {
      "command": "uv",
      "args": ["run", "python", "path/to/server.py"]
    },
    "docker_server": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "--init", "my_image"]
    },
    "npx_server": {
      "command": "npx",
      "args": ["-y", "@some/mcp-server"]
    }
  }
}
```

## Key concept: why multi-server matters

In real-world MCP setups, each server exposes a focused set of tools (file ops, database, API, etc.). A multi-server client lets one agent use tools from all of them — the LLM picks the right server's tool automatically. This is how Cursor, Claude Desktop, and other MCP hosts work internally.
