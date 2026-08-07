# ✈️ VoyageAI — Multi-Agent Travel Planner

VoyageAI is a full-stack, multi-agent travel planning application built on top of [mcp-toolkit](../../README.md). It demonstrates how to connect multiple MCP servers with different transport types, run specialist AI agents in parallel, and synthesize their results into a coherent response — all wired together with a React frontend and a FastAPI backend.

It is a real-world showcase of the [Model Context Protocol (MCP)](https://modelcontextprotocol.io) — not a toy example.

---

## Table of Contents

- [What It Does](#what-it-does)
- [Architecture](#architecture)
- [How It Uses mcp-toolkit](#how-it-uses-mcp-toolkit)
- [Project Structure](#project-structure)
- [MCP Servers](#mcp-servers)
- [Specialist Agents](#specialist-agents)
- [API Keys](#api-keys)
- [Setup & Installation](#setup--installation)
- [Running the App](#running-the-app)
- [Testing Agents Individually](#testing-agents-individually)
- [Checking API Keys](#checking-api-keys)
- [API Endpoints](#api-endpoints)
- [Session Persistence](#session-persistence)
- [Docker](#docker)
- [Known Limitations](#known-limitations)

---

## What It Does

You type a travel query — *"Plan a 5-day trip to Tokyo from London in October"* — and VoyageAI:

1. Sends your query to **four specialist agents simultaneously**
2. Each agent connects to its own MCP server, calls real external APIs, and returns a focused research summary
3. A **Planner LLM** reads all four summaries and synthesizes them into a structured travel plan with weather, flights, hotels, and budget information

There are two interaction modes:

- **Chat** — freeform conversation. All 4 agents always run in parallel.
- **Plan** — structured form input (destination, origin, dates, home currency). Only the relevant agents run based on what fields you filled in.

---

## Architecture

```
                    ┌─────────────────────────────────────────┐
                    │            TravelOrchestrator            │
                    │                                          │
  User query ──────►│  WeatherAgent  ──► weather MCP server   │
                    │  FlightAgent   ──► flights MCP server   │  asyncio.gather
                    │  HotelAgent    ──► Tavily MCP server    │  (all parallel)
                    │  CurrencyAgent ──► currency MCP server  │
                    │                                          │
                    │  Planner LLM ◄── all agent results      │
                    └─────────────────────────────────────────┘
                                        │
                               Final travel plan
```

**Key design decision:** All four agents always run in parallel for `chat()` requests. Each agent's `system_prompt` focuses it on its domain — no LLM pre-processing or intent detection step is needed. This keeps latency low (parallel > sequential) and the code simple.

For `plan()` requests, agents are selected deterministically based on which form fields the user filled in — no LLM involvement in routing at all.

---

## How It Uses mcp-toolkit

VoyageAI is built entirely on [mcp-toolkit](../../README.md). Here is exactly which parts of the toolkit it uses and why:

### `MultiServerClient` — connecting to 4 servers at once

```python
from mcp_toolkit.clients.multi import MultiServerClient
from app.config import OPENAI_API_KEY, get_mcp_config

config = get_mcp_config()   # loads mcp_servers.json, resolves ${VAR} placeholders
client = MultiServerClient(config, api_key=OPENAI_API_KEY)

async with client as mcp:
    print(mcp.server_names)  # ['weather', 'flights', 'currency', 'tavily']
    print(mcp.tool_names)    # all tools from all 4 servers combined
```

`MultiServerClient` connects to all servers in the config file concurrently, aggregates their tool lists, and routes `call_tool()` to the right server automatically.

### `BaseAgent` — the shared tool-calling loop

```python
from mcp_toolkit.agents import BaseAgent

class WeatherAgent(BaseAgent):
    server_names = ["weather"]   # only sees tools from the 'weather' server
    system_prompt = "You are a weather research specialist..."
```

`BaseAgent` handles the entire OpenAI tool-calling loop: sends the query, processes tool calls, executes them via MCP, feeds results back to the LLM, and repeats until the model stops calling tools. Subclasses only need to declare `server_names` and `system_prompt`.

### `mcp_to_openai_completions()` — tool schema conversion

MCP tools use a different schema format than the OpenAI Chat Completions API. `mcp_to_openai_completions()` converts between them, stripping unsupported fields cleanly. `BaseAgent` calls this internally — shown here for clarity:

```python
from mcp_toolkit.converters import mcp_to_openai_completions

tools = mcp_to_openai_completions(mcp.get_tools_by_server("weather"))
# Returns [{"type": "function", "function": {...}}, ...]
# ready to pass to openai.chat.completions.create(tools=...)
```

### `load_config()` — typed config with `${VAR}` resolution

```python
from mcp_toolkit.config import load_config

config = load_config("app/mcp_servers.json")
# ${OPENWEATHER_API_KEY} in the JSON is automatically replaced
# with the actual env var value before the config is used
```

### Transport auto-detection

`mcp_servers.json` has two transport types and the toolkit handles both transparently:

```json
{
  "weather": {
    "command": "python",
    "args": ["servers/weather_server.py"],
    "env": { "OPENWEATHER_API_KEY": "${OPENWEATHER_API_KEY}" }
  },
  "tavily": {
    "url": "https://mcp.tavily.com/mcp/?tavilyApiKey=${TAVILY_API_KEY}",
    "transport": "streamable_http"
  }
}
```

- `weather`, `flights`, `currency` → **stdio** transport: spawns a Python subprocess per server
- `tavily` → **streamable_http** transport: connects to Tavily's hosted MCP endpoint over HTTP

---

## Project Structure

```
voyageai/
├── servers/                        # Custom MCP servers (stdio transport)
│   ├── weather_server.py           # OpenWeather API — current weather + forecast
│   ├── flight_server.py            # AviationStack API — live flights + airports
│   └── currency_server.py          # ExchangeRate API — rates + conversion
│
├── app/
│   ├── main.py                     # FastAPI app, lifespan, all HTTP endpoints
│   ├── config.py                   # Env loading, MCP config resolution, validation
│   ├── state.py                    # SQLite session store (conversation history)
│   ├── mcp_servers.json            # MCP server definitions (4 servers)
│   └── agents/
│       ├── base.py                 # VoyageAI BaseAgent (wraps mcp_toolkit BaseAgent)
│       ├── orchestrator.py         # TravelOrchestrator — parallel agents + synthesis
│       ├── weather.py              # WeatherAgent
│       ├── flight.py               # FlightAgent
│       ├── hotel.py                # HotelAgent (uses Tavily for web search)
│       └── currency.py             # CurrencyAgent
│
├── frontend/                       # React + Vite UI
│   ├── src/
│   │   ├── App.jsx                 # Root component
│   │   └── components/             # ChatWindow, Sidebar, AgentCard, etc.
│   ├── package.json
│   └── vite.config.js              # Dev proxy: /chat /plan /sessions → :8000
│
├── data/                           # SQLite database (auto-created at runtime)
│   └── sessions.db
│
├── check_apis.py                   # Verify all API keys work before running
├── test_agent.py                   # Test any single agent from the terminal
│
├── .env.example                    # Template — copy to .env and fill in keys
├── pyproject.toml                  # Python package definition
│
├── Dockerfile                      # Production container build
├── docker-compose.yml              # Local container with volume for data/
└── render.yaml                     # Render.com deploy configuration
```

---

## MCP Servers

### `weather_server.py` — OpenWeather API

**Transport:** stdio (subprocess)

| Tool | Parameters | Description |
|------|-----------|-------------|
| `get_current_weather` | `city`, `country_code` (opt) | Current temperature, conditions, humidity, wind |
| `get_forecast` | `city`, `days` (1–5), `country_code` (opt) | Day-by-day forecast grouped from 3-hour API intervals |

Uses `httpx` to call the OpenWeather REST API. Returns plain text formatted for the LLM. New API keys take up to 2 hours to activate — see [Known Limitations](#known-limitations).

---

### `flight_server.py` — AviationStack API

**Transport:** stdio (subprocess)  
**Important:** The free AviationStack tier only supports **HTTP** (not HTTPS). The server uses `http://api.aviationstack.com/v1` accordingly.

| Tool | Parameters | Description |
|------|-----------|-------------|
| `search_flights` | `departure_iata`, `arrival_iata` | Live flights between two airports (up to 5 results) |
| `get_airport_info` | `iata_code` | Airport name, city, country, timezone |

The free tier provides 100 API calls/month. Some routes may return no results — this is a data availability limitation, not a bug.

---

### `currency_server.py` — ExchangeRate API

**Transport:** stdio (subprocess)

| Tool | Parameters | Description |
|------|-----------|-------------|
| `get_exchange_rate` | `from_currency`, `to_currency` | Current exchange rate between two currencies |
| `convert_currency` | `amount`, `from_currency`, `to_currency` | Convert a specific amount |

Uses ISO 4217 currency codes (USD, EUR, GBP, JPY, etc.).

---

### Tavily (remote server)

**Transport:** streamable_http (hosted by Tavily)  
**URL:** `https://mcp.tavily.com/mcp/?tavilyApiKey=<key>`  
**Tools:** `tavily_search`, `tavily_extract`, `tavily_crawl`, `tavily_map`, `tavily_research`

Used by `HotelAgent` for live web search — finding hotels, attractions, and local recommendations. No custom server needed; Tavily hosts their own MCP endpoint.

---

## Specialist Agents

All agents inherit from `app.agents.base.BaseAgent`, which is a thin wrapper around `mcp_toolkit.agents.BaseAgent` that injects the configured OpenAI model.

| Agent | Server | What it does |
|-------|--------|-------------|
| `WeatherAgent` | `weather` | Gets current conditions and multi-day forecast for the destination |
| `FlightAgent` | `flights` | Finds flight routes, airlines, times, and airport details |
| `HotelAgent` | `tavily` | Web-searches for top hotels, attractions, and restaurants |
| `CurrencyAgent` | `currency` | Gets exchange rates and converts budget amounts |

Each agent declares only two things — the toolkit handles the rest:

```python
class WeatherAgent(BaseAgent):
    server_names = ["weather"]      # only sees tools from this server
    system_prompt = "You are a weather research specialist for travel planning..."
```

The full tool-calling loop (send → receive tool call → execute via MCP → feed result back → repeat) is handled by `mcp_toolkit.agents.BaseAgent`.

---

## API Keys

You need **5 API keys** to run VoyageAI. All have free tiers that are sufficient for development and testing.

| Service | Env Variable | Free Tier | Sign Up |
|---------|-------------|-----------|---------|
| OpenAI | `OPENAI_API_KEY` | Pay-as-you-go (~$0.01–0.05 per query with gpt-4o-mini) | [platform.openai.com](https://platform.openai.com) |
| OpenWeather | `OPENWEATHER_API_KEY` | 1,000 calls/day | [openweathermap.org/api](https://openweathermap.org/api) |
| Tavily | `TAVILY_API_KEY` | 1,000 searches/month | [app.tavily.com/sign-up](https://app.tavily.com/sign-up) |
| AviationStack | `AVIATIONSTACK_API_KEY` | 100 calls/month | [aviationstack.com/signup/free](https://aviationstack.com/signup/free) |
| ExchangeRate-API | `EXCHANGE_RATE_API_KEY` | 1,500 calls/month | [exchangerate-api.com](https://www.exchangerate-api.com) |

**Important notes:**
- **OpenWeather keys take up to 2 hours to activate** after creation. You will get 401 errors immediately after signing up — wait and try again.
- **AviationStack free tier is HTTP only.** The `flight_server.py` already handles this correctly.
- The model defaults to `gpt-4o-mini`. Override with `OPENAI_MODEL=gpt-4o` in `.env` for better quality at higher cost.

---

## Setup & Installation

### Prerequisites

- Python 3.11+
- Node.js 18+ (only needed for the React dev server — not required for backend-only mode)

### 1. Install Python packages

From the repository root:

```bash
pip install -e ./mcp-toolkit
pip install -e ./mcp-toolkit/examples/voyageai
```

Or with `uv`:

```bash
uv pip install -e ./mcp-toolkit
uv pip install -e ./mcp-toolkit/examples/voyageai
```

### 2. Configure environment

```bash
cd mcp-toolkit/examples/voyageai
cp .env.example .env
```

Edit `.env` and fill in your API keys:

```env
OPENAI_API_KEY=sk-...
OPENWEATHER_API_KEY=...
TAVILY_API_KEY=tvly-...
AVIATIONSTACK_API_KEY=...
EXCHANGE_RATE_API_KEY=...

# Optional — defaults to gpt-4o-mini
OPENAI_MODEL=gpt-4o-mini
```

### 3. Verify all API keys

```bash
cd mcp-toolkit/examples/voyageai
python check_apis.py
```

This hits every external API directly (no LLM, no MCP) and shows raw results. Fix any failures before starting the app.

Expected output when everything is working:

```
=======================================================
  OpenWeather API  (weather agent)
=======================================================
  Key: 5d2fc714...
  ✓  London: 14.8°C, clear sky

=======================================================
  AviationStack API  (flights agent)
=======================================================
  Key: 192462ff...
  ✓  Connected — 1 flight(s) returned for LHR→JFK

=======================================================
  ExchangeRate API  (currency agent)
=======================================================
  Key: 08e5ae4b...
  ✓  100 USD = 86.73 EUR  (rate: 0.8673)

=======================================================
  Tavily API  (hotels agent)
=======================================================
  Key: tvly-dev...
  ✓  Connected — 1 result(s) returned
```

---

## Running the App

### Option 1 — Backend only (simplest)

Serves the full app at `http://127.0.0.1:8000`. The React UI is served as a pre-built static bundle — build it once first:

```bash
# Build the frontend (only needed once, or after frontend changes)
cd mcp-toolkit/examples/voyageai/frontend
npm install && npm run build

# Start the backend
cd ..
uvicorn app.main:app --reload
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000)

### Option 2 — Full dev mode with hot-reload

Use this when actively making changes to the frontend. The Vite dev server at `:5173` proxies all API calls to FastAPI at `:8000`:

```bash
# Terminal 1 — FastAPI backend
cd mcp-toolkit/examples/voyageai
uvicorn app.main:app --reload

# Terminal 2 — Vite dev server
cd mcp-toolkit/examples/voyageai/frontend
npm install && npm run dev
```

Open [http://localhost:5173](http://localhost:5173) — React components update instantly without a page reload.

### What you see at startup

When FastAPI starts, it prints the connected servers and available tools:

```
VoyageAI ready — connected to servers: ['weather', 'currency', 'flights', 'tavily']
Available tools: ['get_current_weather', 'get_forecast', 'get_exchange_rate',
                  'convert_currency', 'search_flights', 'get_airport_info',
                  'tavily_search', 'tavily_extract', ...]
```

If a server fails to connect, you will see the error here at startup rather than mid-request.

---

## Testing Agents Individually

`test_agent.py` lets you run any single agent from the terminal without starting the full app. This is the fastest way to diagnose a failing agent.

```bash
cd mcp-toolkit/examples/voyageai

# Test one agent at a time
python test_agent.py weather What is the weather in Tokyo
python test_agent.py flights Flights from London to New York
python test_agent.py hotels Best hotels in Barcelona
python test_agent.py currency Convert 500 USD to EUR

# Test all four agents in sequence with the same query
python test_agent.py all Plan a trip to Paris from London
```

**Quotes are not required** — the script joins all arguments after the agent name.

Each run connects **only** to the servers that specific agent needs — so testing `weather` does not require `TAVILY_API_KEY` or `AVIATIONSTACK_API_KEY`. A connection failure isolates exactly which server or key is the problem.

Example output:

```
Servers  : ['flights']
Tools    : ['search_flights', 'get_airport_info']
Query    : Flights from London to New York

============================================================
  FLIGHTS AGENT
============================================================
### Flight Summary from London (LHR) to New York (JFK)

1. British Airways BA177 — Scheduled, departs 13:20 UTC
2. Virgin Atlantic VS45  — Scheduled, departs 12:50 UTC
...
```

### Recommended debugging workflow

1. `python check_apis.py` — confirm all keys work at the raw HTTP level
2. `python test_agent.py <name> <query>` — confirm the full MCP + LLM loop works per agent
3. If step 1 passes but step 2 fails — the issue is in the MCP server subprocess or tool-calling logic
4. Start the full app only after all agents pass individually

---

## Checking API Keys

`check_apis.py` hits each external API directly — no LLM, no MCP subprocess — and reports whether the key is valid and returning data:

```bash
python check_apis.py
```

It tests:
- **OpenWeather** — queries current weather for London
- **AviationStack** — queries flights LHR→JFK via HTTP (per free tier requirement)
- **ExchangeRate-API** — converts 100 USD to EUR
- **Tavily** — searches "best hotels Barcelona" via the REST API

Each check shows the raw API response so you can see exactly what the server will receive when it makes tool calls.

---

## API Endpoints

### `POST /chat`

Freeform conversation. All four agents always run in parallel.

**Request body:**
```json
{
  "message": "Plan a trip to Tokyo from London",
  "session_id": ""
}
```

Leave `session_id` empty to start a new session. Pass the returned `session_id` in subsequent messages to maintain conversation history.

**Response:**
```json
{
  "response": "## ✈️ Your Tokyo Trip Plan\n\n...",
  "session_id": "abc123"
}
```

---

### `POST /plan`

Structured trip planner. Agents run only for the fields you provide.

**Request body:**
```json
{
  "destination": "Tokyo",
  "origin": "London",
  "departure_date": "2024-10-15",
  "return_date": "2024-10-22",
  "home_currency": "GBP",
  "session_id": ""
}
```

Only `destination` is required. Providing `origin` enables `FlightAgent`. Providing `home_currency` enables `CurrencyAgent`. `WeatherAgent` and `HotelAgent` always run.

**Response:**
```json
{
  "session_id": "abc123",
  "agents_called": ["weather", "hotels", "flights", "currency"],
  "results": {
    "weather": "Forecast for Tokyo...",
    "hotels": "Top hotels in Tokyo...",
    "flights": "Flights LHR → NRT...",
    "currency": "1 GBP = 187 JPY..."
  },
  "summary": "## ✈️ Trip Overview\n\n..."
}
```

---

### `GET /health`

Returns `200` if all MCP servers are connected, `503` otherwise. Use this to confirm the app started correctly.

```json
{
  "status": "ok",
  "servers": ["weather", "currency", "flights", "tavily"],
  "tools": ["get_current_weather", "get_forecast", "search_flights", "..."]
}
```

---

### Session endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET /sessions` | — | List all sessions with IDs and timestamps |
| `GET /sessions/{id}` | — | Full conversation history for a session |
| `DELETE /sessions/{id}` | — | Delete a session and its history |

---

## Session Persistence

Conversation history is stored in SQLite at `data/sessions.db`, created automatically on first run.

- Every user message and assistant response is saved after each `/chat` or `/plan` request
- History is passed to the Planner LLM on follow-up messages so context is maintained
- Individual specialist agents do **not** receive conversation history — only the final synthesis step does
- Sessions persist across server restarts

---

## Docker

Run the full app in a container without installing Python or Node locally:

```bash
cd mcp-toolkit/examples/voyageai

# Build and start (reads .env automatically)
docker compose up --build

# Run in background
docker compose up -d --build

# Stop
docker compose down
```

The `docker-compose.yml` mounts a named volume for `data/` so session history survives container restarts.

---

## Known Limitations

| Issue | Detail |
|-------|--------|
| **Weather key activation delay** | New OpenWeather keys take up to 2 hours to activate. If the weather agent hallucinates instead of calling the tool, run `check_apis.py` to confirm the key is live. |
| **AviationStack free tier** | 100 calls/month, HTTP only, limited live data. Some routes return empty results — data availability limitation, not a bug. |
| **All agents run on every chat** | `chat()` always runs all 4 agents in parallel regardless of query. Asking only about weather still triggers FlightAgent and CurrencyAgent. Use `/plan` for targeted queries. |
| **No streaming** | Responses are returned all at once after all 4 agents complete. No token-by-token streaming. |
| **SQLite only** | Session storage uses SQLite. Fine for local use; would need replacing for a multi-instance production deployment. |
