Purpose of This Client

This Python client connects to an MCP (Model Context Protocol) server and allows an OpenAI model to:

- Understand user requests

- Decide when a tool (function) should be called

- Execute MCP tools (like terminal commands)

- Use the tool results to generate a final response

In simple terms:

User → OpenAI → (Tool call if needed) → MCP Server → OpenAI → Final Answer


High-Level Flow

1. User types a query
2. Client sends query + tool definitions to OpenAI
3. OpenAI may request a tool call
4. Client executes the tool via MCP
5. Tool output is sent back to OpenAI
6. OpenAI returns the final response
7. Client prints the response
This repeats until no more tool calls are needed