"""Shared test fixtures for pace-ai."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

import pytest

from pace_ai.database import GoalDB, HistoryDB


@pytest.fixture()
def tmp_db(tmp_path):
    """Temporary SQLite database path."""
    return str(tmp_path / "test.db")


@pytest.fixture()
def goal_db(tmp_db):
    """GoalDB backed by temporary database."""
    return GoalDB(tmp_db)


@pytest.fixture()
def history_db(tmp_db):
    """HistoryDB backed by temporary database."""
    return HistoryDB(tmp_db)


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


# ── History store sample data factories ──────────────────────────────


def sample_strava_activities() -> list[dict]:
    """Factory for raw Strava activities (as returned by strava-mcp)."""
    today = date.today()
    d1 = (today - timedelta(days=2)).isoformat()
    d2 = (today - timedelta(days=9)).isoformat()
    d3 = (today - timedelta(days=16)).isoformat()
    return [
        {
            "id": 1001,
            "name": "Morning Easy Run",
            "type": "Run",
            "sport_type": "Run",
            "start_date": f"{d3}T06:00:00Z",
            "start_date_local": f"{d3}T08:00:00",
            "distance": 10000,
            "moving_time": 3000,
            "elapsed_time": 3100,
            "total_elevation_gain": 50,
            "average_heartrate": 145,
            "max_heartrate": 155,
            "average_cadence": 85,
            "average_speed": 3.33,
            "workout_type": 0,
        },
        {
            "id": 1002,
            "name": "Tempo Run",
            "type": "Run",
            "sport_type": "Run",
            "start_date": f"{d2}T06:00:00Z",
            "start_date_local": f"{d2}T08:00:00",
            "distance": 8000,
            "moving_time": 2160,
            "elapsed_time": 2200,
            "total_elevation_gain": 30,
            "average_heartrate": 165,
            "max_heartrate": 178,
            "average_cadence": 88,
            "average_speed": 3.7,
            "workout_type": 0,
        },
        {
            "id": 1003,
            "name": "Saturday parkrun",
            "type": "Run",
            "sport_type": "Run",
            "start_date": f"{d1}T08:00:00Z",
            "start_date_local": f"{d1}T10:00:00",
            "distance": 5020,
            "moving_time": 1320,
            "elapsed_time": 1325,
            "total_elevation_gain": 15,
            "average_heartrate": 175,
            "max_heartrate": 185,
            "average_cadence": 90,
            "average_speed": 3.8,
            "workout_type": 1,
        },
    ]


def sample_wellness_data() -> list[dict]:
    """Factory for Garmin wellness snapshots."""
    today = date.today()
    d1 = today.isoformat()
    d2 = (today - timedelta(days=1)).isoformat()
    return [
        {
            "date": d1,
            "body_battery_max": 85,
            "body_battery_min": 25,
            "hrv_status": "balanced",
            "hrv_value": 52.0,
            "sleep_score": 82,
            "sleep_duration_s": 28800,
            "sleep_deep_s": 7200,
            "sleep_rem_s": 5400,
            "stress_avg": 30,
            "stress_max": 65,
            "training_readiness": 75,
            "resting_hr": 48,
            "respiration_avg": 15.2,
        },
        {
            "date": d2,
            "body_battery_max": 78,
            "body_battery_min": 20,
            "hrv_status": "balanced",
            "hrv_value": 48.0,
            "sleep_score": 75,
            "sleep_duration_s": 27000,
            "sleep_deep_s": 6000,
            "sleep_rem_s": 5000,
            "stress_avg": 35,
            "stress_max": 70,
            "training_readiness": 68,
            "resting_hr": 50,
            "respiration_avg": 15.5,
        },
    ]


def sample_withings_measurements() -> list[dict]:
    """Factory for Withings body measurements."""
    today = date.today()
    d1 = today.isoformat()
    d2 = (today - timedelta(days=7)).isoformat()
    return [
        {
            "date": d1,
            "weight_kg": 75.2,
            "bmi": 23.5,
            "body_fat_pct": 15.0,
            "muscle_mass_kg": 35.0,
            "bone_mass_kg": 3.2,
            "water_pct": 55.0,
        },
        {
            "date": d2,
            "weight_kg": 75.5,
            "bmi": 23.6,
            "body_fat_pct": 15.2,
            "muscle_mass_kg": 34.8,
            "bone_mass_kg": 3.2,
            "water_pct": 54.8,
        },
    ]


def sample_diary_entries() -> list[dict]:
    """Factory for Notion diary entries."""
    today = date.today()
    d1 = today.isoformat()
    d2 = (today - timedelta(days=1)).isoformat()
    return [
        {
            "date": d1,
            "stress_1_5": 2,
            "niggles": "Slight right achilles tightness",
            "notes": "Felt good overall, legs fresh from rest day",
        },
        {
            "date": d2,
            "stress_1_5": 3,
            "niggles": None,
            "notes": "Busy day at work",
        },
    ]


def sample_garmin_workouts() -> list[dict]:
    """Factory for Garmin scheduled workouts."""
    today = date.today()
    d1 = today.isoformat()
    d2 = (today + timedelta(days=2)).isoformat()
    d_created = (today - timedelta(days=1)).isoformat()
    return [
        {
            "garmin_workout_id": "WK001",
            "sport_type": "running",
            "scheduled_date": d1,
            "workout_name": "Easy 10k",
            "workout_detail": {"steps": [{"type": "run", "duration_m": 60}]},
            "created_at": f"{d_created}T12:00:00Z",
        },
        {
            "garmin_workout_id": "WK002",
            "sport_type": "running",
            "scheduled_date": d2,
            "workout_name": "Tempo 5k",
            "workout_detail": {"steps": [{"type": "warmup"}, {"type": "run", "pace": "4:30"}]},
            "created_at": f"{d_created}T12:00:00Z",
        },
    ]
