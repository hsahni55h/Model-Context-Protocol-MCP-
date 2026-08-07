# ✈️ VoyageAI — Multi-Agent Travel Planner

A showcase project demonstrating [mcp-toolkit](../../README.md) in a real-world application. VoyageAI is a multi-agent travel planner that uses MCP (Model Context Protocol) servers to gather weather, flights, hotels, and currency data — then synthesizes everything into a travel plan.

## Architecture

```
User query → WeatherAgent  ┐
           → FlightAgent   │ asyncio.gather (all 4 in parallel)
           → HotelAgent    │
           → CurrencyAgent ┘
           → Planner LLM synthesizes → final response
```

All four specialist agents run in parallel for every request. Each agent's `system_prompt` focuses it on its domain — no LLM pre-processing step needed.

### What it demonstrates

| Feature | How |
|---------|-----|
| **stdio transport** | Custom weather, currency, and flight MCP servers |
| **streamable_http transport** | Tavily remote MCP server for web search |
| **Multi-server connection** | `MultiServerClient` connects to 4 servers simultaneously |
| **Tool schema conversion** | `mcp_to_openai_completions()` converts MCP tools to OpenAI Chat format |
| **Parallel agent execution** | Specialized agents run concurrently via `asyncio.gather` |
| **Session persistence** | SQLite-backed conversation history |
| **Per-server tool filtering** | Each agent only sees tools from its MCP server |

### Components

```
voyageai/
├── servers/                    # MCP servers (stdio transport)
│   ├── weather_server.py       # OpenWeather API — current weather + forecast
│   ├── flight_server.py        # AviationStack API — flight search + airports
│   └── currency_server.py      # ExchangeRate API — rates + conversion
├── app/
│   ├── main.py                 # FastAPI app with lifespan management
│   ├── config.py               # Env loading + MCP config resolution
│   ├── state.py                # SQLite session store
│   ├── mcp_servers.json        # MCP server definitions (4 servers)
│   └── agents/
│       ├── base.py             # BaseAgent — shared tool-calling loop
│   ├── orchestrator.py     # Parallel agents → synthesis
│   ├── weather.py          # WeatherAgent (weather server)
│   ├── flight.py           # FlightAgent (flights server)
│   ├── hotel.py            # HotelAgent (Tavily — web search)
│   └── currency.py         # CurrencyAgent (currency server)
├── frontend/                   # React + Vite UI
│   ├── src/                    # React components
│   └── vite.config.js          # Proxies /chat, /plan, /sessions → FastAPI
├── check_apis.py               # Verify all API keys before running
├── test_agent.py               # Test any agent individually from terminal
├── Dockerfile                  # Container build
├── docker-compose.yml          # Docker Compose (local container)
└── render.yaml                 # Render.com deploy config
```

## Quick Start

### 1. Get API Keys

| API | Env Var | Free Tier | URL |
|-----|---------|-----------|-----|
| OpenAI | `OPENAI_API_KEY` | Pay-as-you-go | [platform.openai.com](https://platform.openai.com) |
| OpenWeather | `OPENWEATHER_API_KEY` | 1000 calls/day | [openweathermap.org/api](https://openweathermap.org/api) |
| Tavily | `TAVILY_API_KEY` | 1000 searches/month | [tavily.com](https://tavily.com) |
| AviationStack | `AVIATIONSTACK_API_KEY` | 100 calls/month | [aviationstack.com](https://aviationstack.com) |
| ExchangeRate-API | `EXCHANGE_RATE_API_KEY` | 1500 calls/month | [exchangerate-api.com](https://exchangerate-api.com) |

### 2. Set Up

```bash
cd mcp-toolkit/examples/voyageai

# Create .env from template
cp .env.example .env
# Edit .env and add your API keys

# Install dependencies (from repo root)
cd ../../..
pip install -e ./mcp-toolkit
pip install -e ./mcp-toolkit/examples/voyageai
```

### 3. Verify API keys

```bash
cd mcp-toolkit/examples/voyageai
python check_apis.py
```

This hits every external API directly and shows raw results — no LLM involved. Fix any failures before starting the app.

### 4. Run

**Backend only** (serves the built React bundle at `/`):
```bash
cd mcp-toolkit/examples/voyageai
uvicorn app.main:app --reload
```
Open [http://127.0.0.1:8000](http://127.0.0.1:8000)

**With hot-reload frontend** (recommended during development):
```bash
# Terminal 1 — FastAPI backend
cd mcp-toolkit/examples/voyageai
uvicorn app.main:app --reload

# Terminal 2 — Vite dev server (proxies API calls to FastAPI)
cd mcp-toolkit/examples/voyageai/frontend
npm install && npm run dev
```
Open [http://localhost:5173](http://localhost:5173) — changes to React components reload instantly.

**Build frontend for production** (bundles into `frontend/dist/`, served by FastAPI):
```bash
cd mcp-toolkit/examples/voyageai/frontend
npm run build
```

### Docker

```bash
cd mcp-toolkit/examples/voyageai
docker compose up --build
```

## Debugging Agents

If something isn't working in the app, test each agent in isolation without starting the full server:

```bash
cd mcp-toolkit/examples/voyageai

# Test a single agent
python test_agent.py weather What is the weather in Tokyo
python test_agent.py flights Flights from London to New York
python test_agent.py hotels Best hotels in Barcelona
python test_agent.py currency Convert 500 USD to EUR

# Test all four agents with the same query
python test_agent.py all Plan a trip to Paris from London
```

Each run connects **only** to the servers that agent needs, so a failure isolates exactly which server or API key is the problem.

## How mcp-toolkit Is Used

```python
# 1. MultiServerClient — connects to all 4 MCP servers at once
from mcp_toolkit.clients.multi import MultiServerClient
client = MultiServerClient(config, api_key=OPENAI_API_KEY)
async with client as mcp:

    # 2. mcp_to_openai_completions() — converts tool schemas for OpenAI Chat API
    from mcp_toolkit.converters import mcp_to_openai_completions
    tools = mcp_to_openai_completions(mcp.get_tools_by_server("weather"))

    # 3. Per-server tool filtering — each agent only sees its own tools
    weather_tools = mcp.get_tools_by_server("weather")
    hotel_tools   = mcp.get_tools_by_server("tavily")

    # 4. Tool execution — routes to correct server automatically
    result = await mcp.call_tool("get_forecast", {"city": "Tokyo", "days": 5})
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET /` | — | Serves React SPA (requires `npm run build` first) |
| `POST /chat` | `{"message": "...", "session_id": "..."}` | Freeform chat — all 4 agents run in parallel |
| `POST /plan` | `{"destination": "Tokyo", "origin": "London", ...}` | Structured trip planner — only relevant agents run |
| `GET /sessions` | — | List all sessions |
| `GET /sessions/:id` | — | Load session history |
| `DELETE /sessions/:id` | — | Delete session |
| `GET /health` | — | Health check — shows connected servers and tools |
