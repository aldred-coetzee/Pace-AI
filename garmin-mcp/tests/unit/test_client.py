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

    def test_get_events_for_date_delegates(self, client_settings):
        client = GarminClient(client_settings)
        mock_garmin = MagicMock()
        mock_garmin.get_all_day_events.return_value = [{"date": "2026-02-16", "workoutId": 100}]
        client._garmin = mock_garmin

        result = client.get_events_for_date("2026-02-16")
        mock_garmin.get_all_day_events.assert_called_once_with("2026-02-16")
        assert result == [{"date": "2026-02-16", "workoutId": 100}]

    def test_get_body_battery_delegates(self, client_settings):
        client = GarminClient(client_settings)
        mock_garmin = MagicMock()
        mock_garmin.get_body_battery.return_value = [{"charged": 75}]
        client._garmin = mock_garmin

        result = client.get_body_battery("2026-03-10")
        mock_garmin.get_body_battery.assert_called_once_with("2026-03-10")
        assert result == [{"charged": 75}]

    def test_get_sleep_delegates(self, client_settings):
        client = GarminClient(client_settings)
        mock_garmin = MagicMock()
        mock_garmin.get_sleep_data.return_value = {"sleepScore": 82}
        client._garmin = mock_garmin

        result = client.get_sleep("2026-03-10")
        mock_garmin.get_sleep_data.assert_called_once_with("2026-03-10")
        assert result == {"sleepScore": 82}

    def test_get_hrv_delegates(self, client_settings):
        client = GarminClient(client_settings)
        mock_garmin = MagicMock()
        mock_garmin.get_hrv_data.return_value = {"hrvSummary": {"weeklyAvg": 45}}
        client._garmin = mock_garmin

        result = client.get_hrv("2026-03-10")
        mock_garmin.get_hrv_data.assert_called_once_with("2026-03-10")
        assert result == {"hrvSummary": {"weeklyAvg": 45}}

    def test_get_hrv_returns_none(self, client_settings):
        client = GarminClient(client_settings)
        mock_garmin = MagicMock()
        mock_garmin.get_hrv_data.return_value = None
        client._garmin = mock_garmin

        result = client.get_hrv("2026-03-10")
        assert result is None

    def test_get_training_readiness_delegates(self, client_settings):
        client = GarminClient(client_settings)
        mock_garmin = MagicMock()
        mock_garmin.get_training_readiness.return_value = {"score": 65}
        client._garmin = mock_garmin

        result = client.get_training_readiness("2026-03-10")
        mock_garmin.get_training_readiness.assert_called_once_with("2026-03-10")
        assert result == {"score": 65}

    def test_get_stress_delegates(self, client_settings):
        client = GarminClient(client_settings)
        mock_garmin = MagicMock()
        mock_garmin.get_stress_data.return_value = {"overallStressLevel": 35}
        client._garmin = mock_garmin

        result = client.get_stress("2026-03-10")
        mock_garmin.get_stress_data.assert_called_once_with("2026-03-10")
        assert result == {"overallStressLevel": 35}

    def test_get_resting_hr_delegates(self, client_settings):
        client = GarminClient(client_settings)
        mock_garmin = MagicMock()
        mock_garmin.get_rhr_day.return_value = {"restingHeartRate": 52, "calendarDate": "2026-03-10"}
        client._garmin = mock_garmin

        result = client.get_resting_hr("2026-03-10")
        mock_garmin.get_rhr_day.assert_called_once_with("2026-03-10")
        assert result == {"restingHeartRate": 52, "calendarDate": "2026-03-10"}

    def test_get_resting_hr_returns_none(self, client_settings):
        client = GarminClient(client_settings)
        mock_garmin = MagicMock()
        mock_garmin.get_rhr_day.return_value = None
        client._garmin = mock_garmin

        result = client.get_resting_hr("2026-03-10")
        assert result is None
