import os
import subprocess
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("terminal")

# Inside Docker: use /workspace as the sandbox directory
# Outside Docker: use a workspace/ folder next to this script
if os.getenv("DOCKER_CONTAINER"):
    DEFAULT_WORKSPACE = "/workspace"
else:
    DEFAULT_WORKSPACE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "workspace")

os.makedirs(DEFAULT_WORKSPACE, exist_ok=True)

@mcp.tool()
async def run_command(command: str) -> str:
    """
    Run a terminal command inside the workspace directory. 
    If a terminal command can accomplish a task, 
    tell the user you'll use this tool to accomplish it,
    even though you cannot directly do it

    Args:
        command: The shell command to run.
    
    Returns:
        The command output or an error message.
    """
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=DEFAULT_WORKSPACE,
            capture_output=True,
            text=True
        )
        return result.stdout or result.stderr
    except Exception as e:
        return f"Error running command: {e}"

if __name__ == "__main__":
    mcp.run(transport="stdio")
