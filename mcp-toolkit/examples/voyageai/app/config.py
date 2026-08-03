"""VoyageAI application configuration.

Loads environment variables and provides typed settings for the app.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Project root is the voyageai/ directory
PROJECT_ROOT = Path(__file__).parent.parent
SERVERS_DIR = PROJECT_ROOT / "servers"

# Load .env from project root (voyageai/.env)
load_dotenv(PROJECT_ROOT / ".env")


# Required API keys
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENWEATHER_API_KEY = os.environ.get("OPENWEATHER_API_KEY", "")
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY", "")
AVIATIONSTACK_API_KEY = os.environ.get("AVIATIONSTACK_API_KEY", "")
EXCHANGE_RATE_API_KEY = os.environ.get("EXCHANGE_RATE_API_KEY", "")

# OpenAI model
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

# MCP server config path
MCP_CONFIG_PATH = Path(__file__).parent / "mcp_servers.json"

# Python executable (for spawning server subprocesses)
PYTHON_PATH = sys.executable


def get_mcp_config() -> dict:
    """Load and resolve the MCP server config with actual env vars."""
    import json

    with open(MCP_CONFIG_PATH) as f:
        config = json.load(f)

    # Resolve ${VAR} placeholders in env blocks and url fields
    for server_cfg in config.get("mcpServers", {}).values():
        if "env" in server_cfg:
            resolved_env = {}
            for key, val in server_cfg["env"].items():
                if val.startswith("${") and val.endswith("}"):
                    env_var = val[2:-1]
                    resolved_env[key] = os.environ.get(env_var, "")
                else:
                    resolved_env[key] = val
            server_cfg["env"] = resolved_env

        # Resolve ${VAR} placeholders in URL
        if "url" in server_cfg:
            import re
            server_cfg["url"] = re.sub(
                r"\$\{(\w+)\}",
                lambda m: os.environ.get(m.group(1), ""),
                server_cfg["url"],
            )

        # Resolve command to absolute python path for stdio servers
        if server_cfg.get("command") == "python":
            server_cfg["command"] = PYTHON_PATH

        # Resolve relative args paths to absolute
        if "args" in server_cfg:
            server_cfg["args"] = [
                str(PROJECT_ROOT / arg) if not Path(arg).is_absolute() else arg
                for arg in server_cfg["args"]
            ]

    return config
