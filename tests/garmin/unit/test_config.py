"""Unit tests for config module."""

from __future__ import annotations

import pytest

from pace_ai.garmin.config import Settings


class TestSettings:
    def test_from_env_with_all_values(self, monkeypatch):
        monkeypatch.setenv("GARMIN_EMAIL", "runner@test.com")
        monkeypatch.setenv("GARMIN_PASSWORD", "secret123")
        monkeypatch.setenv("GARTH_HOME", "/custom/garth")

        s = Settings.from_env()

        assert s.email == "runner@test.com"
        assert s.password == "secret123"
        assert s.garth_home == "/custom/garth"

    def test_from_env_missing_credentials_does_not_raise(self, monkeypatch):
        monkeypatch.delenv("GARMIN_EMAIL", raising=False)
        monkeypatch.delenv("GARMIN_PASSWORD", raising=False)

        s = Settings.from_env()

        assert s.email == ""
        assert s.password == ""

    def test_garth_home_defaults_to_workspace(self, tmp_path):
        s = Settings.from_env()
        assert s.garth_home == str(tmp_path / "pace-ai-workspace" / "garth")

    def test_garth_home_relative_resolves_against_workspace(self, monkeypatch, tmp_path):
        monkeypatch.setenv("GARTH_HOME", "tokens")
        assert Settings.from_env().garth_home == str(tmp_path / "pace-ai-workspace" / "tokens")

    def test_defaults(self):
        s = Settings()
        assert s.email == ""
        assert s.password == ""

    def test_frozen(self):
        s = Settings(email="a@b.com", password="p")
        with pytest.raises(AttributeError):
            s.email = "new@b.com"  # type: ignore[misc]
