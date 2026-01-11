# LangChain MCP Client (OpenAI + Multi-Server Support)

This project implements a **LangChain-based MCP (Model Context Protocol) client** that can connect to **multiple MCP servers**, load their tools, and use an **OpenAI model** to reason, call tools, and respond to user queries.

It allows an AI agent to:

- Discover tools exposed by MCP servers  
- Decide when a tool is needed  
- Execute the tool automatically  
- Use the tool output to generate a final answer  

---

## What This Client Does

The file `langchain_mcp_client_wconfig_openai.py`:

- Loads MCP server configuration from a JSON file  
- Connects to one or more MCP servers via **stdio**  
- Loads tools from each server  
- Uses **OpenAI (via LangChain)** to create a React-style agent  
- Runs an interactive chat loop for user queries  

---



## Why LangChain Is Used

LangChain simplifies MCP + LLM integration by:

- Converting MCP tools into LLM-compatible tools  
- Handling tool-call formats automatically  
- Managing multi-step reasoning and tool usage  
- Removing the need to track call IDs manually  
- Allowing multiple tools from multiple servers  
- Making it easy to switch LLM providers  

Without LangChain, you would need to manually manage:
- Tool schemas  
- Message formats  
- Function call tracking  
- Multi-step reasoning  

---

## Configuration File (config.json)

Your MCP servers are defined in a JSON file:

```json
{
  "preferences": {},
  "mcpServers": {
    "terminal_docker": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "--init",
        "-e",
        "DOCKER_CONTAINER=true",
        "-v",
        "/Users/himanshu/github_himanshu/Model-Context-Protocol-MCP-/mcp/workspace:/root/mcp/workspace",
        "terminal_server_docker"
      ]
    },
    "fetch": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "mcp_fetch_server_test"
      ]
    }
  }
}
