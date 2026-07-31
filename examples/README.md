# Examples

Practical MCP server examples — each demonstrates a different pattern for building tool servers. They progress from simple to complex, teaching one new concept at each step.

---

## Overview

| Example | Pattern | Tools | Client | Stack |
|---|---|---|---|---|
| [`weather/`](weather/) | Minimal multi-tool server | `check_weather`, `get_forecast`, `compare_weather` | MCP Inspector | wttr.in (free) |
| [`job-search/`](job-search/) | REST API integration + web UI | `analyze_resume`, `suggest_job_titles`, `fetch_linkedin_jobs` | Streamlit app | OpenAI, Apify |
| [`medical-tools/`](medical-tools/) | Multi-tool pipeline (chaining) | `extract_symptoms`, `diagnose_symptoms`, `search_pubmed`, `summarize_articles` | Streamlit app | OpenAI, PubMed (free) |

---

## How MCP works in these examples

Each example follows the same MCP architecture:

```
┌────────────────┐    stdio (JSON-RPC)    ┌───────────────┐      ┌─────────────┐
│  MCP Client    │ ◄────────────────────► │  MCP Server   │ ───► │ External API│
│  (Inspector /  │                        │  (server.py)  │      │ (wttr.in /  │
│   Streamlit /  │                        │               │      │  OpenAI /   │
│   Python code) │                        │  @mcp.tool()  │      │  PubMed)    │
└────────────────┘                        └───────────────┘      └─────────────┘
```

1. **Server** registers tools and resources using `FastMCP`
2. **Client** spawns the server as a subprocess and connects over stdio
3. Client calls `list_tools()` to discover available tools
4. Client sends `CallToolRequest` → server executes → returns result
5. Client can also `read_resource()` for static context data

The **server** is always a single Python file with `@mcp.tool()` decorated functions. The **client** can be anything: MCP Inspector, a Streamlit app, a LangChain agent, Claude Desktop, etc.

---

## Progression

Start with **weather** (simplest) and work up:

| # | Example | New concepts learned |
|---|---|---|
| 1 | **weather** | `FastMCP`, `@mcp.tool()`, `@mcp.resource()`, typed params, MCP Inspector |
| 2 | **job-search** | External API keys, `.env` handling, Streamlit as MCP client, JSON returns |
| 3 | **medical-tools** | Tool chaining, XML parsing, composable pipelines, multi-step orchestration |

---

## Running

Each example has its own detailed README. General pattern:

```bash
# 1. Install dependencies (from repo root)
uv sync --extra <group>

# 2a. Test with MCP Inspector
uv run mcp dev examples/<name>/server.py

# 2b. Or run the Streamlit app (job-search, medical-tools)
uv run streamlit run examples/<name>/app.py
```

### Quick start

```bash
# Weather (no setup needed)
uv sync
uv run mcp dev examples/weather/server.py

# Job search
uv sync --extra jobs
uv run streamlit run examples/job-search/app.py

# Medical tools
uv sync --extra clinisight
uv run streamlit run examples/medical-tools/app.py
```

---

## Required API keys

Add to your `.env` file at the repo root:

| Example | Keys needed | Free tier? |
|---|---|---|
| weather | None | Yes (no auth needed) |
| job-search | `OPENAI_API_KEY`, `APIFY_API_TOKEN` | OpenAI: pay-as-you-go, Apify: free tier |
| medical-tools | `OPENAI_API_KEY` | OpenAI: pay-as-you-go, PubMed: free |

---

## Server vs. Client — what's what?

| File | Role | Description |
|---|---|---|
| `server.py` | **MCP Server** | Registers tools/resources, handles JSON-RPC requests, calls external APIs |
| `app.py` | **MCP Client** | Streamlit UI that spawns the server, calls tools, orchestrates the pipeline |
| MCP Inspector | **MCP Client** | Built-in dev tool for testing tools manually (launched via `mcp dev`) |

**Key principle:** Servers expose **capabilities** (tools). Clients provide **orchestration** (deciding which tool to call, passing context between tools, presenting results to users).

---

## Common patterns

### Spawning a server from a client

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

params = StdioServerParameters(
    command="uv", args=["run", "python", "examples/<name>/server.py"],
    env={**os.environ}  # IMPORTANT: pass env vars to subprocess
)
async with stdio_client(params) as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()
        result = await session.call_tool("tool_name", {"arg": "value"})
```

### Robust .env loading (works from any cwd)

```python
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")
```

### Returning structured data from tools

```python
@mcp.tool()
def my_tool(query: str) -> str:
    # Return JSON string for structured data (not dict/list)
    return json.dumps({"results": [...], "count": 5})
```
