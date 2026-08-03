"""VoyageAI Weather MCP Server.

A custom MCP server that exposes weather tools via OpenWeather API.
Demonstrates: stdio transport (local server).

Tools:
    - get_current_weather: Get current weather conditions for a city
    - get_forecast: Get multi-day weather forecast

Usage:
    # Run directly (stdio transport)
    python weather_server.py

    # Or via mcp dev tools
    mcp dev weather_server.py
"""

import os
import httpx
from mcp.server.fastmcp import FastMCP

server = FastMCP(
    "VoyageAI Weather",
    instructions="Weather data and travel packing suggestions powered by OpenWeather API",
)

OPENWEATHER_BASE = "https://api.openweathermap.org/data/2.5"


def _get_api_key() -> str:
    key = os.environ.get("OPENWEATHER_API_KEY", "")
    if not key:
        raise ValueError(
            "OPENWEATHER_API_KEY not set. Get one at https://openweathermap.org/api"
        )
    return key


@server.tool()
async def get_current_weather(city: str, country_code: str = "") -> str:
    """Get current weather conditions for a city.

    Args:
        city: City name (e.g. "London", "New York", "Tokyo")
        country_code: Optional ISO 3166 country code (e.g. "GB", "US", "JP")

    Returns:
        Current weather including temperature, humidity, wind, and description.
    """
    api_key = _get_api_key()
    query = f"{city},{country_code}" if country_code else city

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            f"{OPENWEATHER_BASE}/weather",
            params={"q": query, "appid": api_key, "units": "metric"},
        )
        resp.raise_for_status()
        data = resp.json()

    weather = data["weather"][0]
    main = data["main"]
    wind = data["wind"]

    return (
        f"Weather in {data['name']}, {data.get('sys', {}).get('country', '')}:\n"
        f"  Condition: {weather['main']} — {weather['description']}\n"
        f"  Temperature: {main['temp']}°C (feels like {main['feels_like']}°C)\n"
        f"  Humidity: {main['humidity']}%\n"
        f"  Wind: {wind['speed']} m/s\n"
        f"  Visibility: {data.get('visibility', 'N/A')} m"
    )


@server.tool()
async def get_forecast(city: str, days: int = 5, country_code: str = "") -> str:
    """Get multi-day weather forecast for a city.

    Args:
        city: City name (e.g. "Paris", "Mumbai")
        days: Number of days to forecast (1-5, default 5)
        country_code: Optional ISO 3166 country code

    Returns:
        Day-by-day forecast with temperatures and conditions.
    """
    api_key = _get_api_key()
    query = f"{city},{country_code}" if country_code else city
    days = max(1, min(days, 5))

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            f"{OPENWEATHER_BASE}/forecast",
            params={"q": query, "appid": api_key, "units": "metric", "cnt": days * 8},
        )
        resp.raise_for_status()
        data = resp.json()

    # Group by day (API returns 3-hour intervals)
    daily: dict[str, list] = {}
    for item in data["list"]:
        date = item["dt_txt"].split(" ")[0]
        if date not in daily:
            daily[date] = []
        daily[date].append(item)

    lines = [f"Forecast for {data['city']['name']}, {data['city']['country']}:\n"]
    for date, entries in list(daily.items())[:days]:
        temps = [e["main"]["temp"] for e in entries]
        conditions = [e["weather"][0]["main"] for e in entries]
        # Most common condition
        main_condition = max(set(conditions), key=conditions.count)
        lines.append(
            f"  {date}: {min(temps):.0f}°C — {max(temps):.0f}°C, {main_condition}"
        )

    return "\n".join(lines)


if __name__ == "__main__":
    server.run()
