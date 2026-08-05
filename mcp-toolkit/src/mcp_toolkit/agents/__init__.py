"""
MCP Toolkit Agents

Reusable agent base classes for building multi-server MCP applications.

Usage:
    >>> from mcp_toolkit.agents import BaseAgent
    >>>
    >>> class WeatherAgent(BaseAgent):
    ...     server_names = ["weather"]
    ...     system_prompt = "You are a weather specialist."
    >>>
    >>> agent = WeatherAgent(mcp_client, openai_client)
    >>> result = await agent.run("What's the weather in Tokyo?")
"""

from mcp_toolkit.agents.base import BaseAgent

__all__ = ["BaseAgent"]
