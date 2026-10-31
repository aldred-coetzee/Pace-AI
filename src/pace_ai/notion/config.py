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
    notion_token: str = ""
    diary_database_id: str = ""
    db_path: str = "notion_mcp.db"

    @classmethod
    def from_env(cls) -> Settings:
        env_file = _find_env_file()
        if env_file:
            load_dotenv(env_file)

        raw_db = os.environ.get("NOTION_MCP_DB", "notion_mcp.db")
        if not os.path.isabs(raw_db) and env_file is not None:
            raw_db = str(env_file.parent / raw_db)

        return cls(
            notion_token=os.environ.get("NOTION_TOKEN", ""),
            diary_database_id=os.environ.get("NOTION_DIARY_DATABASE_ID", ""),
            db_path=raw_db,
        )
