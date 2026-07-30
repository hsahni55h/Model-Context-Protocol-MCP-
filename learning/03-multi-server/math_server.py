"""
A simple math MCP server for demonstrating multi-server setups.

Exposes basic math tools so the multi-server client can connect to this
alongside the terminal server and show tool aggregation across servers.
"""

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("math")


@mcp.tool()
def add(a: float, b: float) -> str:
    """Add two numbers together."""
    return str(a + b)


@mcp.tool()
def multiply(a: float, b: float) -> str:
    """Multiply two numbers together."""
    return str(a * b)


@mcp.tool()
def divide(a: float, b: float) -> str:
    """Divide a by b. Returns an error message if b is zero."""
    if b == 0:
        return "Error: division by zero"
    return str(a / b)


if __name__ == "__main__":
    mcp.run(transport="stdio")
