"""Configuration for pace-ai."""

from __future__ import annotations

import os
from dataclasses import dataclass

from pace_ai.workspace import load_config, resolve_in_workspace


@dataclass(frozen=True)
class Settings:
    db_path: str = ""

    @classmethod
    def from_env(cls) -> Settings:
        load_config()
        return cls(
            db_path=resolve_in_workspace(os.environ.get("PACE_AI_DB") or "pace_ai.db"),
        )
