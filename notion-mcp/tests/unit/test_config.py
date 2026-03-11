"""Unit tests for config module."""

from __future__ import annotations

import pytest

from notion_mcp.config import Settings, _parse_port


class TestParsePort:
    def test_valid_port(self):
        assert _parse_port("8005") == 8005

    def test_invalid_port_raises(self):
        with pytest.raises(ValueError, match="NOTION_MCP_PORT must be a number"):
            _parse_port("not_a_number")


class TestSettings:
    def test_from_env_defaults(self):
        s = Settings.from_env()
        assert s.port == 8005
        assert s.host == "127.0.0.1"
        assert s.db_path == "notion_mcp.db"

    def test_from_env_custom_port(self, monkeypatch):
        monkeypatch.setenv("NOTION_MCP_PORT", "9999")
        s = Settings.from_env()
        assert s.port == 9999

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
            s.port = 9999  # type: ignore[misc]

    def test_defaults(self):
        s = Settings()
        assert s.notion_token == ""
        assert s.diary_database_id == ""
        assert s.host == "127.0.0.1"
        assert s.port == 8005
        assert s.db_path == "notion_mcp.db"
