"""
MCP Server Configuration

Typed configuration loader for MCP server definitions.
Supports loading from JSON files, environment variables, or programmatic dicts.
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class MCPServerConfig:
    """Configuration for a single MCP server.

    Attributes:
        name: Human-readable server name.
        command: Command to launch the server (e.g. "python", "node", "uv").
        args: Arguments passed to the command.
        env: Optional environment variables for the subprocess.
        url: SSE endpoint URL (mutually exclusive with command).
    """
    name: str = ""
    command: str = ""
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    url: str = ""

    @property
    def transport(self) -> str:
        """Determine transport type from config."""
        if self.url:
            return "sse"
        return "stdio"

    def validate(self) -> None:
        """Validate the configuration.

        Raises:
            ValueError: If configuration is invalid.
        """
        if not self.url and not self.command:
            raise ValueError(
                f"Server '{self.name}': must specify either 'command' (for stdio) or 'url' (for SSE)"
            )
        if self.url and self.command:
            raise ValueError(
                f"Server '{self.name}': cannot specify both 'command' and 'url'"
            )


@dataclass
class MCPConfig:
    """Top-level configuration containing multiple MCP servers.

    Attributes:
        servers: Mapping of server name to its configuration.
    """
    servers: dict[str, MCPServerConfig] = field(default_factory=dict)

    def server_names(self) -> list[str]:
        """Return list of configured server names."""
        return list(self.servers.keys())


def load_config(
    path: str | Path | None = None,
    *,
    env_var: str = "MCP_CONFIG",
) -> MCPConfig:
    """Load MCP server configuration from a JSON file.

    Resolution order:
        1. Explicit `path` argument
        2. Path from the environment variable specified by `env_var`
        3. `mcp_servers.json` in the current directory

    The JSON format matches the standard MCP config convention:
    ```json
    {
      "mcpServers": {
        "server-name": {
          "command": "python",
          "args": ["server.py"]
        }
      }
    }
    ```

    Args:
        path: Explicit path to the config file.
        env_var: Environment variable to check for config path.

    Returns:
        MCPConfig with all server definitions.

    Raises:
        FileNotFoundError: If no config file is found.
        ValueError: If the config format is invalid.
    """
    config_path = _resolve_config_path(path, env_var)
    data = _read_json(config_path)
    return _parse_config(data)


def load_config_from_dict(data: dict[str, Any]) -> MCPConfig:
    """Load MCP configuration from a Python dict.

    Accepts two formats:
        - Standard: {"mcpServers": {"name": {...}}}
        - Simplified: {"name": {"command": "...", "args": [...]}}

    Args:
        data: Configuration dictionary.

    Returns:
        MCPConfig with all server definitions.
    """
    return _parse_config(data)


def _resolve_config_path(path: str | Path | None, env_var: str) -> Path:
    """Resolve config file path from arguments, env, or default."""
    if path:
        resolved = Path(path)
        if not resolved.exists():
            raise FileNotFoundError(f"Config file not found: {resolved}")
        return resolved

    env_path = os.getenv(env_var)
    if env_path:
        resolved = Path(env_path)
        if not resolved.exists():
            raise FileNotFoundError(
                f"Config file from ${env_var} not found: {resolved}"
            )
        return resolved

    default = Path("mcp_servers.json")
    if default.exists():
        return default

    # Try config.json as fallback
    fallback = Path("config.json")
    if fallback.exists():
        return fallback

    raise FileNotFoundError(
        "No MCP config found. Provide a path, set $MCP_CONFIG, "
        "or create mcp_servers.json in the current directory."
    )


def _read_json(path: Path) -> dict:
    """Read and parse a JSON file."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {path}: {e}") from e


def _parse_config(data: dict[str, Any]) -> MCPConfig:
    """Parse a config dict into MCPConfig."""
    # Support standard format: {"mcpServers": {...}}
    servers_data = data.get("mcpServers", data)

    # Filter out non-server keys if using standard format
    if "mcpServers" in data:
        servers_data = data["mcpServers"]

    servers = {}
    for name, info in servers_data.items():
        if not isinstance(info, dict):
            continue
        servers[name] = MCPServerConfig(
            name=name,
            command=info.get("command", ""),
            args=info.get("args", []),
            env=info.get("env", {}),
            url=info.get("url", ""),
        )
        servers[name].validate()

    if not servers:
        raise ValueError("No valid server configurations found in config")

    return MCPConfig(servers=servers)
