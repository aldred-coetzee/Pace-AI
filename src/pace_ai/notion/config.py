"""Configuration loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass

from pace_ai.workspace import load_config, resolve_in_workspace


@dataclass(frozen=True)
class Settings:
    notion_token: str = ""
    diary_database_id: str = ""
    db_path: str = ""

    @classmethod
    def from_env(cls) -> Settings:
        load_config()

        raw_db = resolve_in_workspace(os.environ.get("NOTION_DB") or "notion.db")

        return cls(
            notion_token=os.environ.get("NOTION_TOKEN", ""),
            diary_database_id=os.environ.get("NOTION_DIARY_DATABASE_ID", ""),
            db_path=raw_db,
        )
