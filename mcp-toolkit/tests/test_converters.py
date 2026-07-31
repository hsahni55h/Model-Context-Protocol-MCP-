"""Tests for mcp_toolkit.converters"""

import pytest

from mcp_toolkit.converters import clean_schema, mcp_to_openai, mcp_to_gemini, mcp_to_anthropic


class MockTool:
    """Mock MCP tool for testing."""

    def __init__(self, name: str, description: str, input_schema: dict):
        self.name = name
        self.description = description
        self.inputSchema = input_schema


@pytest.fixture
def sample_tools():
    return [
        MockTool(
            name="check_weather",
            description="Get current weather for a city",
            input_schema={
                "type": "object",
                "title": "CheckWeatherInput",
                "properties": {
                    "city": {
                        "type": "string",
                        "title": "City",
                        "description": "City name",
                    }
                },
                "required": ["city"],
            },
        ),
        MockTool(
            name="get_forecast",
            description="Get multi-day forecast",
            input_schema={
                "type": "object",
                "title": "ForecastInput",
                "properties": {
                    "city": {"type": "string", "title": "City"},
                    "days": {"type": "integer", "title": "Days", "description": "Number of days"},
                },
                "required": ["city"],
            },
        ),
    ]


class TestCleanSchema:
    def test_removes_title_from_top_level(self):
        schema = {"title": "MySchema", "type": "object", "properties": {}}
        result = clean_schema(schema)
        assert "title" not in result
        assert result["type"] == "object"

    def test_removes_nested_titles(self):
        schema = {
            "title": "Top",
            "properties": {
                "name": {"title": "Name", "type": "string"},
                "age": {"title": "Age", "type": "integer"},
            },
        }
        result = clean_schema(schema)
        assert "title" not in result
        assert "title" not in result["properties"]["name"]
        assert "title" not in result["properties"]["age"]

    def test_handles_lists(self):
        schema = [{"title": "Item", "type": "string"}]
        result = clean_schema(schema)
        assert "title" not in result[0]

    def test_handles_primitives(self):
        assert clean_schema("hello") == "hello"
        assert clean_schema(42) == 42
        assert clean_schema(None) is None


class TestMCPToOpenAI:
    def test_converts_tools(self, sample_tools):
        result = mcp_to_openai(sample_tools)
        assert len(result) == 2

        tool = result[0]
        assert tool["type"] == "function"
        assert tool["name"] == "check_weather"
        assert tool["description"] == "Get current weather for a city"
        assert "title" not in tool["parameters"]

    def test_strips_titles_from_parameters(self, sample_tools):
        result = mcp_to_openai(sample_tools)
        params = result[0]["parameters"]
        assert "title" not in params
        assert "title" not in params["properties"]["city"]

    def test_handles_empty_schema(self):
        tool = MockTool("empty", "An empty tool", None)
        result = mcp_to_openai([tool])
        assert result[0]["parameters"] == {}


class TestMCPToGemini:
    def test_converts_tools(self, sample_tools):
        result = mcp_to_gemini(sample_tools)
        assert len(result) == 2

        decl = result[0]
        assert decl["name"] == "check_weather"
        assert decl["description"] == "Get current weather for a city"
        assert decl["parameters"]["type"] == "OBJECT"
        assert "city" in decl["parameters"]["properties"]

    def test_gemini_property_types(self, sample_tools):
        result = mcp_to_gemini(sample_tools)
        city_prop = result[0]["parameters"]["properties"]["city"]
        assert city_prop["type"] == "STRING"

        days_prop = result[1]["parameters"]["properties"]["days"]
        assert days_prop["type"] == "INTEGER"

    def test_handles_empty_schema(self):
        tool = MockTool("empty", "No params", None)
        result = mcp_to_gemini([tool])
        assert result[0]["parameters"] is None


class TestMCPToAnthropic:
    def test_converts_tools(self, sample_tools):
        result = mcp_to_anthropic(sample_tools)
        assert len(result) == 2

        tool = result[0]
        assert tool["name"] == "check_weather"
        assert tool["description"] == "Get current weather for a city"
        assert "input_schema" in tool
        assert "title" not in tool["input_schema"]

    def test_handles_empty_schema(self):
        tool = MockTool("empty", "No params", None)
        result = mcp_to_anthropic([tool])
        assert result[0]["input_schema"] == {"type": "object", "properties": {}}
