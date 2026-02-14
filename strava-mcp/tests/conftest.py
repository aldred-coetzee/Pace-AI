"""Shared test fixtures for strava-mcp."""

from __future__ import annotations

from typing import Any

import pytest

from strava_mcp.auth import TokenStore
from strava_mcp.cache import ActivityCache
from strava_mcp.config import Settings


@pytest.fixture()
def tmp_db(tmp_path):
    """Temporary SQLite database path."""
    return str(tmp_path / "test.db")


@pytest.fixture()
def settings(tmp_db):
    """Test settings with dummy credentials."""
    return Settings(
        client_id="12345",
        client_secret="test_secret",
        access_token="test_access_token",
        refresh_token="test_refresh_token",
        db_path=tmp_db,
    )


@pytest.fixture()
def token_store(tmp_db):
    """Token store backed by temporary database."""
    return TokenStore(tmp_db)


@pytest.fixture()
def cache(tmp_db):
    """Activity cache backed by temporary database."""
    return ActivityCache(tmp_db, ttl=3600)


def sample_athlete() -> dict[str, Any]:
    """Factory for a realistic athlete profile."""
    return {
        "id": 123456,
        "username": "testrunner",
        "firstname": "Test",
        "lastname": "Runner",
        "city": "Cape Town",
        "state": "Western Cape",
        "country": "South Africa",
        "sex": "M",
        "premium": False,
        "created_at": "2020-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
        "follower_count": 50,
        "friend_count": 30,
        "measurement_preference": "meters",
        "weight": 75.0,
    }


def sample_activity(activity_id: int = 1, **overrides: Any) -> dict[str, Any]:
    """Factory for a realistic activity summary."""
    data = {
        "id": activity_id,
        "name": f"Morning Run #{activity_id}",
        "type": "Run",
        "sport_type": "Run",
        "start_date": "2024-12-01T06:00:00Z",
        "start_date_local": "2024-12-01T08:00:00+02:00",
        "distance": 10000.0,
        "moving_time": 3000,
        "elapsed_time": 3100,
        "total_elevation_gain": 120.0,
        "average_speed": 3.33,
        "max_speed": 4.5,
        "average_heartrate": 150,
        "max_heartrate": 175,
        "suffer_score": 80,
        "has_heartrate": True,
        "average_cadence": 85.0,
    }
    data.update(overrides)
    return data


def sample_activity_detail(activity_id: int = 1) -> dict[str, Any]:
    """Factory for a detailed activity with splits and laps."""
    base = sample_activity(activity_id)
    base.update(
        {
            "calories": 650,
            "description": "Easy morning run",
            "splits_metric": [
                {
                    "distance": 1000,
                    "elapsed_time": 300,
                    "moving_time": 298,
                    "average_speed": 3.36,
                    "average_heartrate": 145,
                    "split": i + 1,
                }
                for i in range(10)
            ],
            "laps": [
                {
                    "id": i + 1,
                    "name": f"Lap {i + 1}",
                    "distance": 5000,
                    "elapsed_time": 1500,
                    "moving_time": 1490,
                    "average_speed": 3.36,
                    "average_heartrate": 148,
                }
                for i in range(2)
            ],
            "best_efforts": [
                {"name": "1k", "elapsed_time": 270, "distance": 1000},
                {"name": "5k", "elapsed_time": 1450, "distance": 5000},
            ],
        }
    )
    return base


def sample_streams() -> list[dict[str, Any]]:
    """Factory for activity stream data (Strava API format)."""
    n = 10
    return [
        {"type": "time", "data": list(range(0, n * 300, 300)), "series_type": "time", "original_size": n},
        {"type": "distance", "data": [i * 1000.0 for i in range(n)], "series_type": "distance", "original_size": n},
        {"type": "heartrate", "data": [140 + i for i in range(n)], "series_type": "distance", "original_size": n},
        {"type": "altitude", "data": [100.0 + i * 5 for i in range(n)], "series_type": "distance", "original_size": n},
    ]


def sample_athlete_stats() -> dict[str, Any]:
    """Factory for athlete statistics."""
    return {
        "recent_run_totals": {"count": 12, "distance": 60000, "moving_time": 18000, "elevation_gain": 500},
        "ytd_run_totals": {"count": 150, "distance": 750000, "moving_time": 225000, "elevation_gain": 8000},
        "all_run_totals": {"count": 500, "distance": 2500000, "moving_time": 750000, "elevation_gain": 25000},
        "recent_ride_totals": {"count": 0, "distance": 0, "moving_time": 0, "elevation_gain": 0},
        "ytd_ride_totals": {"count": 0, "distance": 0, "moving_time": 0, "elevation_gain": 0},
        "all_ride_totals": {"count": 0, "distance": 0, "moving_time": 0, "elevation_gain": 0},
    }


def sample_zones() -> dict[str, Any]:
    """Factory for athlete zones."""
    return {
        "heart_rate": {
            "custom_zones": False,
            "zones": [
                {"min": 0, "max": 115},
                {"min": 115, "max": 152},
                {"min": 152, "max": 171},
                {"min": 171, "max": 190},
                {"min": 190, "max": -1},
            ],
        }
    }
