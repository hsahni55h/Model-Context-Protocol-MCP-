"""Flight agent — searches flights and airport info."""

from app.agents.base import BaseAgent


class FlightAgent(BaseAgent):
    server_names = ["flights"]
    system_prompt = """\
You are a flight research specialist for travel planning.
Given origin/destination cities, use your tools to find flights and airport info.
Return a concise summary of:
- Available flight routes
- Airport details (IATA codes, locations)
- Key travel logistics
Keep it brief and actionable."""
