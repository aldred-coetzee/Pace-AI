"""Garmin Connect authentication via garth SSO."""

from __future__ import annotations

import sys
from pathlib import Path

import garth


class GarminAuth:
    """Manages Garmin Connect authentication using garth SSO tokens."""

    def __init__(self, garth_home: str = "~/.garth") -> None:
        self._garth_home = str(Path(garth_home).expanduser())

    def resume(self) -> bool:
        """Try to resume a saved garth session. Returns True if successful."""
        try:
            garth.resume(self._garth_home)
            # Verify the session is still valid by accessing the username
            _ = garth.client.username
            return True
        except Exception:
            return False

    def login(self, email: str, password: str, *, prompt_mfa: bool = True) -> None:
        """Perform interactive SSO login. May prompt for MFA on stdin."""
        garth.login(email, password, prompt_mfa=prompt_mfa)
        garth.save(self._garth_home)


def login_cli() -> None:
    """CLI entry point: authenticate to Garmin Connect and save session.

    Registered as `garmin-mcp-login` console script in pyproject.toml.
    Handles MFA prompts interactively via stdin.
    """
    from garmin_mcp.config import Settings

    try:
        settings = Settings.from_env()
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        print("Set GARMIN_EMAIL and GARMIN_PASSWORD in your .env file.", file=sys.stderr)
        sys.exit(1)

    auth = GarminAuth(settings.garth_home)

    # Try resuming first
    if auth.resume():
        print("Already authenticated (session resumed).")
        return

    print(f"Logging in as {settings.email}...")
    try:
        auth.login(settings.email, settings.password)
        print("Login successful. Session saved.")
    except Exception as e:
        print(f"Login failed: {e}", file=sys.stderr)
        sys.exit(1)
