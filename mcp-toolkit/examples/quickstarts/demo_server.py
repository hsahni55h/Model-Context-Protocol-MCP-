"""
Demo MCP Server

A minimal server bundled with mcp-toolkit so you can verify your install
and run the quickstarts with zero setup — no API keys, no configuration.

Tools:
    echo(message)  — returns the message back
    add(a, b)      — returns a + b
    greet(name)    — returns a greeting

Run standalone:
    python demo_server.py
"""

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("demo")


@mcp.tool()
def echo(message: str) -> str:
    """Echo a message back unchanged."""
    return message


@mcp.tool()
def add(a: float, b: float) -> float:
    """Add two numbers and return the result."""
    return a + b


@mcp.tool()
def greet(name: str) -> str:
    """Return a friendly greeting for a given name."""
    return f"Hello, {name}! Welcome to MCP Toolkit."


if __name__ == "__main__":
    mcp.run()
