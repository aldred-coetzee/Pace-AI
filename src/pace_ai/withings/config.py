"""Configuration loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass

from pace_ai.workspace import load_config, resolve_in_workspace


@dataclass(frozen=True)
class Settings:
    config_folder: str = ""

    @classmethod
    def from_env(cls) -> Settings:
        load_config()

        return cls(
            config_folder=resolve_in_workspace(os.environ.get("WITHINGS_CONFIG_FOLDER") or "withings"),
        )
