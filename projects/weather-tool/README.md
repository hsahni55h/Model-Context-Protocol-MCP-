# Weather MCP Tool 🌦️

This is a simple **Model Context Protocol (MCP)** tool that fetches real-time weather
information for any city using the `wttr.in` service.

It exposes a `check_weather` tool that can be used by MCP clients like **Cursor**,
Claude Desktop, or custom agents.

---

## What This Project Does

- Takes a **city name** as input  
- Fetches current weather data from `wttr.in`  
- Returns a short, readable weather summary  
- Works as an MCP server using **stdio transport**


---

### `tools/weather.py`
Contains the actual Python function that calls the weather API.

### `main.py`
Registers the function as an MCP tool and runs the MCP server.

---

## How It Works

1. The MCP server starts using `mcp run main.py`
2. The `check_weather` tool is registered
3. An MCP client calls the tool with a city name
4. The tool fetches weather data and returns the result

---

## Running Locally (Dev Mode)

You can test the tool using the MCP inspector:

```bash
mcp dev main.py
