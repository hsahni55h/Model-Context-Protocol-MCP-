"""Tests for mcp_toolkit.config"""

import json
import pytest
from pathlib import Path

from mcp_toolkit.config import (
    MCPServerConfig,
    MCPConfig,
    load_config,
    load_config_from_dict,
    _parse_config,
)


class TestMCPServerConfig:
    def test_stdio_transport(self):
        cfg = MCPServerConfig(name="test", command="python", args=["server.py"])
        assert cfg.transport == "stdio"

    def test_sse_transport(self):
        cfg = MCPServerConfig(name="test", url="http://localhost:8000/sse")
        assert cfg.transport == "sse"

    def test_validate_no_command_or_url(self):
        cfg = MCPServerConfig(name="test")
        with pytest.raises(ValueError, match="must specify either"):
            cfg.validate()

    def test_validate_both_command_and_url(self):
        cfg = MCPServerConfig(name="test", command="python", url="http://localhost")
        with pytest.raises(ValueError, match="cannot specify both"):
            cfg.validate()

    def test_validate_valid_stdio(self):
        cfg = MCPServerConfig(name="test", command="python", args=["server.py"])
        cfg.validate()  # Should not raise

    def test_validate_valid_sse(self):
        cfg = MCPServerConfig(name="test", url="http://localhost:8000/sse")
        cfg.validate()  # Should not raise


class TestParseConfig:
    def test_standard_format(self):
        data = {
            "mcpServers": {
                "weather": {"command": "python", "args": ["weather_server.py"]},
                "math": {"command": "node", "args": ["math_server.js"]},
            }
        }
        config = _parse_config(data)
        assert len(config.servers) == 2
        assert "weather" in config.servers
        assert config.servers["weather"].command == "python"
        assert config.servers["math"].args == ["math_server.js"]

    def test_simplified_format(self):
        data = {
            "weather": {"command": "python", "args": ["weather_server.py"]},
        }
        config = _parse_config(data)
        assert "weather" in config.servers

    def test_sse_server(self):
        data = {
            "mcpServers": {
                "remote": {"url": "http://example.com/sse"},
            }
        }
        config = _parse_config(data)
        assert config.servers["remote"].transport == "sse"

    def test_empty_config_raises(self):
        with pytest.raises(ValueError, match="No valid server"):
            _parse_config({})

    def test_server_names(self):
        data = {
            "mcpServers": {
                "a": {"command": "python", "args": ["a.py"]},
                "b": {"command": "python", "args": ["b.py"]},
            }
        }
        config = _parse_config(data)
        assert set(config.server_names()) == {"a", "b"}


class TestLoadConfig:
    def test_load_from_file(self, tmp_path):
        config_file = tmp_path / "test_config.json"
        config_file.write_text(json.dumps({
            "mcpServers": {
                "test": {"command": "python", "args": ["test.py"]},
            }
        }))
        config = load_config(str(config_file))
        assert "test" in config.servers

    def test_load_from_env(self, tmp_path, monkeypatch):
        config_file = tmp_path / "env_config.json"
        config_file.write_text(json.dumps({
            "mcpServers": {
                "env_server": {"command": "python", "args": ["env.py"]},
            }
        }))
        monkeypatch.setenv("MCP_CONFIG", str(config_file))
        config = load_config()
        assert "env_server" in config.servers

    def test_file_not_found(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv("MCP_CONFIG", raising=False)
        with pytest.raises(FileNotFoundError):
            load_config()


class TestLoadConfigFromDict:
    def test_basic(self):
        config = load_config_from_dict({
            "mcpServers": {
                "my_server": {"command": "python", "args": ["server.py"]},
            }
        })
        assert config.servers["my_server"].command == "python"
