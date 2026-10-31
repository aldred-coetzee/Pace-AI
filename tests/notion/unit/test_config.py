"""Unit tests for config module."""

from __future__ import annotations

import pytest

from pace_ai.notion.config import Settings


class TestSettings:
    def test_from_env_defaults(self):
        s = Settings.from_env()
        # db_path is resolved to absolute path relative to .env location
        assert s.db_path.endswith("notion_mcp.db")

    def test_from_env_token(self, monkeypatch):
        monkeypatch.setenv("NOTION_TOKEN", "ntn_test123")
        s = Settings.from_env()
        assert s.notion_token == "ntn_test123"

    def test_from_env_database_id(self, monkeypatch):
        monkeypatch.setenv("NOTION_DIARY_DATABASE_ID", "abc-123")
        s = Settings.from_env()
        assert s.diary_database_id == "abc-123"

    def test_from_env_db_path(self, monkeypatch):
        monkeypatch.setenv("NOTION_MCP_DB", "/tmp/test.db")
        s = Settings.from_env()
        assert s.db_path == "/tmp/test.db"

    def test_frozen(self):
        s = Settings()
        with pytest.raises(AttributeError):
            s.notion_token = "x"  # type: ignore[misc]

    def test_defaults(self):
        s = Settings()
        assert s.notion_token == ""
        assert s.diary_database_id == ""
        assert s.db_path == "notion_mcp.db"
