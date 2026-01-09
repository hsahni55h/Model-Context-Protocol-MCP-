This MCP (Model Context Protocol) server exposes a terminal execution tool that allows an AI client (e.g., Cursor, Claude, etc.) to safely run shell commands inside a controlled workspace directory.

Instead of running commands anywhere on your system, all commands are forced to execute inside the current working directory.

The workspace directory is automatically created at:

/mcp/workspace

Any files created using the MCP terminal tool should be placed there.

How to run the server



The server is launched using the following JSON config (add this by going into cursor settings for MCP and same for the claude connectors):

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