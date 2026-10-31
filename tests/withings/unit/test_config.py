"""Unit tests for config module."""

from __future__ import annotations

import pytest

from pace_ai.withings.config import Settings


class TestSettings:
    def test_from_env_defaults(self, tmp_path):
        s = Settings.from_env()
        assert s.config_folder == str(tmp_path / "pace-ai-workspace" / "withings")

    def test_from_env_config_folder(self, monkeypatch):
        monkeypatch.setenv("WITHINGS_CONFIG_FOLDER", "/tmp/withings")
        s = Settings.from_env()
        assert s.config_folder == "/tmp/withings"

    def test_frozen(self):
        s = Settings()
        with pytest.raises(AttributeError):
            s.config_folder = "x"  # type: ignore[misc]

    def test_defaults(self):
        s = Settings()
        assert s.config_folder == ""
