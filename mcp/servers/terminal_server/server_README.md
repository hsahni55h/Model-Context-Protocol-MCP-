# MCP Terminal Server

This MCP (Model Context Protocol) server exposes a **terminal execution tool** that allows an AI client (e.g., Cursor, Claude, etc.) to safely run shell commands inside a **controlled workspace directory**.

Instead of running commands anywhere on your system, all commands are forced to execute inside a dedicated workspace.

---

## Workspace Directory

Any files created using the MCP terminal tool will be placed inside this directory.

This ensures:

- File operations are isolated  
- Outputs are predictable  
- Your system remains protected  
- Generated files are easy to locate  

---

## How to Run the Server

The MCP terminal server is launched using a JSON configuration file.

You can add this configuration in:

- **Cursor** → Settings → MCP  
- **Claude Desktop** → Connectors / MCP settings  

---

## MCP Server Configuration

```json
{
  "preferences": {},
  "mcpServers": {
    "terminal": {
      "command": "/opt/homebrew/bin/uv",
      "args": [
        "run",
        "--frozen",
        "--with",
        "mcp[cli]",
        "mcp",
        "run",
        "/Users/himanshu/github_himanshu/Model-Context-Protocol-MCP-/mcp/servers/terminal_server/main.py"
      ]
    }
  }
}
