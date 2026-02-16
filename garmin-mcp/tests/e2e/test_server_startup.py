"""E2E tests for garmin-mcp server startup.

These tests actually boot the server and verify it responds to HTTP.
They catch issues that unit/integration tests miss (bad kwargs, import errors, etc).
"""

from __future__ import annotations

import os
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
    def test_garmin_mcp_boots_and_responds(self):
        """Start garmin-mcp as a subprocess and verify it serves HTTP."""
        port = _find_free_port()
        env = {
            "GARMIN_EMAIL": "test@example.com",
            "GARMIN_PASSWORD": "test_password",
            "GARMIN_MCP_PORT": str(port),
            "GARTH_HOME": "/tmp/test_garth_e2e",
            "PATH": "",
        }
        full_env = {**os.environ, **env}

        proc = subprocess.Popen(
            [sys.executable, "-m", "garmin_mcp.server"],
            env=full_env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        try:
            started = _wait_for_server(port, timeout=10.0)
            assert started, f"garmin-mcp failed to start on port {port}"

            # Verify MCP endpoint responds
            resp = httpx.get(f"http://127.0.0.1:{port}/mcp", timeout=5.0)
            # MCP streamable-http endpoint should respond (405 for GET is fine — it expects POST)
            assert resp.status_code in (200, 405, 406), f"Unexpected status: {resp.status_code}"
        finally:
            proc.terminate()
            proc.wait(timeout=5)
