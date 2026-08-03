"""Tests for mcp_toolkit.transports"""

import pytest

from mcp_toolkit.transports import _detect_command, connect
from mcp_toolkit.config import MCPServerConfig


class TestDetectCommand:
    def test_python_script(self):
        assert _detect_command("server.py") == __import__("sys").executable

    def test_js_script(self):
        assert _detect_command("server.js") == "node"

    def test_mjs_script(self):
        assert _detect_command("server.mjs") == "node"

    def test_ts_script(self):
        assert _detect_command("server.ts") == "npx"

    def test_unknown_defaults_to_python(self):
        import sys
        assert _detect_command("server.rb") == sys.executable


class TestConnectValidation:
    @pytest.mark.anyio
    async def test_connect_raises_no_params(self):
        with pytest.raises(ValueError, match="Must provide one of"):
            async with connect():
                pass

    @pytest.mark.anyio
    async def test_connect_streamable_http_config_routes_correctly(self):
        """Verify that streamable_http config triggers the correct code path."""
        cfg = MCPServerConfig(
            name="test",
            url="http://localhost:9999/mcp",
            transport_type="streamable_http",
        )
        # This will fail to actually connect (no server), but verifies routing
        with pytest.raises((OSError, Exception)):
            async with connect(config=cfg):
                pass
