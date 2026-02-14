"""E2E tests for strava-mcp server startup.

These tests actually boot the server and verify it responds to HTTP.
They catch issues that unit/integration tests miss (bad kwargs, import errors, etc).
"""

from __future__ import annotations

import socket
import subprocess
import sys
import time

import httpx


def _find_free_port() -> int:
    """Find a free port on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _wait_for_server(port: int, timeout: float = 10.0) -> bool:
    """Wait for a server to start accepting connections."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.5):
                return True
        except OSError:
            time.sleep(0.2)
    return False


class TestServerStartupE2E:
    def test_strava_mcp_boots_and_responds(self):
        """Start strava-mcp as a subprocess and verify it serves HTTP."""
        port = _find_free_port()
        env = {
            "STRAVA_CLIENT_ID": "test_id",
            "STRAVA_CLIENT_SECRET": "test_secret",
            "STRAVA_MCP_PORT": str(port),
            "STRAVA_MCP_DB": ":memory:",
            "PATH": "",
        }
        # Merge with current env for Python path
        import os

        full_env = {**os.environ, **env}

        proc = subprocess.Popen(
            [sys.executable, "-m", "strava_mcp.server"],
            env=full_env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        try:
            # Wait for server to start
            started = _wait_for_server(port, timeout=10.0)
            assert started, f"strava-mcp failed to start on port {port}"

            # Verify MCP endpoint responds
            resp = httpx.get(f"http://127.0.0.1:{port}/mcp", timeout=5.0)
            # MCP streamable-http endpoint should respond (405 for GET is fine — it expects POST)
            assert resp.status_code in (200, 405, 406), f"Unexpected status: {resp.status_code}"
        finally:
            proc.terminate()
            proc.wait(timeout=5)
