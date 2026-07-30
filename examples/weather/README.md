# Weather MCP Server

A simple MCP server demonstrating **tools** and **resources** using the free [wttr.in](https://wttr.in) API. No API keys required — the simplest possible MCP example to start with.

## MCP features demonstrated

| Feature | What it shows |
|---|---|
| **Multiple tools** | `check_weather`, `get_forecast`, `compare_weather` — LLM picks the right one |
| **Resources** | `weather://favorites` — static data the LLM can read for context |
| **Typed parameters** | `days: int = 3` — optional params with defaults |

## Tools

| Tool | Description |
|---|---|
| `check_weather(city)` | Current weather: condition, temperature, wind |
| `get_forecast(city, days=3)` | 1-3 day forecast with highs/lows |
| `compare_weather(city1, city2)` | Side-by-side comparison of two cities |

## Resources

| URI | Description |
|---|---|
| `weather://favorites` | List of example cities to try |

## Running

```bash
# Test with MCP Inspector (from repo root)
uv run mcp dev examples/weather/server.py
```

Open the Inspector URL, then:
1. Click **Tools** → try `check_weather` with `city: "Tokyo"`
2. Click **Resources** → see `weather://favorites`
3. Try `compare_weather` with `city1: "London"`, `city2: "Sydney"`

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

## File structure

```
weather/
  server.py     ← MCP server with tools + resource (single file)
  README.md
```
