"""Unit tests for pace-ai server startup."""

from __future__ import annotations

import inspect

from mcp.server.fastmcp import FastMCP


class TestServerStartup:
    def test_main_calls_run_without_host_port(self):
        """Ensure main() calls mcp.run() without host/port kwargs.

        FastMCP.run() does not accept host/port — those belong on the
        constructor. This test prevents the regression that caused
        TypeError on startup.
        """
        from pace_ai.server import main

        sig = inspect.signature(FastMCP.run)
        params = set(sig.parameters.keys())
        assert "host" not in params or "port" not in params, (
            "If FastMCP.run() accepts host/port, this test needs updating"
        )
        source = inspect.getsource(main)
        assert ", host=" not in source, "main() must not pass host= to mcp.run() — use FastMCP constructor instead"
        assert ", port=" not in source, "main() must not pass port= to mcp.run() — use FastMCP constructor instead"

    def test_mcp_instance_has_custom_port(self):
        """Ensure the FastMCP instance is configured with port 8002."""
        from pace_ai.server import mcp
        assert mcp.settings.port == 8002
