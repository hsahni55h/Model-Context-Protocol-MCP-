# MCP Client (OpenAI)

This Python client connects to an **MCP server** over STDIO and lets **OpenAI (gpt-4o-mini)** use the server's tools via function calling.

---

## How It Works

```
User query → OpenAI → (tool call?) → MCP Server → OpenAI → Final answer
```

1. User types a query
2. Client sends the query + available tool definitions to OpenAI
3. OpenAI decides whether to call a tool
4. If yes → client executes the tool via MCP and sends the result back
5. OpenAI generates the final response (may call more tools in a loop)
6. Client prints the response

---

## How to Run

> All commands are run from the **repo root**. Requires `OPENAI_API_KEY` in your `.env` file.

### Run the client (connects to the terminal server)

```bash
uv run python learning/01-mcp-basics/client/openai_client.py learning/01-mcp-basics/server/main.py
```

This starts an interactive chat. Type `quit` to exit.

### Example Session

```
MCP Client Started! Type 'quit' to exit.

Query: What files are in the workspace?

[OpenAI requested tool call: run_command args={'command': 'ls'}]

The workspace is currently empty.

Query: Create a file called notes.txt with "MCP is working"

[OpenAI requested tool call: run_command args={'command': 'echo "MCP is working" > notes.txt'}]

Done! I've created notes.txt with the content "MCP is working".

Query: What's in notes.txt?

[OpenAI requested tool call: run_command args={'command': 'cat notes.txt'}]

The file contains: MCP is working

Query: quit
```

---

## Key Code Concepts

| Concept | What it does |
|---------|-------------|
| `StdioServerParameters` | Configures how to launch the MCP server process |
| `ClientSession` | Manages the connection to the MCP server |
| `convert_mcp_tools_to_openai()` | Converts MCP tool schemas to OpenAI function calling format |
| `session.call_tool()` | Executes a tool on the MCP server |
| Agentic loop | Keeps calling tools until OpenAI returns a text response (no more tool calls) |

---

## Gemini Client

`gemini_client.py` is also included for reference. It does the same thing but uses **Google Gemini** instead of OpenAI. Requires a `GEMINI_API_KEY` in your `.env` file.
