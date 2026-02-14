"""Unit tests for server helpers."""

from __future__ import annotations

import inspect

from mcp.server.fastmcp import FastMCP

from strava_mcp.server import _speed_to_pace, main


class TestServerStartup:
    def test_main_calls_run_without_host_port(self):
        """Ensure main() calls mcp.run() without host/port kwargs.

        FastMCP.run() does not accept host/port — those belong on the
        constructor. This test prevents the regression that caused
        TypeError on startup.
        """
        sig = inspect.signature(FastMCP.run)
        params = set(sig.parameters.keys())
        # If run() doesn't accept host/port, our main() must not pass them
        assert "host" not in params or "port" not in params, (
            "If FastMCP.run() accepts host/port, this test needs updating"
        )
        # Verify main() source doesn't pass host= or port= to mcp.run()
        source = inspect.getsource(main)
        assert ", host=" not in source, "main() must not pass host= to mcp.run() — use FastMCP constructor instead"
        assert ", port=" not in source, "main() must not pass port= to mcp.run() — use FastMCP constructor instead"

    def test_mcp_instance_has_custom_port(self):
        """Ensure the FastMCP instance is configured with port 8001."""
        from strava_mcp.server import mcp

        assert mcp.settings.port == 8001


class TestSpeedToPace:
    def test_normal_pace(self):
        # 3.33 m/s ≈ 5:00/km
        result = _speed_to_pace(3.33)
        assert result == "5:00"

    def test_fast_pace(self):
        # 5.0 m/s ≈ 3:20/km
        result = _speed_to_pace(5.0)
        assert result == "3:20"

    def test_slow_pace(self):
        # 2.0 m/s ≈ 8:20/km
        result = _speed_to_pace(2.0)
        assert result == "8:20"

    def test_zero_speed(self):
        assert _speed_to_pace(0) is None

    def test_negative_speed(self):
        assert _speed_to_pace(-1) is None
