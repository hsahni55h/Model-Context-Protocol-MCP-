## LangChain + MCP + OpenAI Integration

This client uses **LangChain** and **LangGraph** to connect an **OpenAI model** with an **MCP (Model Context Protocol) server**.

The goal is to allow the AI model to **automatically discover and use MCP tools** (such as terminal commands) when needed.

---

### What We Are Doing

1. We start an MCP server using a stdio connection  
2. We load all available MCP tools using the LangChain MCP adapter  
3. We create a React-style agent using:
   - An OpenAI model (via `ChatOpenAI`)
   - The loaded MCP tools  
4. The agent can now:
   - Understand user queries  
   - Decide when a tool is needed  
   - Call MCP tools automatically  
   - Use the tool output to generate a final response  

---

### Why LangChain MCP Adapters Are Used

We use the **LangChain MCP Adapters** to convert MCP tools into LangChain-compatible tools.

This allows the React agent to call MCP tools without any custom glue code.

Repository used:

https://github.com/langchain-ai/langchain-mcp-adapters

The adapter handles:
- Tool discovery from the MCP server  
- Argument schema conversion  
- Tool invocation via the MCP session  


---

### Key Components

- **ChatOpenAI**  
  OpenAI model wrapper used by LangChain.

- **load_mcp_tools(session)**  
  Loads MCP tools and converts them into LangChain tools.

- **create_react_agent(llm, tools)**  
  Creates a React agent that can reason and call tools.

- **agent.ainvoke(...)**  
  Runs the full reasoning + tool execution loop.

---

### Result

This setup allows the AI to:

- Execute terminal commands  
- Interact with MCP tools  
- Use tool results in its responses  
- Operate in a controlled environment  

---

### Why We Use LangChain with MCP

Using LangChain together with MCP gives us several practical advantages:

- We don’t need to worry about LLM-specific input or tool formats
LangChain + MCP adapters automatically convert MCP tools into the correct format for OpenAI, Gemini, etc.

- We don’t need to manage function call IDs
LangChain handles tool call tracking and response matching internally.

- We can use multiple tools in one workflow
The agent can call different tools step-by-step without manual orchestration.

- The agent decides when and how to use tools
We don’t write custom logic to detect tool calls or execute them.

- Multi-step reasoning is handled automatically
The agent can think, act, observe results, and continue until the task is complete.

- Switching LLM providers is easy
We can move from Gemini to OpenAI (or others) with minimal code changes.

- The system is easy to extend
We can later add memory, routing, or multi-agent workflows without rewriting MCP logic.