"""Base agent for VoyageAI specialized agents.

Thin wrapper around mcp_toolkit.agents.BaseAgent that wires in the
app-configured OpenAI model so subclasses don't need to repeat it.
"""

from openai import AsyncOpenAI

from mcp_toolkit.agents import BaseAgent as _ToolkitBaseAgent
from mcp_toolkit.clients.multi import MultiServerClient

from app.config import OPENAI_MODEL


class BaseAgent(_ToolkitBaseAgent):
    """VoyageAI base agent.

    Extends mcp_toolkit.agents.BaseAgent with the app's configured model
    so all specialist agents share the same model without repeating it.

    Subclass usage::

        class WeatherAgent(BaseAgent):
            server_names = ["weather"]
            system_prompt = "You are a weather specialist."
    """

    def __init__(self, mcp_client: MultiServerClient, openai_client: AsyncOpenAI):
        super().__init__(mcp_client, openai_client, model=OPENAI_MODEL)
