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
    config_folder: str = ""

    @classmethod
    def from_env(cls) -> Settings:
        env_file = _find_env_file()
        if env_file:
            load_dotenv(env_file)

        return cls(
            config_folder=os.environ.get("WITHINGS_CONFIG_FOLDER", ""),
        )
