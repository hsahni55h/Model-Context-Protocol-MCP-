# MCP SSE Server – Remote Tool Execution with Streaming

This file implements an **MCP Server using HTTP + SSE (Server-Sent Events)**  
to expose tools that AI clients can call remotely in real time.

Instead of using the local **STDIO transport**, this server runs as a **web service**  
and streams responses to connected clients using SSE.

---

## 🚀 What This Server Does

The server exposes MCP tools such as:

- `run_command(command)` → Executes shell commands in a workspace  
- `add_numbers(a, b)` → Simple example tool  

- **GET /sse** → Opens a streaming SSE connection  
- **POST /messages/** → Sends client requests to the server  

The server responds over the SSE stream. Clients connect over HTTP and receive responses via **SSE streaming**.

This setup is ideal for:

- Remote MCP servers  
- Multi-client access  
- Real-time updates  
- Production-style deployments  




