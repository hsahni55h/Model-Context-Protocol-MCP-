"""
MCP Server Helpers

Utility functions for building MCP servers — environment loading,
OpenAI helper for tool implementations, and common patterns.

Note on AI helpers
------------------
Only an OpenAI helper is provided here because OpenAI's Python SDK ships a
**synchronous** client (``openai.OpenAI``) that can be called like a regular
function — no ``await`` needed. This makes it safe to wrap in a plain ``def``.

Gemini and Anthropic's SDKs are **async-only**, meaning they require ``await``
and cannot be called from a plain synchronous function. Calling them through
``asyncio.run()`` would crash inside an MCP server because the MCP event loop
is already running. For those providers, call their async clients directly
inside your ``async def`` tool functions:

    from anthropic import AsyncAnthropic

    client = AsyncAnthropic()

    @mcp.tool()
    async def summarize(text: str) -> str:
        response = await client.messages.create(...)  # just await directly
        return response.content[0].text
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any


def load_env(start_dir: str | Path | None = None) -> bool:
    """Load .env file by walking up the directory tree.

    Searches upward from `start_dir` (default: caller's directory) until
    a .env file is found. This eliminates hardcoded relative path calculations
    like `Path(__file__).parent.parent.parent / ".env"`.

    Args:
        start_dir: Directory to start searching from. Defaults to cwd.

    Returns:
        True if a .env file was found and loaded, False otherwise.
    """
    try:
        from dotenv import load_dotenv
    except ImportError:
        return False

    search_dir = Path(start_dir) if start_dir else Path.cwd()

    # Walk up the tree looking for .env
    current = search_dir.resolve()
    for _ in range(20):  # Safety limit
        env_file = current / ".env"
        if env_file.is_file():
            load_dotenv(env_file)
            return True
        parent = current.parent
        if parent == current:
            break
        current = parent

    return False


def openai_helper(
    prompt: str,
    *,
    system: str = "You are a helpful assistant.",
    model: str = "gpt-4o-mini",
    temperature: float = 0.3,
    max_tokens: int = 500,
    api_key: str | None = None,
) -> str:
    """Quick OpenAI call for use inside MCP tool implementations.

    A convenience wrapper around the OpenAI Chat Completions API.
    Useful when your MCP tools need AI processing (summarization,
    extraction, classification, etc.).

    Args:
        prompt: The user prompt.
        system: System prompt.
        model: Model name.
        temperature: Sampling temperature.
        max_tokens: Max response tokens.
        api_key: API key override. Falls back to OPENAI_API_KEY env var.

    Returns:
        The model's text response.

    Raises:
        ValueError: If no API key is available.
        ImportError: If openai package is not installed.

    Example:
        >>> from mcp_toolkit.server import openai_helper
        >>> summary = openai_helper(
        ...     f"Summarize: {long_text}",
        ...     system="You are a concise summarizer.",
        ...     max_tokens=200,
        ... )
    """
    resolved_key = api_key or os.getenv("OPENAI_API_KEY")
    if not resolved_key:
        raise ValueError("OPENAI_API_KEY not set. Pass api_key= or set the env var.")

    try:
        from openai import OpenAI
    except ImportError as e:
        raise ImportError(
            "openai_helper requires the openai package. "
            "Install with: pip install openai"
        ) from e

    client = OpenAI(api_key=resolved_key)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content.strip()


def get_env_or_raise(key: str, message: str | None = None) -> str:
    """Get an environment variable or raise with a helpful message.

    Args:
        key: Environment variable name.
        message: Custom error message. Defaults to a helpful generic one.

    Returns:
        The environment variable value.

    Raises:
        ValueError: If the variable is not set.
    """
    value = os.getenv(key)
    if not value:
        raise ValueError(
            message or f"Required environment variable '{key}' is not set. "
            f"Add it to your .env file or export it."
        )
    return value
