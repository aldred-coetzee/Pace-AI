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
    mock_client.unschedule_workout.return_value = {"unscheduled": True, "schedule_id": 999}
    mock_client.get_calendar.return_value = {
        "calendarItems": [
            {"id": 100, "title": "Easy Run", "date": "2026-02-16", "itemType": "workout", "sportTypeKey": "running"}
        ]
    }
    mock_client.get_body_battery.return_value = [{"charged": 75, "drained": 30}]
    mock_client.get_sleep.return_value = {"sleepScore": 82, "sleepDuration": 28800}
    mock_client.get_hrv.return_value = {"hrvSummary": {"weeklyAvg": 45, "lastNight": 48}}
    mock_client.get_training_readiness.return_value = {"score": 65, "level": "MODERATE"}
    mock_client.get_stress.return_value = {"overallStressLevel": 35, "restStressDuration": 600}
    mock_client.get_resting_hr.return_value = {"restingHeartRate": 52, "calendarDate": "2026-03-10"}

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
    async def test_create_strength(self):
        from garmin_mcp.server import create_workout

        params = '{"exercises": [{"name": "Squats", "sets": 3, "reps": 10, "rest_s": 60}]}'
        result = await create_workout("strength", "Leg Strength", params)
        assert result["created"] is True
        assert result["workout_type"] == "strength"

    @pytest.mark.asyncio()
    async def test_create_mobility(self):
        from garmin_mcp.server import create_workout

        params = '{"exercises": [{"name": "Hip stretch", "sets": 2, "duration_s": 30, "rest_s": 10}]}'
        result = await create_workout("mobility", "AM Mobility", params)
        assert result["created"] is True
        assert result["workout_type"] == "mobility"

    @pytest.mark.asyncio()
    async def test_create_yoga(self):
        from garmin_mcp.server import create_workout

        result = await create_workout("yoga", "Yin Yoga", '{"duration_minutes": 45, "style": "Yin"}')
        assert result["created"] is True
        assert result["workout_type"] == "yoga"

    @pytest.mark.asyncio()
    async def test_create_cardio(self):
        from garmin_mcp.server import create_workout

        result = await create_workout("cardio", "Bike", '{"duration_minutes": 30, "intensity": "moderate"}')
        assert result["created"] is True
        assert result["workout_type"] == "cardio"

    @pytest.mark.asyncio()
    async def test_create_hiit(self):
        from garmin_mcp.server import create_workout

        params = '{"rounds": 4, "work_s": 30, "rest_s": 15, "exercises": ["Burpees", "Squats"]}'
        result = await create_workout("hiit", "HIIT Circuit", params)
        assert result["created"] is True
        assert result["workout_type"] == "hiit"

    @pytest.mark.asyncio()
    async def test_create_walking(self):
        from garmin_mcp.server import create_workout

        result = await create_workout("walking", "Evening Walk", '{"duration_minutes": 45}')
        assert result["created"] is True
        assert result["workout_type"] == "walking"

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

        result = await list_calendar("2026-02-16", "2026-02-16")
        assert result["count"] == 1
        assert result["events"][0]["date"] == "2026-02-16"
        assert result["events"][0]["title"] == "Easy Run"


@pytest.mark.usefixtures("_wired")
class TestUnscheduleWorkout:
    @pytest.mark.asyncio()
    async def test_unschedule_workout(self):
        from garmin_mcp.server import unschedule_workout

        result = await unschedule_workout(999)
        assert result["unscheduled"] is True
        assert result["schedule_id"] == 999


@pytest.mark.usefixtures("_wired")
class TestCreateAndSchedule:
    @pytest.mark.asyncio()
    async def test_create_and_schedule(self):
        from garmin_mcp.server import create_and_schedule

        result = await create_and_schedule("easy_run", "Test Run", "2026-03-20", '{"duration_minutes": 30}')
        assert result["created"] is True
        assert result["scheduled"] is True
        assert result["workout_id"] == 200
        assert result["date"] == "2026-03-20"

    @pytest.mark.asyncio()
    async def test_create_and_schedule_invalid_type(self):
        from garmin_mcp.server import create_and_schedule

        result = await create_and_schedule("nope", "Bad", "2026-03-20")
        assert result["error"] == "invalid_workout_type"


@pytest.mark.usefixtures("_wired")
class TestGetBodyBattery:
    @pytest.mark.asyncio()
    async def test_get_body_battery(self):
        from garmin_mcp.server import get_body_battery

        result = await get_body_battery("2026-03-10")
        assert result["date"] == "2026-03-10"
        assert result["data"] == [{"charged": 75, "drained": 30}]

    @pytest.mark.asyncio()
    async def test_get_body_battery_api_error(self, _wired):
        from garmin_mcp.server import get_body_battery

        _wired.get_body_battery.side_effect = GarminAPIError("api_error", "Failed", "Retry")
        result = await get_body_battery("2026-03-10")
        assert result["error"] == "api_error"


@pytest.mark.usefixtures("_wired")
class TestGetSleep:
    @pytest.mark.asyncio()
    async def test_get_sleep(self):
        from garmin_mcp.server import get_sleep

        result = await get_sleep("2026-03-10")
        assert result["sleepScore"] == 82

    @pytest.mark.asyncio()
    async def test_get_sleep_api_error(self, _wired):
        from garmin_mcp.server import get_sleep

        _wired.get_sleep.side_effect = GarminAPIError("api_error", "Failed", "Retry")
        result = await get_sleep("2026-03-10")
        assert result["error"] == "api_error"


@pytest.mark.usefixtures("_wired")
class TestGetHrv:
    @pytest.mark.asyncio()
    async def test_get_hrv(self):
        from garmin_mcp.server import get_hrv

        result = await get_hrv("2026-03-10")
        assert result["hrvSummary"]["weeklyAvg"] == 45

    @pytest.mark.asyncio()
    async def test_get_hrv_no_data(self, _wired):
        from garmin_mcp.server import get_hrv

        _wired.get_hrv.return_value = None
        result = await get_hrv("2026-03-10")
        assert result["hrv"] is None
        assert "No HRV data" in result["message"]

    @pytest.mark.asyncio()
    async def test_get_hrv_api_error(self, _wired):
        from garmin_mcp.server import get_hrv

        _wired.get_hrv.side_effect = GarminAPIError("api_error", "Failed", "Retry")
        result = await get_hrv("2026-03-10")
        assert result["error"] == "api_error"


@pytest.mark.usefixtures("_wired")
class TestGetTrainingReadiness:
    @pytest.mark.asyncio()
    async def test_get_training_readiness(self):
        from garmin_mcp.server import get_training_readiness

        result = await get_training_readiness("2026-03-10")
        assert result["score"] == 65

    @pytest.mark.asyncio()
    async def test_get_training_readiness_api_error(self, _wired):
        from garmin_mcp.server import get_training_readiness

        _wired.get_training_readiness.side_effect = GarminAPIError("api_error", "Failed", "Retry")
        result = await get_training_readiness("2026-03-10")
        assert result["error"] == "api_error"


@pytest.mark.usefixtures("_wired")
class TestGetStress:
    @pytest.mark.asyncio()
    async def test_get_stress(self):
        from garmin_mcp.server import get_stress

        result = await get_stress("2026-03-10")
        assert result["overallStressLevel"] == 35

    @pytest.mark.asyncio()
    async def test_get_stress_api_error(self, _wired):
        from garmin_mcp.server import get_stress

        _wired.get_stress.side_effect = GarminAPIError("api_error", "Failed", "Retry")
        result = await get_stress("2026-03-10")
        assert result["error"] == "api_error"


@pytest.mark.usefixtures("_wired")
class TestGetRestingHr:
    @pytest.mark.asyncio()
    async def test_get_resting_hr(self):
        from garmin_mcp.server import get_resting_hr

        result = await get_resting_hr("2026-03-10")
        assert result["restingHeartRate"] == 52

    @pytest.mark.asyncio()
    async def test_get_resting_hr_no_data(self, _wired):
        from garmin_mcp.server import get_resting_hr

        _wired.get_resting_hr.return_value = None
        result = await get_resting_hr("2026-03-10")
        assert result["resting_hr"] is None
        assert "No resting HR" in result["message"]

    @pytest.mark.asyncio()
    async def test_get_resting_hr_api_error(self, _wired):
        from garmin_mcp.server import get_resting_hr

        _wired.get_resting_hr.side_effect = GarminAPIError("api_error", "Failed", "Retry")
        result = await get_resting_hr("2026-03-10")
        assert result["error"] == "api_error"


@pytest.mark.usefixtures("_wired")
class TestGetWellnessSnapshot:
    @pytest.mark.asyncio()
    async def test_get_wellness_snapshot(self):
        from garmin_mcp.server import get_wellness_snapshot

        result = await get_wellness_snapshot(days=3)
        assert len(result["dates"]) == 3
        assert len(result["days"]) == 3
        day = result["days"][0]
        assert "body_battery" in day
        assert "sleep" in day
        assert "hrv" in day
        assert "resting_hr" in day
        assert "training_readiness" in day
        assert "stress" in day

    @pytest.mark.asyncio()
    async def test_get_wellness_snapshot_partial_failure(self, _wired):
        from garmin_mcp.server import get_wellness_snapshot

        _wired.get_hrv.side_effect = GarminAPIError("api_error", "HRV unavailable", "Retry")
        result = await get_wellness_snapshot(days=2)
        assert len(result["days"]) == 2
        for day in result["days"]:
            assert day["hrv"] is None
            assert day["sleep"]["sleepScore"] == 82
