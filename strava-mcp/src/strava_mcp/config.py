"""Configuration loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


def _find_env_file() -> Path | None:
    """Walk up from cwd looking for .env."""
    current = Path.cwd()
    for directory in [current, *current.parents]:
        env_path = directory / ".env"
        if env_path.exists():
            return env_path
    return None


def _parse_port(value: str) -> int:
    try:
        return int(value)
    except ValueError:
        msg = f"STRAVA_MCP_PORT must be a number, got: {value!r}"
        raise ValueError(msg) from None


@dataclass(frozen=True)
class Settings:
    client_id: str
    client_secret: str
    access_token: str | None = None
    refresh_token: str | None = None
    host: str = "127.0.0.1"
    port: int = 8001
    db_path: str = "strava_mcp.db"

    @classmethod
    def from_env(cls) -> Settings:
        env_file = _find_env_file()
        if env_file:
            load_dotenv(env_file)

        client_id = os.environ.get("STRAVA_CLIENT_ID", "")
        client_secret = os.environ.get("STRAVA_CLIENT_SECRET", "")

        if not client_id or not client_secret:
            msg = "STRAVA_CLIENT_ID and STRAVA_CLIENT_SECRET must be set"
            raise ValueError(msg)

        return cls(
            client_id=client_id,
            client_secret=client_secret,
            access_token=os.environ.get("STRAVA_ACCESS_TOKEN"),
            refresh_token=os.environ.get("STRAVA_REFRESH_TOKEN"),
            host=os.environ.get("STRAVA_MCP_HOST", "127.0.0.1"),
            port=_parse_port(os.environ.get("STRAVA_MCP_PORT", "8001")),
            db_path=os.environ.get("STRAVA_MCP_DB", "strava_mcp.db"),
        )
