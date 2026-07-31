"""
LangChain MCP Client

A drop-in MCP client that uses LangChain's agent framework with MCP adapters.
Provides the simplest path from MCP server to working agent.
"""

from __future__ import annotations

import os
from typing import Any

from mcp_toolkit.clients.base import BaseMCPClient


class LangChainMCPClient(BaseMCPClient):
    """MCP client powered by LangChain + LangGraph.

    Uses langchain-mcp-adapters to automatically convert MCP tools
    to LangChain tools, then builds a React agent.

    Example:
        >>> async with LangChainMCPClient(server_script="server.py") as client:
        ...     response = await client.chat("Read the file hello.txt")
        ...     print(response)
    """

    def __init__(
        self,
        *,
        model: str = "gpt-4o-mini",
        api_key: str | None = None,
        temperature: float = 0,
        max_retries: int = 2,
        **kwargs,
    ):
        """Initialize the LangChain MCP client.

        Args:
            model: OpenAI model name for the LangChain agent.
            api_key: OpenAI API key. Falls back to OPENAI_API_KEY env var.
            temperature: Sampling temperature.
            max_retries: Number of API retries on transient failures.
            **kwargs: Passed to BaseMCPClient (server_script, server_url, etc.)
        """
        super().__init__(**kwargs)
        self.model = model
        self.temperature = temperature
        self.max_retries = max_retries

        resolved_key = api_key or os.getenv("OPENAI_API_KEY")
        if not resolved_key:
            raise ValueError(
                "OpenAI API key required for LangChain agent. "
                "Pass api_key= or set OPENAI_API_KEY env var."
            )

        try:
            from langchain_openai import ChatOpenAI
            from langchain_mcp_adapters.tools import load_mcp_tools
            from langgraph.prebuilt import create_react_agent
        except ImportError as e:
            raise ImportError(
                "LangChain client requires the 'langchain' extra. "
                "Install with: pip install 'mcp-toolkit[langchain]'"
            ) from e

        self._llm = ChatOpenAI(
            model=model,
            temperature=temperature,
            max_retries=max_retries,
            api_key=resolved_key,
        )
        self._load_mcp_tools = load_mcp_tools
        self._create_react_agent = create_react_agent
        self._agent = None

    async def _connect(self) -> None:
        """Connect and build the LangChain agent with MCP tools."""
        await super()._connect()

        # Use langchain-mcp-adapters to load tools directly from session
        lc_tools = await self._load_mcp_tools(self._session)
        self._agent = self._create_react_agent(self._llm, lc_tools)

    async def chat(self, message: str) -> str:
        """Send a message and get a response via the LangChain agent.

        The agent automatically handles tool calling and multi-step reasoning.

        Args:
            message: User message.

        Returns:
            The agent's final text response.
        """
        if not self._agent:
            raise RuntimeError("Not connected. Use 'async with' context manager.")

        response = await self._agent.ainvoke({"messages": message})

        # Extract the final AI message
        messages = response.get("messages", [])
        if messages:
            last_message = messages[-1]
            if hasattr(last_message, "content"):
                return last_message.content
        return str(response)
