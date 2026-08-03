"""Weather agent — checks conditions and forecasts at destinations."""

from app.agents.base import BaseAgent


class WeatherAgent(BaseAgent):
    server_names = ["weather"]
    system_prompt = """\
You are a weather research specialist for travel planning.
Given a destination, use your tools to get current weather and forecasts.
Return a concise weather summary including:
- Current conditions and temperature
- Multi-day forecast overview
- What to expect and how to prepare
Keep it brief and travel-relevant."""
