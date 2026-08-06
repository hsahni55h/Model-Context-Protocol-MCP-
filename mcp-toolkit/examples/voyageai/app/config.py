"""VoyageAI application configuration.

Loads environment variables and provides typed settings for the app.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

from mcp_toolkit.config import load_config, MCPConfig

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


def get_mcp_config() -> MCPConfig:
    """Load and resolve the MCP server config.

    Uses mcp_toolkit.config.load_config() which handles ${VAR} placeholder
    resolution automatically. Additionally resolves the Python executable path
    and converts relative server script paths to absolute.

    Returns:
        MCPConfig ready to pass directly to MultiServerClient.
    """
    config = load_config(MCP_CONFIG_PATH)

    for server_cfg in config.servers.values():
        # Resolve 'python' to the current interpreter's absolute path
        if server_cfg.command == "python":
            server_cfg.command = PYTHON_PATH

        # Make relative script paths absolute (relative to voyageai/ root)
        server_cfg.args = [
            str(PROJECT_ROOT / arg) if not Path(arg).is_absolute() else arg
            for arg in server_cfg.args
        ]

    return config


def validate_config() -> None:
    """Raise RuntimeError if any required API keys are missing.

    Call this at application startup to surface configuration errors
    immediately rather than mid-request.
    """
    required = {
        "OPENAI_API_KEY": OPENAI_API_KEY,
        "OPENWEATHER_API_KEY": OPENWEATHER_API_KEY,
        "TAVILY_API_KEY": TAVILY_API_KEY,
        "AVIATIONSTACK_API_KEY": AVIATIONSTACK_API_KEY,
        "EXCHANGE_RATE_API_KEY": EXCHANGE_RATE_API_KEY,
    }
    missing = [k for k, v in required.items() if not v]
    if missing:
        raise RuntimeError(
            f"Missing required API keys: {', '.join(missing)}. "
            "Add them to your .env file."
        )
