"""
Weather MCP Server

A simple MCP server demonstrating tools and resources using the free wttr.in API.
No API keys required.

Tools:
  - check_weather: Get current weather for a city
  - get_forecast: Get multi-day forecast for a city
  - compare_weather: Compare weather between two cities

Resources:
  - weather://favorites: A list of example cities to try
"""

import urllib.request
import json
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("weather")

# --- Helper ---

def _fetch_weather(city: str, format: str = "3") -> str:
    """Fetch weather data from wttr.in."""
    url = f"https://wttr.in/{urllib.parse.quote(city)}?format={format}"
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            return response.read().decode("utf-8").strip()
    except Exception as e:
        return f"Error: {e}"


import urllib.parse

# --- Tools ---

@mcp.tool()
def check_weather(city: str) -> str:
    """Get the current weather for a city. Returns temperature, condition, and wind."""
    # format="%l:+%c+%t+%w" gives: City: ☁️ +15°C ↗10km/h
    result = _fetch_weather(city, format="%l:+%c+%t+%w")
    return result


@mcp.tool()
def get_forecast(city: str, days: int = 3) -> str:
    """Get a multi-day weather forecast for a city.

    Args:
        city: City name (e.g. "London", "New York")
        days: Number of days (1-3)
    """
    days = max(1, min(3, days))  # wttr.in supports 1-3 days
    # format=v2 gives a nice text forecast, but it's very long
    # Instead, get day-by-day summary
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
            # Get the midday description
            hourly = day.get("hourly", [])
            desc = hourly[4]["weatherDesc"][0]["value"] if len(hourly) > 4 else "N/A"
            lines.append(f"  {date}: {desc}, {min_temp}°C - {max_temp}°C")

        return "\n".join(lines)
    except Exception as e:
        return f"Error fetching forecast: {e}"


@mcp.tool()
def compare_weather(city1: str, city2: str) -> str:
    """Compare current weather between two cities side by side.

    Args:
        city1: First city name
        city2: Second city name
    """
    w1 = _fetch_weather(city1, format="%c+%t+%w")
    w2 = _fetch_weather(city2, format="%c+%t+%w")
    return f"{city1}: {w1}\n{city2}: {w2}"


# --- Resources ---

FAVORITE_CITIES = ["Paris", "Sydney", "Gothenburg", "Stockholm", "Copenhagen", "Zurich"]


@mcp.resource("weather://favorites")
def get_favorites() -> str:
    """A list of example cities you can query weather for."""
    return "\n".join(f"- {city}" for city in FAVORITE_CITIES)


if __name__ == "__main__":
    mcp.run(transport="stdio")
