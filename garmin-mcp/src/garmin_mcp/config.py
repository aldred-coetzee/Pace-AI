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
        msg = f"GARMIN_MCP_PORT must be a number, got: {value!r}"
        raise ValueError(msg) from None


@dataclass(frozen=True)
class Settings:
    email: str
    password: str
    host: str = "127.0.0.1"
    port: int = 8003
    garth_home: str = "~/.garth"

    @classmethod
    def from_env(cls) -> Settings:
        env_file = _find_env_file()
        if env_file:
            load_dotenv(env_file)

        email = os.environ.get("GARMIN_EMAIL", "")
        password = os.environ.get("GARMIN_PASSWORD", "")

        if not email or not password:
            msg = "GARMIN_EMAIL and GARMIN_PASSWORD must be set"
            raise ValueError(msg)

        return cls(
            email=email,
            password=password,
            host=os.environ.get("GARMIN_MCP_HOST", "127.0.0.1"),
            port=_parse_port(os.environ.get("GARMIN_MCP_PORT", "8003")),
            garth_home=os.environ.get("GARTH_HOME", "~/.garth"),
        )
