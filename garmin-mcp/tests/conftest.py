"""Shared test fixtures for garmin-mcp."""

from __future__ import annotations

import os
from typing import Any
from unittest.mock import MagicMock

# Set test env vars BEFORE any garmin_mcp imports that trigger Settings.from_env()
os.environ.setdefault("GARMIN_EMAIL", "test@example.com")
os.environ.setdefault("GARMIN_PASSWORD", "test_password")

import pytest

from garmin_mcp.config import Settings


@pytest.fixture()
def settings():
    """Test settings with dummy credentials."""
    return Settings(
        email="test@example.com",
        password="test_password",
        garth_home="/tmp/test_garth",
    )


@pytest.fixture()
def mock_garmin_api():
    """Mock garminconnect.Garmin instance."""
    mock = MagicMock()
    mock.get_full_name.return_value = "Test Runner"
    mock.get_workouts.return_value = [sample_workout()]
    mock.get_workout_by_id.return_value = sample_workout_detail()
    mock.upload_workout.return_value = {"workoutId": 12345, "workoutName": "Test Workout"}
    # Mock garth for direct API calls (delete, schedule, calendar)
    mock.garth = MagicMock()
    mock_resp = MagicMock()
    mock_resp.json.return_value = {}
    mock_resp.raise_for_status.return_value = None
    mock.garth.delete.return_value = mock_resp
    mock.garth.post.return_value = mock_resp
    mock.garth.get.return_value = mock_resp
    return mock


def sample_workout(**overrides: Any) -> dict[str, Any]:
    """Factory for a workout summary."""
    data: dict[str, Any] = {
        "workoutId": 12345,
        "workoutName": "Easy Run 30min",
        "sportType": {"sportTypeId": 1, "sportTypeKey": "running"},
        "createdDate": "2026-02-16T10:00:00.000",
        "updatedDate": "2026-02-16T10:00:00.000",
    }
    data.update(overrides)
    return data


def sample_workout_detail(**overrides: Any) -> dict[str, Any]:
    """Factory for a full workout with steps."""
    data = sample_workout()
    data.update(
        {
            "workoutSegments": [
                {
                    "segmentOrder": 1,
                    "sportType": {"sportTypeId": 1, "sportTypeKey": "running"},
                    "workoutSteps": [
                        {
                            "type": "ExecutableStepDTO",
                            "stepOrder": 1,
                            "stepType": {"stepTypeId": 3, "stepTypeKey": "interval"},
                            "endCondition": {"conditionTypeId": 2, "conditionTypeKey": "time"},
                            "endConditionValue": 1800.0,
                            "targetType": {"workoutTargetTypeId": 4, "workoutTargetTypeKey": "heart.rate.zone"},
                            "zoneNumber": 1,
                        }
                    ],
                }
            ],
        }
    )
    data.update(overrides)
    return data


def sample_calendar_events() -> list[dict[str, Any]]:
    """Factory for calendar event data."""
    return [
        {
            "id": 1,
            "date": "2026-02-16",
            "workoutId": 12345,
            "workoutName": "Easy Run 30min",
        },
        {
            "id": 2,
            "date": "2026-02-18",
            "workoutId": 12346,
            "workoutName": "Run/Walk 25min",
        },
    ]
