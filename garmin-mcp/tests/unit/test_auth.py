"""Unit tests for auth module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from garmin_mcp.auth import GarminAuth


class TestGarminAuth:
    def test_resume_success(self):
        auth = GarminAuth("/tmp/test_garth")
        with (
            patch("garmin_mcp.auth.garth") as mock_garth,
        ):
            mock_garth.client.username = "test_user"
            assert auth.resume() is True
            mock_garth.resume.assert_called_once_with("/tmp/test_garth")

    def test_resume_failure(self):
        auth = GarminAuth("/tmp/test_garth")
        with patch("garmin_mcp.auth.garth") as mock_garth:
            mock_garth.resume.side_effect = Exception("No saved session")
            assert auth.resume() is False

    def test_login_calls_garth(self):
        auth = GarminAuth("/tmp/test_garth")
        with patch("garmin_mcp.auth.garth") as mock_garth:
            auth.login("test@example.com", "password123")
            mock_garth.login.assert_called_once_with("test@example.com", "password123", prompt_mfa=True)
            mock_garth.save.assert_called_once_with("/tmp/test_garth")

    def test_garth_home_expands_tilde(self):
        auth = GarminAuth("~/custom_garth")
        # The path should be expanded
        assert "~" not in auth._garth_home


class TestLoginCli:
    def test_login_cli_missing_env_exits(self, monkeypatch):
        """login_cli should exit 1 if credentials are missing."""
        monkeypatch.setattr("garmin_mcp.config._find_env_file", lambda: None)
        monkeypatch.delenv("GARMIN_EMAIL", raising=False)
        monkeypatch.delenv("GARMIN_PASSWORD", raising=False)

        import pytest

        from garmin_mcp.auth import login_cli

        with pytest.raises(SystemExit, match="1"):
            login_cli()

    def test_login_cli_already_authenticated(self, monkeypatch):
        """login_cli should return early if session resumes."""
        monkeypatch.setenv("GARMIN_EMAIL", "test@example.com")
        monkeypatch.setenv("GARMIN_PASSWORD", "password")

        with patch.object(GarminAuth, "resume", return_value=True):
            from garmin_mcp.auth import login_cli

            # Should not raise — just prints and returns
            login_cli()

    def test_login_cli_performs_login(self, monkeypatch):
        """login_cli should call login when resume fails."""
        monkeypatch.setenv("GARMIN_EMAIL", "test@example.com")
        monkeypatch.setenv("GARMIN_PASSWORD", "password")

        mock_login = MagicMock()
        with (
            patch.object(GarminAuth, "resume", return_value=False),
            patch.object(GarminAuth, "login", mock_login),
        ):
            from garmin_mcp.auth import login_cli

            login_cli()
            mock_login.assert_called_once_with("test@example.com", "password")
