"""Unit tests for config module."""

from __future__ import annotations

import pytest

from withings_mcp.config import Settings, _parse_port


class TestParsePort:
    def test_valid_port(self):
        assert _parse_port("8004") == 8004

    def test_invalid_port_raises(self):
        with pytest.raises(ValueError, match="WITHINGS_MCP_PORT must be a number"):
            _parse_port("not_a_number")


class TestSettings:
    def test_from_env_defaults(self):
        s = Settings.from_env()
        assert s.port == 8004
        assert s.host == "127.0.0.1"

    def test_from_env_custom_port(self, monkeypatch):
        monkeypatch.setenv("WITHINGS_MCP_PORT", "9999")
        s = Settings.from_env()
        assert s.port == 9999

    def test_from_env_config_folder(self, monkeypatch):
        monkeypatch.setenv("WITHINGS_CONFIG_FOLDER", "/tmp/withings")
        s = Settings.from_env()
        assert s.config_folder == "/tmp/withings"

    def test_frozen(self):
        s = Settings()
        with pytest.raises(AttributeError):
            s.port = 9999  # type: ignore[misc]

    def test_defaults(self):
        s = Settings()
        assert s.config_folder == ""
        assert s.host == "127.0.0.1"
        assert s.port == 8004
