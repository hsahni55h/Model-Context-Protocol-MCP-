# 05 — SSE Transport

This module teaches **SSE (Server-Sent Events)** as an alternative MCP transport to stdio. Same weather tools, completely different communication model — the server runs as a persistent HTTP service instead of a subprocess.

---

## What is SSE?

**SSE (Server-Sent Events)** is a web standard that allows a server to push real-time updates to a client over a single, long-lived HTTP connection.

```
┌──────────┐         HTTP GET /sse          ┌──────────┐
│  Client  │ ──────────────────────────────► │  Server  │
│          │ ◄─────────────────────────────  │          │
│          │    (persistent SSE stream)      │          │
│          │                                 │          │
│          │       HTTP POST /messages/      │          │
│          │ ──────────────────────────────► │          │
└──────────┘                                 └──────────┘
```

- Client opens a **GET /sse** connection — server holds it open and pushes events (responses)
- Client sends requests via **POST /messages/** — server processes them and responds on the SSE stream
- The connection stays open until the client disconnects

---

## SSE vs Stdio — When to use which?

| | **Stdio** (Modules 01-04) | **SSE** (This module) |
|---|---|---|
| **How it works** | Client spawns server as subprocess, communicates via stdin/stdout | Server runs as HTTP service, client connects over the network |
| **Connection** | One client per server process | Multiple clients can connect simultaneously |
| **Network** | Local only (same machine) | Works across the network (local, Docker, cloud) |
| **Lifecycle** | Server starts/stops with the client | Server runs independently, clients come and go |
| **Startup** | New process per connection (slow) | Server always running (fast) |
| **Use case** | Dev tools (Cursor, Claude Desktop), single-user CLI | Production services, multi-user, remote access |
| **Complexity** | Simpler — no HTTP server needed | Needs HTTP server (uvicorn), but more flexible |

### When to use stdio
- Local development tools (IDE integrations)
- Single-user CLI applications
- Quick prototyping and testing
- When you don't need network access

### When to use SSE
- Server runs on a different machine (or container)
- Multiple clients need to connect
- Production deployments behind a load balancer
- When you want the server to persist across client sessions

---

## How MCP works over SSE

In **stdio** (modules 01-04), the flow is:

```
Client starts server subprocess → communicates via stdin/stdout → server dies when client disconnects
```

In **SSE**, the flow is:

```
Server starts independently (uvicorn) → client connects via HTTP → server stays running
```

Under the hood, it's the same MCP protocol (JSON-RPC messages), just carried over HTTP instead of pipes:

```
┌────────────────────┐                              ┌────────────────────────┐
│    client.py       │                              │     server.py          │
│    (OpenAI +       │     HTTP (SSE transport)     │     (FastMCP +         │
│     MCP SDK)       │ ◄──────────────────────────► │      uvicorn)          │
│                    │                              │                        │
│  sse_client(url)   │  GET /sse (open stream)      │  mcp.run("sse")        │
│  session.call_tool │  POST /messages/ (requests)  │  @mcp.tool()           │
│                    │  SSE events (responses)      │  @mcp.resource()       │
└────────────────────┘                              └────────────────────────┘
                                                           │
                                                           ▼
                                                    ┌──────────────┐
                                                    │   wttr.in    │
                                                    │   (weather)  │
                                                    └──────────────┘
```

### The code difference is minimal

**Server — stdio (01-basics):**
```python
mcp = FastMCP("weather")
# ... define tools ...
mcp.run(transport="stdio")       # ← communicates via stdin/stdout
```

**Server — SSE (this module):**
```python
mcp = FastMCP("weather-sse", host="0.0.0.0", port=8000)
# ... same tools ...
mcp.run(transport="sse")         # ← starts HTTP server on port 8000
```

**Client — stdio (01-basics):**
```python
from mcp.client.stdio import stdio_client
params = StdioServerParameters(command="uv", args=["run", "python", "server.py"])
async with stdio_client(params) as (read, write):  # spawns subprocess
    ...
```

**Client — SSE (this module):**
```python
from mcp.client.sse import sse_client
async with sse_client(url="http://localhost:8000/sse") as (read, write):  # connects over HTTP
    ...
```

The `ClientSession` API is identical — `call_tool()`, `list_tools()`, `read_resource()` all work the same way.

---

## Files

| File | Role | Description |
|---|---|---|
| `server.py` | **MCP Server** | Weather tools served over SSE (uvicorn HTTP server) |
| `client.py` | **MCP Client** | Connects to SSE server, uses OpenAI for tool-calling |
| `Dockerfile` | **Container** | Runs the SSE server in Docker (network-accessible) |

---

## Setup

```bash
# Install dependencies (from repo root)
uv sync --extra sse

# Required env vars in .env (for the client only — server needs no API keys)
OPENAI_API_KEY=sk-...
```

---

## Running

### Step 1: Start the SSE server

```bash
# Terminal 1 (from repo root)
uv run python learning/05-sse-transport/server.py
```

You should see:
```
Starting weather SSE server on http://0.0.0.0:8000/sse
INFO:     Uvicorn running on http://0.0.0.0:8000
```

The server stays running — it doesn't exit. Leave this terminal open.

### Step 2: Connect the client

```bash
# Terminal 2 (from repo root)
uv run python learning/05-sse-transport/client.py http://localhost:8000/sse
```

You should see:
```
Connected to SSE server at http://localhost:8000/sse
Available tools: ['check_weather', 'get_forecast']

MCP SSE Client Started! Type 'quit' to exit.

Query: What's the weather in Tokyo?

[Calling tool: check_weather({"city": "Tokyo"})]

The current weather in Tokyo is 29°C with clouds and a 15 km/h wind.
```

### Step 3 (optional): Test with MCP Inspector

You can also test the SSE server with the MCP Inspector:

```bash
# In a browser, go to the Inspector and enter the SSE URL:
# Transport: SSE
# URL: http://localhost:8000/sse
```

---

## Running with Docker

Docker is the most common way to deploy SSE servers — the server runs in a container, accessible over the network.

### Build and run

```bash
# Build the image (from the 05-sse-transport directory)
cd learning/05-sse-transport
docker build -t mcp-weather-sse .

# Run the container
docker run -p 8000:8000 mcp-weather-sse
```

### Connect to the containerized server

```bash
# From repo root — same client command, same URL
uv run python learning/05-sse-transport/client.py http://localhost:8000/sse
```

The client doesn't know (or care) whether the server is running locally or in Docker — it just connects to the URL.

---

## Key differences from 01-basics

| Aspect | 01-basics (stdio) | 05-sse-transport (SSE) |
|---|---|---|
| Server start | `mcp.run(transport="stdio")` | `mcp.run(transport="sse")` |
| Client import | `from mcp.client.stdio import stdio_client` | `from mcp.client.sse import sse_client` |
| Client connect | `stdio_client(StdioServerParameters(...))` | `sse_client(url="http://...")` |
| Server lifecycle | Dies when client disconnects | Runs independently |
| Docker | Not useful (subprocess is local) | Natural fit (server as container) |
| Network | Same machine only | Any machine on the network |

Everything else is identical — the tools, the `ClientSession` API, the OpenAI integration, the tool-calling loop.

---

## Key takeaways

- **SSE is just a transport** — swap one line (`transport="sse"`) and your server is network-accessible
- **Same protocol** — MCP uses JSON-RPC regardless of transport. Tools, resources, and the client API are identical
- **Server independence** — SSE servers run as persistent services, independent of client lifecycle
- **Docker-friendly** — SSE servers are natural container workloads (expose a port, connect from anywhere)
- **No API keys on the server** — the weather tools use the free wttr.in API. Only the client needs `OPENAI_API_KEY`
