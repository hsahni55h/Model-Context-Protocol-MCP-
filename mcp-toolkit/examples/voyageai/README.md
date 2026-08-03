# ✈️ VoyageAI — Multi-Agent Travel Planner

A showcase project demonstrating [mcp-toolkit](../../README.md) in a real-world application. VoyageAI is a multi-agent travel planner that uses MCP (Model Context Protocol) servers to gather weather, flights, hotels, and currency data — then synthesizes everything into a travel plan.

## Architecture

```
User query → Orchestrator (parses intent via LLM)
                → WeatherAgent  ┐
                → FlightAgent   │ asyncio.gather (parallel)
                → HotelAgent    │
                → CurrencyAgent ┘
                → Planner LLM synthesizes → final response
```

### What it demonstrates

| Feature | How |
|---------|-----|
| **stdio transport** | Custom weather, currency, and flight MCP servers |
| **streamable_http transport** | Tavily remote MCP server for web search |
| **Multi-server connection** | `MultiServerClient` connects to 4 servers simultaneously |
| **Tool schema conversion** | `mcp_to_openai()` converts MCP tools to OpenAI format |
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
│       ├── orchestrator.py     # Parses intent → parallel agents → synthesis
│       ├── weather.py          # WeatherAgent (weather server)
│       ├── flight.py           # FlightAgent (flights server)
│       ├── hotel.py            # HotelAgent (Tavily server)
│       └── currency.py         # CurrencyAgent (currency server)
├── templates/index.html        # Chat UI
├── static/                     # CSS + JS
├── Dockerfile                  # Container build
├── docker-compose.yml          # Docker Compose
└── render.yaml                 # One-click Render deploy
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

### 3. Run

```bash
cd mcp-toolkit/examples/voyageai
uvicorn app.main:app --reload
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000) and start planning trips!

### Docker

```bash
cd mcp-toolkit/examples/voyageai
docker compose up --build
```

## How mcp-toolkit Is Used

```python
# 1. MultiServerClient — connects to all 4 MCP servers at once
from mcp_toolkit.clients.multi import MultiServerClient
client = MultiServerClient.from_dict(servers, api_key=OPENAI_API_KEY)
mcp = await client.__aenter__()

# 2. mcp_to_openai() — converts tool schemas for OpenAI
from mcp_toolkit.converters import mcp_to_openai
tools = mcp_to_openai(mcp._all_mcp_tools)

# 3. Per-server tool filtering
weather_tools = mcp.get_tools_by_server("weather")

# 4. Tool execution — routes to correct server automatically
result = await mcp.call_tool("get_forecast", {"city": "Tokyo", "days": 5})
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET /` | — | Chat UI |
| `POST /chat` | `{"message": "...", "session_id": "..."}` | Send message |
| `GET /sessions` | — | List all sessions |
| `GET /sessions/:id` | — | Load session history |
| `DELETE /sessions/:id` | — | Delete session |
| `GET /health` | — | Health check |
