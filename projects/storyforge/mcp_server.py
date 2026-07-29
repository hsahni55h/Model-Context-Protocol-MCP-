import asyncio
from mcp.server.fastmcp import FastMCP
from functions.get_realtime_info import get_realtime_info
from functions.get_video_transcription import generate_video_transcription

mcp = FastMCP("StoryForge Agent")

@mcp.tool()
async def get_realtime_info_mcp(query: str) -> str:
    """
    Fetch real-time info for a topic (Tavily) and return a concise summary (OpenAI).
    """
    return await asyncio.to_thread(get_realtime_info, query)

@mcp.tool()
async def generate_video_transcription_mcp(query: str) -> str:
    """
    Fetch real-time info for a topic, then generate a short video script.
    """
    info = await asyncio.to_thread(get_realtime_info, query)
    return await asyncio.to_thread(generate_video_transcription, info)

if __name__ == "__main__":
    mcp.run(transport="stdio")
