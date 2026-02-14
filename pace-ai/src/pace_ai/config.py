"""Configuration for pace-ai server."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    host: str = "127.0.0.1"
    port: int = 8002
    db_path: str = "pace_ai.db"

    @classmethod
    def from_env(cls) -> Settings:
        return cls(
            host=os.environ.get("PACE_AI_HOST", "127.0.0.1"),
            port=int(os.environ.get("PACE_AI_PORT", "8002")),
            db_path=os.environ.get("PACE_AI_DB", "pace_ai.db"),
        )
