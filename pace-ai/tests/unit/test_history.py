"""Unit tests for history query tools."""

from __future__ import annotations

from pace_ai.tools.history import (
    get_pbs,
    get_race_history,
    get_recent_activities,
    get_recent_diary,
    get_recent_wellness,
    get_weekly_distances,
)
from pace_ai.tools.sync import sync_garmin_wellness, sync_notion, sync_strava
from tests.conftest import (
    sample_diary_entries,
    sample_strava_activities,
    sample_wellness_data,
)


class TestGetWeeklyDistances:
    def test_returns_weekly_totals(self, history_db):
        sync_strava(history_db, sample_strava_activities())
        weeks = get_weekly_distances(history_db, weeks=4, sport_type="run")
        assert len(weeks) >= 1
        for w in weeks:
            assert "distance_km" in w
            assert "activity_count" in w
            assert w["distance_km"] > 0

    def test_empty_when_no_data(self, history_db):
        weeks = get_weekly_distances(history_db, weeks=4)
        assert weeks == []


class TestGetRecentActivities:
    def test_returns_activities(self, history_db):
        sync_strava(history_db, sample_strava_activities())
        activities = get_recent_activities(history_db, days=30)
        assert len(activities) == 3

    def test_sport_type_filter(self, history_db):
        sync_strava(history_db, sample_strava_activities())
        # Add a ride
        history_db.upsert_activities(
            [
                {
                    "strava_id": "9999",
                    "date": "2026-03-05",
                    "sport_type": "Ride",
                    "distance_m": 30000,
                }
            ]
        )
        runs = get_recent_activities(history_db, days=30, sport_type="run")
        assert all("Run" in a["sport_type"] for a in runs)

    def test_empty_when_no_data(self, history_db):
        assert get_recent_activities(history_db, days=30) == []


class TestGetRecentWellness:
    def test_returns_snapshots(self, history_db):
        sync_garmin_wellness(history_db, sample_wellness_data())
        result = get_recent_wellness(history_db, days=7)
        assert len(result) == 2

    def test_empty_when_no_data(self, history_db):
        assert get_recent_wellness(history_db, days=7) == []


class TestGetRecentDiary:
    def test_returns_entries(self, history_db):
        sync_notion(history_db, sample_diary_entries())
        result = get_recent_diary(history_db, days=7)
        assert len(result) == 2

    def test_empty_when_no_data(self, history_db):
        assert get_recent_diary(history_db, days=7) == []


class TestGetRaceHistory:
    def test_returns_races(self, history_db):
        sync_strava(history_db, sample_strava_activities())
        races = get_race_history(history_db, limit=10)
        assert len(races) >= 1

    def test_empty_when_no_data(self, history_db):
        assert get_race_history(history_db) == []


class TestGetPBs:
    def test_returns_pbs(self, history_db):
        sync_strava(history_db, sample_strava_activities())
        pbs = get_pbs(history_db)
        assert len(pbs) >= 1
        assert pbs[0]["best_time_s"] > 0

    def test_empty_when_no_data(self, history_db):
        assert get_pbs(history_db) == []
