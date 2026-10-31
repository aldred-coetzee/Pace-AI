"""Configuration loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


def _find_env_file() -> Path | None:
    """Walk up from cwd or package directory looking for .env."""
    roots = [Path.cwd(), Path(__file__).resolve().parent]
    for base in roots:
        for directory in [base, *base.parents]:
            env_path = directory / ".env"
            if env_path.exists():
                return env_path
    return None


@dataclass(frozen=True)
class Settings:
    email: str
    password: str
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
            garth_home=os.environ.get("GARTH_HOME", "~/.garth"),
        )
