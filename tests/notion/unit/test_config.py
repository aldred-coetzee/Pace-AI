"""Unit tests for config module."""

from __future__ import annotations

import pytest

from pace_ai.notion.config import Settings


class TestSettings:
    def test_from_env_defaults(self, tmp_path):
        s = Settings.from_env()
        assert s.db_path == str(tmp_path / "pace-ai-workspace" / "notion.db")

    def test_from_env_token(self, monkeypatch):
        monkeypatch.setenv("NOTION_TOKEN", "ntn_test123")
        s = Settings.from_env()
        assert s.notion_token == "ntn_test123"

    def test_from_env_database_id(self, monkeypatch):
        monkeypatch.setenv("NOTION_DIARY_DATABASE_ID", "abc-123")
        s = Settings.from_env()
        assert s.diary_database_id == "abc-123"

    def test_from_env_db_path(self, monkeypatch):
        monkeypatch.setenv("NOTION_DB", "/tmp/test.db")
        s = Settings.from_env()
        assert s.db_path == "/tmp/test.db"

    def test_from_env_db_path_relative(self, monkeypatch, tmp_path):
        monkeypatch.setenv("NOTION_DB", "sub/n.db")
        assert Settings.from_env().db_path == str(tmp_path / "pace-ai-workspace" / "sub" / "n.db")

    def test_env_beats_config_env(self, monkeypatch, tmp_path):
        ws = tmp_path / "pace-ai-workspace"
        ws.mkdir(mode=0o700)
        (ws / "config.env").write_text("NOTION_TOKEN=from_file\nNOTION_DIARY_DATABASE_ID=file_db\n")
        monkeypatch.setenv("NOTION_TOKEN", "from_env")
        monkeypatch.delenv("NOTION_DIARY_DATABASE_ID", raising=False)
        s = Settings.from_env()
        assert s.notion_token == "from_env"
        assert s.diary_database_id == "file_db"

    def test_frozen(self):
        s = Settings()
        with pytest.raises(AttributeError):
            s.notion_token = "x"  # type: ignore[misc]

    def test_defaults(self):
        s = Settings()
        assert s.notion_token == ""
        assert s.diary_database_id == ""
        assert s.db_path == ""
