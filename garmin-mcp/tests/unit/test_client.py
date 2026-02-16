"""Unit tests for client module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from garmin_mcp.client import GarminAPIError, GarminClient
from garmin_mcp.config import Settings


@pytest.fixture()
def client_settings():
    return Settings(email="test@example.com", password="test", garth_home="/tmp/test_garth")


class TestGarminAPIError:
    def test_to_dict(self):
        err = GarminAPIError(code="test_error", message="Something broke", action="Fix it")
        d = err.to_dict()
        assert d["error"] == "test_error"
        assert d["message"] == "Something broke"
        assert d["action"] == "Fix it"

    def test_inherits_runtime_error(self):
        err = GarminAPIError(code="test", message="msg", action="act")
        assert isinstance(err, RuntimeError)
        assert str(err) == "msg"


class TestGarminClient:
    def test_ensure_client_no_session_raises(self, client_settings):
        client = GarminClient(client_settings)
        with (
            patch.object(client._auth, "resume", return_value=False),
            pytest.raises(GarminAPIError, match="No valid Garmin session"),
        ):
            client._ensure_client()

    def test_ensure_client_login_failure_raises(self, client_settings):
        client = GarminClient(client_settings)
        with (
            patch.object(client._auth, "resume", return_value=True),
            patch("garmin_mcp.client.Garmin") as mock_garmin_cls,
        ):
            mock_instance = MagicMock()
            mock_instance.login.side_effect = Exception("Login failed")
            mock_garmin_cls.return_value = mock_instance
            with pytest.raises(GarminAPIError, match="Failed to initialize"):
                client._ensure_client()

    def test_ensure_client_success(self, client_settings):
        client = GarminClient(client_settings)
        with (
            patch.object(client._auth, "resume", return_value=True),
            patch("garmin_mcp.client.Garmin") as mock_garmin_cls,
        ):
            mock_instance = MagicMock()
            mock_garmin_cls.return_value = mock_instance
            result = client._ensure_client()
            assert result is mock_instance

    def test_call_auth_error_clears_client(self, client_settings):
        client = GarminClient(client_settings)
        mock_garmin = MagicMock()
        mock_garmin.get_workouts.side_effect = Exception("401 Unauthorized")
        client._garmin = mock_garmin

        with pytest.raises(GarminAPIError, match="session expired"):
            client._call("get_workouts")
        assert client._garmin is None

    def test_call_rate_limit_error(self, client_settings):
        client = GarminClient(client_settings)
        mock_garmin = MagicMock()
        mock_garmin.get_workouts.side_effect = Exception("429 Too Many Requests")
        client._garmin = mock_garmin

        with pytest.raises(GarminAPIError, match="rate limit"):
            client._call("get_workouts")

    def test_call_generic_error(self, client_settings):
        client = GarminClient(client_settings)
        mock_garmin = MagicMock()
        mock_garmin.get_workouts.side_effect = Exception("Something unexpected")
        client._garmin = mock_garmin

        with pytest.raises(GarminAPIError, match="Garmin API error"):
            client._call("get_workouts")

    def test_call_unknown_method_raises(self, client_settings):
        client = GarminClient(client_settings)
        mock_garmin = MagicMock(spec=[])  # no attributes
        client._garmin = mock_garmin

        with pytest.raises(AttributeError, match="no method"):
            client._call("nonexistent_method")

    def test_check_auth(self, client_settings):
        client = GarminClient(client_settings)
        mock_garmin = MagicMock()
        mock_garmin.get_full_name.return_value = "Test Runner"
        client._garmin = mock_garmin

        result = client.check_auth()
        assert result["authenticated"] is True
        assert result["display_name"] == "Test Runner"

    def test_get_workouts_delegates(self, client_settings):
        client = GarminClient(client_settings)
        mock_garmin = MagicMock()
        mock_garmin.get_workouts.return_value = [{"workoutId": 1}]
        client._garmin = mock_garmin

        result = client.get_workouts(0, 50)
        mock_garmin.get_workouts.assert_called_once_with(0, 50)
        assert result == [{"workoutId": 1}]

    def test_get_workout_delegates(self, client_settings):
        client = GarminClient(client_settings)
        mock_garmin = MagicMock()
        mock_garmin.get_workout_by_id.return_value = {"workoutId": 123}
        client._garmin = mock_garmin

        result = client.get_workout(123)
        mock_garmin.get_workout_by_id.assert_called_once_with(123)
        assert result == {"workoutId": 123}

    def test_create_workout_delegates(self, client_settings):
        client = GarminClient(client_settings)
        mock_garmin = MagicMock()
        mock_garmin.upload_workout.return_value = {"workoutId": 456}
        client._garmin = mock_garmin

        payload = {"workoutName": "Test"}
        result = client.create_workout(payload)
        mock_garmin.upload_workout.assert_called_once_with(payload)
        assert result == {"workoutId": 456}

    def test_delete_workout_uses_garth(self, client_settings):
        client = GarminClient(client_settings)
        mock_garmin = MagicMock()
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_garmin.garth.delete.return_value = mock_resp
        client._garmin = mock_garmin

        result = client.delete_workout(123)
        mock_garmin.garth.delete.assert_called_once_with("connectapi", "/workout-service/workout/123", api=True)
        assert result["deleted"] is True

    def test_schedule_workout_uses_garth(self, client_settings):
        client = GarminClient(client_settings)
        mock_garmin = MagicMock()
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_garmin.garth.post.return_value = mock_resp
        client._garmin = mock_garmin

        result = client.schedule_workout(123, "2026-02-20")
        mock_garmin.garth.post.assert_called_once_with(
            "connectapi", "/workout-service/schedule/123", json={"date": "2026-02-20"}, api=True
        )
        assert result["scheduled"] is True
        assert result["date"] == "2026-02-20"

    def test_get_calendar_uses_garth(self, client_settings):
        client = GarminClient(client_settings)
        mock_garmin = MagicMock()
        mock_resp = MagicMock()
        mock_resp.json.return_value = [{"date": "2026-02-16"}]
        mock_resp.raise_for_status.return_value = None
        mock_garmin.garth.get.return_value = mock_resp
        client._garmin = mock_garmin

        result = client.get_calendar(2026, 2)
        mock_garmin.garth.get.assert_called_once_with("connectapi", "/workout-service/schedule/2026/2", api=True)
        assert result == [{"date": "2026-02-16"}]
