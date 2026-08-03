"""Hotel/attractions agent — searches the web via Tavily."""

from app.agents.base import BaseAgent


class HotelAgent(BaseAgent):
    server_names = ["tavily"]
    system_prompt = """\
You are a hotel and attractions research specialist for travel planning.
Given a destination, use tavily_search to find:
- Top-rated hotels with approximate prices
- Must-see attractions and activities
- Recommended restaurants or food experiences
Return a concise, well-organized summary.
Keep it brief and actionable."""
