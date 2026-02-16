"""Integration tests for garmin-mcp server tools.

Tests each tool through the actual async function with a mocked GarminClient.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from garmin_mcp.client import GarminAPIError
from garmin_mcp.config import Settings


@pytest.fixture()
def _wired(monkeypatch):
    """Wire up server module globals with test instances."""
    import garmin_mcp.server as srv

    settings = Settings(email="test@example.com", password="test", garth_home="/tmp/test_garth")
    monkeypatch.setattr(srv, "settings", settings)

    mock_client = MagicMock()
    mock_client.check_auth.return_value = {"authenticated": True, "display_name": "Test Runner"}
    mock_client.get_workouts.return_value = [
        {
            "workoutId": 100,
            "workoutName": "Easy Run",
            "sportType": {"sportTypeId": 1, "sportTypeKey": "running"},
            "createdDate": "2026-02-16",
            "updatedDate": "2026-02-16",
        }
    ]
    mock_client.get_workout.return_value = {"workoutId": 100, "workoutName": "Easy Run"}
    mock_client.create_workout.return_value = {"workoutId": 200, "workoutName": "New Workout"}
    mock_client.delete_workout.return_value = {"deleted": True, "workout_id": 100}
    mock_client.schedule_workout.return_value = {"scheduled": True, "workout_id": 100, "date": "2026-02-20"}
    mock_client.get_calendar.return_value = [{"date": "2026-02-16", "workoutId": 100}]

    monkeypatch.setattr(srv, "garmin", mock_client)
    return mock_client


@pytest.mark.usefixtures("_wired")
class TestAuthenticate:
    @pytest.mark.asyncio()
    async def test_authenticate_success(self):
        from garmin_mcp.server import authenticate

        result = await authenticate()
        assert result["authenticated"] is True
        assert result["display_name"] == "Test Runner"

    @pytest.mark.asyncio()
    async def test_authenticate_failure(self, _wired):
        from garmin_mcp.server import authenticate

        _wired.check_auth.side_effect = GarminAPIError("auth_required", "No session", "Login first")
        result = await authenticate()
        assert result["error"] == "auth_required"


@pytest.mark.usefixtures("_wired")
class TestCreateWorkout:
    @pytest.mark.asyncio()
    async def test_create_easy_run(self):
        from garmin_mcp.server import create_workout

        result = await create_workout("easy_run", "Easy 30", '{"duration_minutes": 30}')
        assert result["created"] is True
        assert result["workout_id"] == 200
        assert result["workout_type"] == "easy_run"

    @pytest.mark.asyncio()
    async def test_create_run_walk(self):
        from garmin_mcp.server import create_workout

        result = await create_workout("run_walk", "RW 5x3/1", '{"intervals": 5, "run_minutes": 3, "walk_minutes": 1}')
        assert result["created"] is True

    @pytest.mark.asyncio()
    async def test_invalid_workout_type(self):
        from garmin_mcp.server import create_workout

        result = await create_workout("bogus", "Test", "{}")
        assert result["error"] == "invalid_workout_type"
        assert "bogus" in result["message"]

    @pytest.mark.asyncio()
    async def test_invalid_params_json(self):
        from garmin_mcp.server import create_workout

        result = await create_workout("easy_run", "Test", "not-json")
        assert result["error"] == "invalid_json"

    @pytest.mark.asyncio()
    async def test_missing_required_params(self):
        from garmin_mcp.server import create_workout

        result = await create_workout("easy_run", "Test", "{}")
        assert result["error"] == "invalid_params"

    @pytest.mark.asyncio()
    async def test_api_error(self, _wired):
        from garmin_mcp.server import create_workout

        _wired.create_workout.side_effect = GarminAPIError("api_error", "Server error", "Retry")
        result = await create_workout("easy_run", "Test", '{"duration_minutes": 30}')
        assert result["error"] == "api_error"


@pytest.mark.usefixtures("_wired")
class TestListWorkouts:
    @pytest.mark.asyncio()
    async def test_list_workouts(self):
        from garmin_mcp.server import list_workouts

        result = await list_workouts()
        assert result["count"] == 1
        assert result["workouts"][0]["workout_id"] == 100
        assert result["workouts"][0]["name"] == "Easy Run"

    @pytest.mark.asyncio()
    async def test_list_workouts_api_error(self, _wired):
        from garmin_mcp.server import list_workouts

        _wired.get_workouts.side_effect = GarminAPIError("api_error", "Failed", "Retry")
        result = await list_workouts()
        assert result["error"] == "api_error"


@pytest.mark.usefixtures("_wired")
class TestGetWorkout:
    @pytest.mark.asyncio()
    async def test_get_workout(self):
        from garmin_mcp.server import get_workout

        result = await get_workout(100)
        assert result["workoutId"] == 100


@pytest.mark.usefixtures("_wired")
class TestDeleteWorkout:
    @pytest.mark.asyncio()
    async def test_delete_workout(self):
        from garmin_mcp.server import delete_workout

        result = await delete_workout(100)
        assert result["deleted"] is True

    @pytest.mark.asyncio()
    async def test_delete_api_error(self, _wired):
        from garmin_mcp.server import delete_workout

        _wired.delete_workout.side_effect = GarminAPIError("delete_failed", "Not found", "Check ID")
        result = await delete_workout(999)
        assert result["error"] == "delete_failed"


@pytest.mark.usefixtures("_wired")
class TestScheduleWorkout:
    @pytest.mark.asyncio()
    async def test_schedule_workout(self):
        from garmin_mcp.server import schedule_workout

        result = await schedule_workout(100, "2026-02-20")
        assert result["scheduled"] is True
        assert result["date"] == "2026-02-20"

    @pytest.mark.asyncio()
    async def test_schedule_api_error(self, _wired):
        from garmin_mcp.server import schedule_workout

        _wired.schedule_workout.side_effect = GarminAPIError("schedule_failed", "Bad date", "Fix date")
        result = await schedule_workout(100, "invalid")
        assert result["error"] == "schedule_failed"


@pytest.mark.usefixtures("_wired")
class TestListCalendar:
    @pytest.mark.asyncio()
    async def test_list_calendar(self):
        from garmin_mcp.server import list_calendar

        result = await list_calendar(2026, 2)
        assert isinstance(result, list)
        assert result[0]["date"] == "2026-02-16"
