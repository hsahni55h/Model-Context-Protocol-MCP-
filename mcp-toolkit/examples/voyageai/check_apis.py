#!/usr/bin/env python3
"""Check that all external API keys are valid and returning data.

Run from examples/voyageai/ BEFORE starting the app or running test_agent.py.
This bypasses the LLM entirely and shows raw API responses.

    python check_apis.py
"""

import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv
import httpx

# Load .env from this directory
load_dotenv(Path(__file__).parent / ".env")

OPENWEATHER_API_KEY   = os.environ.get("OPENWEATHER_API_KEY", "")
AVIATIONSTACK_API_KEY = os.environ.get("AVIATIONSTACK_API_KEY", "")
EXCHANGE_RATE_API_KEY = os.environ.get("EXCHANGE_RATE_API_KEY", "")
TAVILY_API_KEY        = os.environ.get("TAVILY_API_KEY", "")


def header(title: str) -> None:
    print(f"\n{'='*55}")
    print(f"  {title}")
    print(f"{'='*55}")


def ok(msg: str) -> None:
    print(f"  ✓  {msg}")


def fail(msg: str) -> None:
    print(f"  ✗  {msg}")


async def check_openweather() -> None:
    header("OpenWeather API  (weather agent)")
    key = OPENWEATHER_API_KEY
    if not key:
        fail("OPENWEATHER_API_KEY not set in .env")
        return

    print(f"  Key: {key[:8]}...")
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={"q": "London", "appid": key, "units": "metric"},
        )

    if resp.status_code == 200:
        data = resp.json()
        temp = data["main"]["temp"]
        desc = data["weather"][0]["description"]
        ok(f"London: {temp}°C, {desc}")
    elif resp.status_code == 401:
        fail(f"401 Unauthorized — key is invalid or not yet activated")
        fail("New keys take up to 2 hours to activate on openweathermap.org")
        print(f"  Raw: {resp.text[:200]}")
    else:
        fail(f"HTTP {resp.status_code}")
        print(f"  Raw: {resp.text[:200]}")


async def check_aviationstack() -> None:
    header("AviationStack API  (flights agent)")
    key = AVIATIONSTACK_API_KEY
    if not key:
        fail("AVIATIONSTACK_API_KEY not set in .env")
        return

    print(f"  Key: {key[:8]}...")
    # Free tier: HTTP only (HTTPS returns "Access Restricted" error)
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            "http://api.aviationstack.com/v1/flights",
            params={"access_key": key, "dep_iata": "LHR", "arr_iata": "JFK", "limit": 1},
        )

    if resp.status_code == 200:
        data = resp.json()
        if "error" in data:
            code = data["error"].get("code", "unknown")
            msg  = data["error"].get("message", "")
            fail(f"API error [{code}]: {msg}")
            if "https" in code.lower() or "https" in msg.lower():
                fail("This error means HTTPS was used — fixed in servers/flight_server.py")
        else:
            flights = data.get("data", [])
            ok(f"Connected — {len(flights)} flight(s) returned for LHR→JFK")
            if not flights:
                print("  Note: No live flights right now is normal (free tier has limited data)")
    else:
        fail(f"HTTP {resp.status_code}")
        print(f"  Raw: {resp.text[:200]}")


async def check_exchange_rate() -> None:
    header("ExchangeRate API  (currency agent)")
    key = EXCHANGE_RATE_API_KEY
    if not key:
        fail("EXCHANGE_RATE_API_KEY not set in .env")
        return

    print(f"  Key: {key[:8]}...")
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            f"https://v6.exchangerate-api.com/v6/{key}/pair/USD/EUR/100",
        )

    if resp.status_code == 200:
        data = resp.json()
        if data.get("result") == "success":
            rate = data.get("conversion_rate")
            converted = data.get("conversion_result")
            ok(f"100 USD = {converted} EUR  (rate: {rate})")
        else:
            fail(f"API error: {data.get('error-type', 'unknown')}")
    else:
        fail(f"HTTP {resp.status_code}: {resp.text[:200]}")


async def check_tavily() -> None:
    header("Tavily API  (hotels agent)")
    key = TAVILY_API_KEY
    if not key:
        fail("TAVILY_API_KEY not set in .env")
        return

    print(f"  Key: {key[:8]}...")
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            "https://api.tavily.com/search",
            json={"api_key": key, "query": "best hotels Barcelona", "max_results": 1},
        )

    if resp.status_code == 200:
        data = resp.json()
        results = data.get("results", [])
        ok(f"Connected — {len(results)} result(s) returned")
    elif resp.status_code == 401:
        fail("401 Unauthorized — TAVILY_API_KEY is invalid")
    else:
        fail(f"HTTP {resp.status_code}: {resp.text[:200]}")


async def main() -> None:
    print("Checking all VoyageAI API keys...\n")
    await check_openweather()
    await check_aviationstack()
    await check_exchange_rate()
    await check_tavily()
    print(f"\n{'='*55}\n")


if __name__ == "__main__":
    asyncio.run(main())
