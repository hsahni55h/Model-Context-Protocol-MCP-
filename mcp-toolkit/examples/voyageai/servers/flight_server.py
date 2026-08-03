"""VoyageAI Flight MCP Server.

A custom MCP server that exposes flight data via AviationStack API.
Demonstrates: stdio transport (local server).

Tools:
    - search_flights: Search for flights between airports
    - get_airport_info: Get airport details by IATA code

Usage:
    python flight_server.py
"""

import os
import httpx
from mcp.server.fastmcp import FastMCP

server = FastMCP(
    "VoyageAI Flights",
    instructions="Flight search and airport info powered by AviationStack API",
)

AVIATIONSTACK_BASE = "https://api.aviationstack.com/v1"


def _get_api_key() -> str:
    key = os.environ.get("AVIATIONSTACK_API_KEY", "")
    if not key:
        raise ValueError(
            "AVIATIONSTACK_API_KEY not set. Get one at https://aviationstack.com"
        )
    return key


@server.tool()
async def search_flights(departure_iata: str, arrival_iata: str) -> str:
    """Search for flights between two airports.

    Args:
        departure_iata: Departure airport IATA code (e.g. "JFK", "LHR", "DEL")
        arrival_iata: Arrival airport IATA code (e.g. "LAX", "CDG", "NRT")

    Returns:
        Available flights with airline, times, and status.
    """
    api_key = _get_api_key()

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            f"{AVIATIONSTACK_BASE}/flights",
            params={
                "access_key": api_key,
                "dep_iata": departure_iata.upper(),
                "arr_iata": arrival_iata.upper(),
                "limit": 5,
            },
        )
        resp.raise_for_status()
        data = resp.json()

    if "error" in data:
        return f"Error: {data['error'].get('message', 'Unknown error')}"

    flights = data.get("data", [])
    if not flights:
        return f"No flights found from {departure_iata.upper()} to {arrival_iata.upper()}."

    lines = [f"Flights from {departure_iata.upper()} to {arrival_iata.upper()}:\n"]
    for f in flights[:5]:
        airline = f.get("airline", {}).get("name", "Unknown")
        flight_num = f.get("flight", {}).get("iata", "N/A")
        status = f.get("flight_status", "unknown")
        dep_time = f.get("departure", {}).get("scheduled", "N/A")
        arr_time = f.get("arrival", {}).get("scheduled", "N/A")

        lines.append(f"  {airline} {flight_num}")
        lines.append(f"    Status: {status}")
        lines.append(f"    Departure: {dep_time}")
        lines.append(f"    Arrival: {arr_time}")
        lines.append("")

    return "\n".join(lines)


@server.tool()
async def get_airport_info(iata_code: str) -> str:
    """Get information about an airport by its IATA code.

    Args:
        iata_code: Airport IATA code (e.g. "JFK", "LHR", "SIN")

    Returns:
        Airport name, city, country, and timezone.
    """
    api_key = _get_api_key()

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            f"{AVIATIONSTACK_BASE}/airports",
            params={
                "access_key": api_key,
                "iata_code": iata_code.upper(),
            },
        )
        resp.raise_for_status()
        data = resp.json()

    if "error" in data:
        return f"Error: {data['error'].get('message', 'Unknown error')}"

    airports = data.get("data", [])
    if not airports:
        return f"No airport found with IATA code '{iata_code.upper()}'."

    airport = airports[0]
    return (
        f"Airport: {airport.get('airport_name', 'N/A')}\n"
        f"  IATA: {airport.get('iata_code', 'N/A')}\n"
        f"  City: {airport.get('city_iata_code', 'N/A')}\n"
        f"  Country: {airport.get('country_name', 'N/A')}\n"
        f"  Timezone: {airport.get('timezone', 'N/A')}"
    )


if __name__ == "__main__":
    server.run()
