## LangChain MCP Adapters

In [01-mcp-basics](../01-mcp-basics/) we built a custom MCP client from scratch — manually converting tool schemas, handling function calls, and managing the agentic loop.

This folder shows a **much simpler approach** using **LangChain MCP Adapters**. The adapter handles all the glue code for us.

---

### What Changed vs 01-mcp-basics

| Aspect | 01-mcp-basics (raw SDK) | 02-langchain-adapters |
|--------|------------------------|-----------------------|
| Tool conversion | Manual `convert_mcp_tools_to_openai()` | `load_mcp_tools(session)` — one line |
| Agentic loop | Manual while loop checking for tool calls | `create_agent()` handles everything |
| Tool execution | Manual `session.call_tool()` + result parsing | Agent calls tools automatically |
| Lines of code | ~240 lines | ~80 lines |

---

### How It Works

```
User query → LangChain React Agent → (tool call?) → MCP Server → Agent → Final answer
```

1. Connect to the MCP server via STDIO
2. `load_mcp_tools(session)` — discovers and converts MCP tools to LangChain format
3. `create_agent(llm, tools)` — creates an agent that can reason and call tools
4. `agent.ainvoke({"messages": query})` — runs the full reasoning + tool execution loop

---

### How to Run

> All commands run from the **repo root**. Requires `OPENAI_API_KEY` in your `.env` file.

#### Install langchain dependencies

```bash
uv sync --extra langchain
```

#### Run the client (connects to the terminal server from 01-mcp-basics)

```bash
uv run python learning/02-langchain-adapters/openai_client.py learning/01-mcp-basics/server/main.py
```

#### Example Session

```
MCP Client Started! Type 'quit' to exit.

Query: List files in the workspace

Response:
{
  "messages": [
    {"type": "HumanMessage", "content": "List files in the workspace"},
    {"type": "AIMessage", "content": ""},
    {"type": "ToolMessage", "content": "..."},
    {"type": "AIMessage", "content": "The workspace is currently empty."}
  ]
}

Query: Create a file called demo.txt with "LangChain + MCP"

Response:
{
  "messages": [
    {"type": "HumanMessage", "content": "Create a file called demo.txt with \"LangChain + MCP\""},
    {"type": "AIMessage", "content": ""},
    {"type": "ToolMessage", "content": ""},
    {"type": "AIMessage", "content": "Done! I created demo.txt with the content \"LangChain + MCP\"."}
  ]
}

Query: quit
```

> Note: The response is the full LangGraph message history (JSON), not just the final text. The last `AIMessage` contains the final answer.

---

### Key Components

| Component | What it does |
|-----------|-------------|
| `load_mcp_tools(session)` | Discovers MCP tools and converts them to LangChain-compatible tools |
| `create_agent(llm, tools)` | Creates a ReAct agent that reasons, acts, observes in a loop |
| `agent.ainvoke({"messages": query})` | Runs the agent — handles tool calls automatically |
| `ChatOpenAI` | LangChain wrapper for OpenAI models |

---

### Why Use LangChain with MCP

- **No manual tool format conversion** — adapters handle it automatically
- **No manual agentic loop** — the ReAct agent decides when to call tools
- **Easy to swap LLMs** — change `ChatOpenAI` to `ChatGoogleGenerativeAI` and it still works
- **Extensible** — can add memory, routing, or multi-agent workflows later

---

### Gemini Client

`gemini_client.py` is included for reference. Same pattern but uses `ChatGoogleGenerativeAI` instead of `ChatOpenAI`. Requires a `GOOGLE_API_KEY` in your `.env` file.
