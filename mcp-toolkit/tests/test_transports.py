"""Tests for mcp_toolkit.transports"""

import pytest

from mcp_toolkit.transports import _detect_command


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
