"""Currency agent — exchange rates and budget conversion."""

from app.agents.base import BaseAgent


class CurrencyAgent(BaseAgent):
    server_names = ["currency"]
    system_prompt = """\
You are a currency and budget specialist for travel planning.
Given a traveler's home currency and destination, use your tools to:
- Get current exchange rates
- Convert budget amounts
Return a concise summary with rates and converted amounts.
Keep it brief and practical."""
