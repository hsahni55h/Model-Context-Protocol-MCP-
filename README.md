# Model Context Protocol (MCP) – Learning & Projects Repository

This repository contains multiple hands-on projects built using the  
**Model Context Protocol (MCP)** — an open standard that enables AI models  
to interact with external tools, data sources, and services in a structured way.

Official MCP Documentation:  
https://modelcontextprotocol.io/docs/getting-started/intro  

This repo is designed to help developers understand:

- What MCP is  
- How MCP works  
- MCP architecture  
- MCP components  
- How to build MCP servers  
- How to connect AI models to tools  

---

## 🔍 What is MCP?

**Model Context Protocol (MCP)** is an open-source standard that allows AI applications  
to connect with external systems such as APIs, databases, tools, and files  
through a unified interface.

It is often described as:

> **“USB-C for AI applications”**

Just like USB-C standardizes how devices connect to hardware,  
MCP standardizes how AI models connect to tools and data sources.

With MCP, AI systems can:

- Call external tools  
- Access structured resources  
- Use predefined prompts  
- Work across different environments  

Official intro:  
https://modelcontextprotocol.io/docs/getting-started/intro  

---

## 🏗️ MCP Architecture

MCP follows a **Client–Server architecture**.


### Communication Flow

1. User asks a question  
2. AI model decides it needs external data  
3. MCP Client sends a request  
4. MCP Server runs the tool  
5. Result is returned  
6. AI generates final response  

Official architecture docs:  
https://modelcontextprotocol.io/docs/learn/architecture

---

## 🧠 Core MCP Concepts

MCP follows a client-server architecture where an MCP host — an AI application like Claude Code or Claude Desktop — establishes connections to one or more MCP servers. The MCP host accomplishes this by creating one MCP client for each MCP server. Each MCP client maintains a dedicated connection with its corresponding MCP server.

Local MCP servers that use the STDIO transport typically serve a single MCP client, whereas remote MCP servers that use the Streamable HTTP transport will typically serve many MCP clients.

The key participants in the MCP architecture are:

### 1. MCP Host  
The **Host** is the AI application the user interacts with. The AI application that coordinates and manages one or multiple MCP clients.

Examples:
- Cursor IDE  
- Claude Desktop  
- Custom AI apps  

The host:
- Runs the AI model  
- Manages user interaction  
- Decides when to call MCP tools  

---

### 2. MCP Client  
An **MCP Client** is created by the host to connect to an MCP server. A component that maintains a connection to an MCP server and obtains context from an MCP server for the MCP host to use

Key points:
- One client per server  
- Handles communication  
- Sends tool requests  
- Receives results  

A host can run **multiple MCP clients** at the same time.
 
---

### 3. MCP Server  
An **MCP Server** exposes capabilities to AI models. A program that provides context to MCP clients

It can provide:
- **Tools** → executable functions  
- **Resources** → read-only data  
- **Prompts** → reusable workflows  

Each server focuses on a specific capability  
(e.g., weather, jobs, medical research, content creation).
 

---

### MCP Transports
1. STDIO Transport (Local)
- Runs on your machine
- Serves a single client
- Used for development tools
Example:
Terminal MCP server
Weather MCP server

2. HTTP Transport (Remote)
- Runs on a server
- Can serve many clients
- Used for production setup

---

### Testing MCP Servers
To test any MCP server in this repository:

> **uv run mcp dev mcp_server.py**

This opens the MCP Inspector, where you can:
- Call tools
- View inputs/outputs
- Debug workflows