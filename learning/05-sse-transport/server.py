"""
Weather MCP Server — SSE Transport

Same weather tools as 01-basics/examples, but served over SSE instead of stdio.
This is the key difference: the server runs as a persistent HTTP service that
multiple clients can connect to simultaneously.

Start with:
    uv run python learning/05-sse-transport/server.py

Then connect a client to http://localhost:8000/sse
"""

import urllib.request
import urllib.parse
import json
from mcp.server.fastmcp import FastMCP

# Create server — set host/port for SSE transport
mcp = FastMCP("weather-sse", host="0.0.0.0", port=8000)


# --- Helper ---

def _fetch_weather(city: str, format: str = "3") -> str:
    """Fetch weather data from wttr.in."""
    url = f"https://wttr.in/{urllib.parse.quote(city)}?format={format}"
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            return response.read().decode("utf-8").strip()
    except Exception as e:
        return f"Error: {e}"


# --- Tools ---

@mcp.tool()
def check_weather(city: str) -> str:
    """Get the current weather for a city. Returns temperature, condition, and wind.

    Args:
        city: City name (e.g. "London", "Tokyo")
    """
    return _fetch_weather(city, format="%l:+%c+%t+%w")


@mcp.tool()
def get_forecast(city: str, days: int = 3) -> str:
    """Get a multi-day weather forecast for a city.

    Args:
        city: City name (e.g. "London", "New York")
        days: Number of days (1-3)
    """
    days = max(1, min(3, days))
    url = f"https://wttr.in/{urllib.parse.quote(city)}?format=j1"
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))

        forecast_days = data.get("weather", [])[:days]
        lines = [f"Forecast for {city} ({days} day{'s' if days > 1 else ''}):\n"]

        for day in forecast_days:
            date = day["date"]
            max_temp = day["maxtempC"]
            min_temp = day["mintempC"]
            hourly = day.get("hourly", [])
            desc = hourly[4]["weatherDesc"][0]["value"] if len(hourly) > 4 else "N/A"
            lines.append(f"  {date}: {desc}, {min_temp}°C - {max_temp}°C")

        return "\n".join(lines)
    except Exception as e:
        return f"Error fetching forecast: {e}"


# --- Resources ---

@mcp.resource("weather://favorites")
def get_favorites() -> str:
    """A list of example cities you can query weather for."""
    return "\n".join(f"- {city}" for city in [
        "Paris", "Sydney", "Gothenburg", "Stockholm", "Copenhagen", "Zurich"
    ])


# --- Entry point ---
# The ONLY difference from a stdio server: transport="sse"
# This starts an HTTP server (uvicorn) with SSE endpoints at /sse and /messages/

if __name__ == "__main__":
    print("Starting weather SSE server on http://0.0.0.0:8000/sse")
    mcp.run(transport="sse")
