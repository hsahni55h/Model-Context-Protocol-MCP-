# MCP Terminal Server

This MCP (Model Context Protocol) server exposes a **terminal execution tool** that allows an AI client (e.g., Cursor, Claude, etc.) to safely run shell commands inside a **controlled workspace directory**.

Instead of running commands anywhere on your system, all commands are forced to execute inside a dedicated `workspace/` folder.

---

## What This Server Exposes

| Component | Details |
|-----------|---------|
| **Tool** | `run_command` — executes a shell command in the workspace |
| **Transport** | STDIO (local, single client) |
| **Framework** | `FastMCP` from the `mcp` Python SDK |

---

## Workspace Directory

All commands run inside `learning/01-mcp-basics/workspace/`. This ensures:

- File operations are isolated from your system
- Outputs are predictable and easy to locate
- Your system remains protected

---

## How to Run

> All commands are run from the **repo root**.

### 1. Test with MCP Inspector (no API key needed)

```bash
uv run mcp dev learning/01-mcp-basics/server/main.py
```

This opens a web UI where you can:
- See the `run_command` tool listed under the **Tools** tab
- Call it with any command and see the output
- Debug inputs/outputs

**Example calls to try in the Inspector:**

| Command input | Expected output |
|---------------|-----------------|
| `pwd` | The absolute path to the `workspace/` folder |
| `echo "hello" > test.txt` | (empty — file created silently) |
| `ls` | `test.txt` |
| `cat test.txt` | `hello` |

### 2. Test with Cursor

Add this to Cursor → Settings → MCP:

```json
{
  "mcpServers": {
    "terminal": {
      "command": "uv",
      "args": [
        "run",
        "--frozen",
        "--with",
        "mcp[cli]",
        "mcp",
        "run",
        "<ABSOLUTE_PATH_TO_REPO>/learning/01-mcp-basics/server/main.py"
      ]
    }
  }
}
```

> Replace `<ABSOLUTE_PATH_TO_REPO>` with the actual path to your cloned repository.

Then ask Cursor to run terminal commands — it will use your MCP server.

---

## Code Walkthrough

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("terminal")          # Create a named MCP server

@mcp.tool()                         # Register a tool
async def run_command(command: str) -> str:
    # Runs the command in the workspace directory
    result = subprocess.run(command, shell=True, cwd=DEFAULT_WORKSPACE, ...)
    return result.stdout or result.stderr

mcp.run(transport="stdio")          # Start the server using STDIO transport
```

**Key concepts:**
- `FastMCP("terminal")` — creates a server with the name "terminal"
- `@mcp.tool()` — decorator that registers a function as an MCP tool
- `mcp.run(transport="stdio")` — starts the server, communicating via standard input/output
