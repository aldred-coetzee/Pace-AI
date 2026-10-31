"""Configuration for pace-ai."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    db_path: str = "pace_ai.db"

    @classmethod
    def from_env(cls) -> Settings:
        return cls(
            db_path=os.environ.get("PACE_AI_DB", "pace_ai.db"),
        )
