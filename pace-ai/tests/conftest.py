"""Shared test fixtures for pace-ai."""

from __future__ import annotations

from typing import Any

import pytest

from pace_ai.database import GoalDB


@pytest.fixture()
def tmp_db(tmp_path):
    """Temporary SQLite database path."""
    return str(tmp_path / "test.db")


@pytest.fixture()
def goal_db(tmp_db):
    """GoalDB backed by temporary database."""
    return GoalDB(tmp_db)


def sample_goal(**overrides: Any) -> dict:
    """Factory for a goal dict (as returned by GoalDB)."""
    data: dict[str, Any] = {
        "id": 1,
        "race_type": "half marathon",
        "target_time_seconds": 5400,
        "target_time_formatted": "1:30:00",
        "race_date": "2025-06-15",
        "notes": "Cape Town Half Marathon",
        "created_at": 1700000000.0,
        "updated_at": 1700000000.0,
    }
    data.update(overrides)
    return data


def sample_activities() -> list[dict]:
    """Factory for recent activities (enriched format from strava-mcp)."""
    return [
        {
            "id": 1,
            "name": "Morning Run",
            "type": "Run",
            "start_date": "2024-12-01T06:00:00Z",
            "distance_km": 10.0,
            "pace_min_per_km": "5:00",
            "average_heartrate": 150,
        },
        {
            "id": 2,
            "name": "Tempo Run",
            "type": "Run",
            "start_date": "2024-12-03T06:00:00Z",
            "distance_km": 8.0,
            "pace_min_per_km": "4:30",
            "average_heartrate": 165,
        },
        {
            "id": 3,
            "name": "Long Run",
            "type": "Run",
            "start_date": "2024-12-07T07:00:00Z",
            "distance_km": 18.0,
            "pace_min_per_km": "5:30",
            "average_heartrate": 145,
        },
    ]


def sample_athlete_stats() -> dict:
    """Factory for athlete statistics."""
    return {
        "recent_run_totals": {"count": 12, "distance": 60000, "moving_time": 18000, "elevation_gain": 500},
        "ytd_run_totals": {"count": 150, "distance": 750000, "moving_time": 225000, "elevation_gain": 8000},
        "all_run_totals": {"count": 500, "distance": 2500000, "moving_time": 750000, "elevation_gain": 25000},
    }


def sample_activity_detail() -> dict:
    """Factory for a detailed activity."""
    return {
        "id": 42,
        "name": "Tempo Run",
        "type": "Run",
        "start_date": "2024-12-03T06:00:00Z",
        "distance": 8000,
        "moving_time": 2160,
        "elapsed_time": 2200,
        "total_elevation_gain": 50,
        "average_heartrate": 165,
        "max_heartrate": 178,
        "average_cadence": 86,
        "splits_metric": [
            {"split": i + 1, "distance": 1000, "moving_time": 270, "average_speed": 3.7, "average_heartrate": 160 + i}
            for i in range(8)
        ],
    }
