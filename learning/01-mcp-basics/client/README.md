## Purpose of This Client

This Python client connects to an **MCP (Model Context Protocol) server** and allows an **OpenAI model** to:

- Understand user requests  
- Decide when a tool (function) should be called  
- Execute MCP tools (such as terminal commands)  
- Use the tool results to generate a final response  

### In Simple Terms

User → OpenAI → (Tool call if needed) → MCP Server → OpenAI → Final Answer


---

## High-Level Flow

1. The user types a query  
2. The client sends the query and tool definitions to OpenAI  
3. OpenAI may request a tool call  
4. The client executes the tool via MCP  
5. The tool output is sent back to OpenAI  
6. OpenAI generates the final response  
7. The client prints the response  

This process repeats until no more tool calls are needed.
