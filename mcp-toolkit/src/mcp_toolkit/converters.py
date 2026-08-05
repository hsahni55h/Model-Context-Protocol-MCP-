"""
MCP Tool/Schema Converters

Convert MCP tool definitions to formats expected by various LLM providers.
Handles schema cleaning and format differences transparently.
"""

from __future__ import annotations

from typing import Any


def clean_schema(schema: Any) -> Any:
    """Recursively remove 'title' fields from a JSON schema.

    Many LLM providers reject schemas that include 'title' keys added by
    Pydantic or other serializers. This strips them out.

    Args:
        schema: A JSON schema dict (or list/primitive).

    Returns:
        The cleaned schema with all 'title' fields removed.
    """
    if isinstance(schema, dict):
        schema.pop("title", None)
        for key, value in list(schema.items()):
            schema[key] = clean_schema(value)
        return schema
    if isinstance(schema, list):
        return [clean_schema(item) for item in schema]
    return schema


def mcp_to_openai(mcp_tools: list) -> list[dict[str, Any]]:
    """Convert MCP tools to OpenAI Responses API format.

    Use this with ``openai.responses.create()`` (the newer Responses API).
    For the standard ``openai.chat.completions.create()`` API, use
    :func:`mcp_to_openai_chat` instead.

    Args:
        mcp_tools: List of MCP tool objects (with .name, .description, .inputSchema).

    Returns:
        List of tool dicts in OpenAI Responses API format (flat, no nested "function" key).

    Example:
        >>> from mcp_toolkit.converters import mcp_to_openai
        >>> tools = mcp_to_openai(await session.list_tools())
        >>> response = openai.responses.create(model="gpt-4o", tools=tools, ...)
    """
    openai_tools = []
    for tool in mcp_tools:
        parameters = clean_schema(tool.inputSchema) if tool.inputSchema else {}
        openai_tools.append({
            "type": "function",
            "name": tool.name,
            "description": tool.description or "",
            "parameters": parameters,
        })
    return openai_tools


def mcp_to_openai_chat(mcp_tools: list) -> list[dict[str, Any]]:
    """Convert MCP tools to OpenAI Chat Completions API format.

    Use this with ``openai.chat.completions.create()`` — the standard Chat API
    used by most applications and the ``AsyncOpenAI`` client. The difference from
    :func:`mcp_to_openai` is the nested ``"function"`` key required by Chat Completions.

    Args:
        mcp_tools: List of MCP tool objects (with .name, .description, .inputSchema).

    Returns:
        List of tool dicts in OpenAI Chat Completions format (with nested "function" key).

    Example:
        >>> from mcp_toolkit.converters import mcp_to_openai_chat
        >>> tools = mcp_to_openai_chat(await session.list_tools())
        >>> response = await openai.chat.completions.create(model="gpt-4o", tools=tools, ...)
    """
    chat_tools = []
    for tool in mcp_tools:
        parameters = clean_schema(tool.inputSchema) if tool.inputSchema else {}
        chat_tools.append({
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description or "",
                "parameters": parameters,
            },
        })
    return chat_tools


def mcp_to_gemini(mcp_tools: list) -> list[dict[str, Any]]:
    """Convert MCP tools to Google Gemini FunctionDeclaration format.

    Args:
        mcp_tools: List of MCP tool objects.

    Returns:
        List of FunctionDeclaration-compatible dicts for Gemini's Tool wrapper.

    Example:
        >>> from mcp_toolkit.converters import mcp_to_gemini
        >>> declarations = mcp_to_gemini(mcp_tools)
        >>> # Use with: genai types.Tool(function_declarations=declarations)
    """
    declarations = []
    for tool in mcp_tools:
        schema = clean_schema(tool.inputSchema) if tool.inputSchema else {}
        # Gemini expects 'properties' and 'required' at top level of parameters
        parameters = {}
        if schema.get("properties"):
            parameters["type"] = "OBJECT"
            parameters["properties"] = {
                name: _convert_property_to_gemini(prop)
                for name, prop in schema["properties"].items()
            }
            if schema.get("required"):
                parameters["required"] = schema["required"]

        declarations.append({
            "name": tool.name,
            "description": tool.description or "",
            "parameters": parameters if parameters else None,
        })
    return declarations


def mcp_to_anthropic(mcp_tools: list) -> list[dict[str, Any]]:
    """Convert MCP tools to Anthropic Claude API tool format.

    Args:
        mcp_tools: List of MCP tool objects.

    Returns:
        List of tool dicts in Anthropic's format.

    Example:
        >>> from mcp_toolkit.converters import mcp_to_anthropic
        >>> tools = mcp_to_anthropic(mcp_tools)
        >>> # Use with: client.messages.create(tools=tools, ...)
    """
    anthropic_tools = []
    for tool in mcp_tools:
        input_schema = clean_schema(tool.inputSchema) if tool.inputSchema else {"type": "object", "properties": {}}
        anthropic_tools.append({
            "name": tool.name,
            "description": tool.description or "",
            "input_schema": input_schema,
        })
    return anthropic_tools


def _convert_property_to_gemini(prop: dict) -> dict:
    """Convert a JSON Schema property to Gemini's parameter format."""
    gemini_type_map = {
        "string": "STRING",
        "number": "NUMBER",
        "integer": "INTEGER",
        "boolean": "BOOLEAN",
        "array": "ARRAY",
        "object": "OBJECT",
    }
    result = {}
    json_type = prop.get("type", "string")
    result["type"] = gemini_type_map.get(json_type, "STRING")
    if prop.get("description"):
        result["description"] = prop["description"]
    if json_type == "array" and prop.get("items"):
        result["items"] = _convert_property_to_gemini(prop["items"])
    if prop.get("enum"):
        result["enum"] = prop["enum"]
    return result
