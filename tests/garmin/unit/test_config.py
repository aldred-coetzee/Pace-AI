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

    def test_from_env_missing_email_raises(self, monkeypatch):
        monkeypatch.setattr("pace_ai.garmin.config._find_env_file", lambda: None)
        monkeypatch.delenv("GARMIN_EMAIL", raising=False)
        monkeypatch.delenv("GARMIN_PASSWORD", raising=False)

        with pytest.raises(ValueError, match="GARMIN_EMAIL"):
            Settings.from_env()

    def test_from_env_missing_password_raises(self, monkeypatch):
        monkeypatch.setattr("pace_ai.garmin.config._find_env_file", lambda: None)
        monkeypatch.setenv("GARMIN_EMAIL", "test@test.com")
        monkeypatch.delenv("GARMIN_PASSWORD", raising=False)

        with pytest.raises(ValueError, match="GARMIN_PASSWORD"):
            Settings.from_env()

    def test_defaults(self):
        s = Settings(email="a@b.com", password="p")
        assert s.garth_home == "~/.garth"

    def test_frozen(self):
        s = Settings(email="a@b.com", password="p")
        with pytest.raises(AttributeError):
            s.email = "new@b.com"  # type: ignore[misc]
