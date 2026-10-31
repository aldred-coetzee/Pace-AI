"""Unit tests for config module."""

from __future__ import annotations

import pytest

from pace_ai.strava.config import Settings


class TestSettings:
    def test_from_env_with_all_values(self, monkeypatch):
        monkeypatch.setenv("STRAVA_CLIENT_ID", "99999")
        monkeypatch.setenv("STRAVA_CLIENT_SECRET", "supersecret")
        monkeypatch.setenv("STRAVA_ACCESS_TOKEN", "tok123")
        monkeypatch.setenv("STRAVA_REFRESH_TOKEN", "ref456")

        s = Settings.from_env()

        assert s.client_id == "99999"
        assert s.client_secret == "supersecret"
        assert s.access_token == "tok123"
        assert s.refresh_token == "ref456"

    def test_from_env_missing_client_id_raises(self, monkeypatch):
        monkeypatch.delenv("STRAVA_CLIENT_ID", raising=False)
        monkeypatch.delenv("STRAVA_CLIENT_SECRET", raising=False)

        with pytest.raises(ValueError, match="STRAVA_CLIENT_ID"):
            Settings.from_env()

    def test_from_env_missing_client_secret_raises(self, monkeypatch):
        monkeypatch.setenv("STRAVA_CLIENT_ID", "12345")
        monkeypatch.delenv("STRAVA_CLIENT_SECRET", raising=False)

        with pytest.raises(ValueError, match="STRAVA_CLIENT_SECRET"):
            Settings.from_env()

    def test_db_defaults_to_workspace(self, monkeypatch, tmp_path):
        monkeypatch.setenv("STRAVA_CLIENT_ID", "1")
        monkeypatch.setenv("STRAVA_CLIENT_SECRET", "s")
        assert Settings.from_env().db_path == str(tmp_path / "pace-ai-workspace" / "strava.db")

    def test_db_relative_and_absolute_override(self, monkeypatch, tmp_path):
        monkeypatch.setenv("STRAVA_CLIENT_ID", "1")
        monkeypatch.setenv("STRAVA_CLIENT_SECRET", "s")
        monkeypatch.setenv("STRAVA_DB", "x.db")
        assert Settings.from_env().db_path == str(tmp_path / "pace-ai-workspace" / "x.db")
        monkeypatch.setenv("STRAVA_DB", str(tmp_path / "abs.db"))
        assert Settings.from_env().db_path == str(tmp_path / "abs.db")

    def test_credentials_read_from_config_env(self, monkeypatch, tmp_path):
        ws = tmp_path / "pace-ai-workspace"
        ws.mkdir(mode=0o700)
        (ws / "config.env").write_text("STRAVA_CLIENT_ID=fid\nSTRAVA_CLIENT_SECRET=fsec\n")
        monkeypatch.delenv("STRAVA_CLIENT_ID", raising=False)
        monkeypatch.delenv("STRAVA_CLIENT_SECRET", raising=False)
        monkeypatch.setenv("STRAVA_CLIENT_SECRET", "envsec")
        s = Settings.from_env()
        assert (s.client_id, s.client_secret) == ("fid", "envsec")

    def test_defaults(self):
        s = Settings(client_id="1", client_secret="s")
        assert s.access_token is None
        assert s.refresh_token is None

    def test_frozen(self):
        s = Settings(client_id="1", client_secret="s")
        with pytest.raises(AttributeError):
            s.client_id = "2"  # type: ignore[misc]
