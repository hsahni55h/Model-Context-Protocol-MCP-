import asyncio
from typing import Any, Dict, List, Union
from mcp.server.fastmcp import FastMCP
from src.job_api import fetch_linkedin_jobs

mcp = FastMCP("Job Recommender")


@mcp.tool()
async def fetch_linkedin_jobs_tool(
    search_query: str,
    location: str = "India",
    rows: int = 60
) -> Dict[str, Any]:
    """
    Fetch LinkedIn jobs via Apify.
    Returns a dict with either `jobs` or `error`.
    """
    result = await asyncio.to_thread(fetch_linkedin_jobs, search_query, location, rows)

    # Normalize output
    if isinstance(result, dict) and "error" in result:
        return result
    return {"jobs": result}


if __name__ == "__main__":
    mcp.run(transport="stdio")
