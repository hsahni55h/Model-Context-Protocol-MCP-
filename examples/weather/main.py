from mcp.server.fastmcp import FastMCP
from tools.weather import get_weather

mcp = FastMCP("Weather checker")

@mcp.tool()
async def check_weather(city: str) -> dict:
    """Get the weather for a given city."""
    result = get_weather(city)
    return {"city": city, "result": result}

if __name__ == "__main__":
    mcp.run(transport="stdio")
