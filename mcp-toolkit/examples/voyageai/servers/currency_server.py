"""VoyageAI Currency Converter MCP Server.

A custom MCP server that exposes currency conversion tools via ExchangeRate API.
Demonstrates: stdio transport (local server).

Tools:
    - convert_currency: Convert an amount between currencies
    - get_exchange_rate: Get the exchange rate between two currencies

Usage:
    # Run directly (stdio transport)
    python currency_server.py

    # Or via mcp dev tools
    mcp dev currency_server.py
"""

import os
import httpx
from mcp.server.fastmcp import FastMCP

server = FastMCP(
    "VoyageAI Currency",
    instructions="Real-time currency conversion and travel budget tools",
)

EXCHANGE_RATE_BASE = "https://v6.exchangerate-api.com/v6"


def _get_api_key() -> str:
    key = os.environ.get("EXCHANGE_RATE_API_KEY", "")
    if not key:
        raise ValueError(
            "EXCHANGE_RATE_API_KEY not set. Get one at https://www.exchangerate-api.com/"
        )
    return key


@server.tool()
async def get_exchange_rate(from_currency: str, to_currency: str) -> str:
    """Get the current exchange rate between two currencies.

    Args:
        from_currency: Source currency code (e.g. "USD", "EUR", "GBP")
        to_currency: Target currency code (e.g. "JPY", "INR", "THB")

    Returns:
        The current exchange rate and conversion info.
    """
    api_key = _get_api_key()
    from_code = from_currency.upper().strip()
    to_code = to_currency.upper().strip()

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            f"{EXCHANGE_RATE_BASE}/{api_key}/pair/{from_code}/{to_code}"
        )
        resp.raise_for_status()
        data = resp.json()

    if data.get("result") != "success":
        return f"Error: Could not get rate for {from_code} → {to_code}. Check currency codes."

    rate = data["conversion_rate"]
    return (
        f"Exchange Rate: 1 {from_code} = {rate:.4f} {to_code}\n"
        f"Last updated: {data.get('time_last_update_utc', 'N/A')}"
    )


@server.tool()
async def convert_currency(
    amount: float, from_currency: str, to_currency: str
) -> str:
    """Convert an amount from one currency to another.

    Args:
        amount: Amount to convert
        from_currency: Source currency code (e.g. "USD")
        to_currency: Target currency code (e.g. "EUR")

    Returns:
        Converted amount with rate information.
    """
    api_key = _get_api_key()
    from_code = from_currency.upper().strip()
    to_code = to_currency.upper().strip()

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            f"{EXCHANGE_RATE_BASE}/{api_key}/pair/{from_code}/{to_code}/{amount}"
        )
        resp.raise_for_status()
        data = resp.json()

    if data.get("result") != "success":
        return f"Error: Conversion failed for {amount} {from_code} → {to_code}."

    converted = data["conversion_result"]
    rate = data["conversion_rate"]
    return (
        f"💱 {amount:,.2f} {from_code} = {converted:,.2f} {to_code}\n"
        f"Rate: 1 {from_code} = {rate:.4f} {to_code}"
    )


if __name__ == "__main__":
    server.run()
