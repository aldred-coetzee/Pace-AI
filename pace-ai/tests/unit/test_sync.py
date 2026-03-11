"""Unit tests for sync tools."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from pace_ai.tools.sync import (
    get_sync_status,
    sync_all,
    sync_garmin_wellness,
    sync_garmin_workouts,
    sync_notion,
    sync_strava,
    sync_withings,
)
from tests.conftest import (
    sample_diary_entries,
    sample_garmin_workouts,
    sample_strava_activities,
    sample_wellness_data,
    sample_withings_measurements,
)


class TestSyncStrava:
    def test_sync_basic(self, history_db):
        activities = sample_strava_activities()
        result = sync_strava(history_db, activities)
        assert result["source"] == "strava"
        assert result["activities_synced"] == 3

    def test_race_detection(self, history_db):
        activities = sample_strava_activities()
        result = sync_strava(history_db, activities)
        # parkrun (name match) + workout_type=1 (race)
        assert result["races_detected"] >= 1

        races = history_db.get_race_results()
        assert len(races) >= 1
        race_names = [r["event_name"] for r in races]
        assert any("parkrun" in n for n in race_names)

    def test_vdot_calculated_for_races(self, history_db):
        activities = sample_strava_activities()
        sync_strava(history_db, activities)
        races = history_db.get_race_results()
        for r in races:
            assert r["vdot"] is not None
            assert r["vdot"] > 0

    def test_pb_marked(self, history_db):
        activities = sample_strava_activities()
        sync_strava(history_db, activities)
        races = history_db.get_race_results()
        pb_count = sum(1 for r in races if r["pb"] == 1)
        assert pb_count >= 1

    def test_idempotent_sync(self, history_db):
        activities = sample_strava_activities()
        sync_strava(history_db, activities)
        sync_strava(history_db, activities)

        all_activities = history_db.get_activities(days=30)
        assert len(all_activities) == 3

    def test_sync_log_created(self, history_db):
        sync_strava(history_db, sample_strava_activities())
        status = get_sync_status(history_db)
        strava = [s for s in status if s["source"] == "strava"]
        assert len(strava) == 1
        assert strava[0]["status"] == "success"

    def test_distance_label_detection(self, history_db):
        """5020m should be detected as '5k' (within 5% tolerance)."""
        activities = [sample_strava_activities()[2]]  # parkrun at 5020m
        sync_strava(history_db, activities)
        races = history_db.get_race_results()
        assert races[0]["distance_label"] == "5k"


class TestSyncGarminWellness:
    def test_sync_basic(self, history_db):
        result = sync_garmin_wellness(history_db, sample_wellness_data())
        assert result["source"] == "garmin_wellness"
        assert result["records_synced"] == 2

    def test_idempotent(self, history_db):
        data = sample_wellness_data()
        sync_garmin_wellness(history_db, data)
        sync_garmin_wellness(history_db, data)
        result = history_db.get_wellness(days=7)
        assert len(result) == 2


class TestSyncWithings:
    def test_sync_basic(self, history_db):
        result = sync_withings(history_db, sample_withings_measurements())
        assert result["source"] == "withings"
        assert result["records_synced"] == 2

    def test_idempotent(self, history_db):
        data = sample_withings_measurements()
        sync_withings(history_db, data)
        sync_withings(history_db, data)
        result = history_db.get_body_measurements(days=30)
        assert len(result) == 2


class TestSyncNotion:
    def test_sync_basic(self, history_db):
        result = sync_notion(history_db, sample_diary_entries())
        assert result["source"] == "notion"
        assert result["records_synced"] == 2

    def test_idempotent(self, history_db):
        data = sample_diary_entries()
        sync_notion(history_db, data)
        sync_notion(history_db, data)
        result = history_db.get_diary_entries(days=7)
        assert len(result) == 2


class TestSyncGarminWorkouts:
    def test_sync_basic(self, history_db):
        result = sync_garmin_workouts(history_db, sample_garmin_workouts())
        assert result["source"] == "garmin_workouts"
        assert result["records_synced"] == 2

    def test_workout_matching(self, history_db):
        """A workout scheduled on a day with a matching activity should be marked completed."""
        # First sync an activity on 2026-03-10
        history_db.upsert_activities(
            [
                {
                    "strava_id": "999",
                    "date": "2026-03-10",
                    "sport_type": "Run",
                    "distance_m": 10000,
                }
            ]
        )
        # Then sync a workout scheduled for the same date
        sync_garmin_workouts(history_db, sample_garmin_workouts())

        with history_db._connect() as conn:
            matched = conn.execute(
                "SELECT * FROM scheduled_workouts WHERE completed = 1",
            ).fetchall()
        assert len(matched) >= 1


class TestGetSyncStatus:
    def test_multiple_sources(self, history_db):
        sync_strava(history_db, sample_strava_activities())
        sync_garmin_wellness(history_db, sample_wellness_data())
        sync_notion(history_db, sample_diary_entries())

        status = get_sync_status(history_db)
        sources = {s["source"] for s in status}
        assert "strava" in sources
        assert "garmin_wellness" in sources
        assert "notion" in sources


class TestSyncAll:
    @pytest.mark.asyncio()
    async def test_sync_all_success(self, history_db):
        """sync_all calls all sources and reports results."""
        mock_strava_client = AsyncMock()
        mock_strava_client.get_all_activities.return_value = sample_strava_activities()

        mock_garmin_client = MagicMock()
        mock_garmin_client.get_body_battery.return_value = [{"batteryLevel": 80}]
        mock_garmin_client.get_sleep.return_value = {"sleepTimeSeconds": 28000}
        mock_garmin_client.get_stress.return_value = {"overallStressLevel": 30}
        mock_garmin_client.get_resting_hr.return_value = {"restingHeartRate": 52}
        mock_garmin_client.get_workouts.return_value = []

        mock_withings_client = MagicMock()
        mock_withings_client.get_measurements.return_value = [
            {"datetime": "2026-03-10T09:00:00", "weight_kg": 80.0, "date": 1773134817},
        ]

        mock_notion_client = AsyncMock()
        mock_notion_client.fetch_all_entries.return_value = []

        with (
            patch("strava_mcp.client.StravaClient", return_value=mock_strava_client),
            patch("strava_mcp.config.Settings.from_env", return_value=MagicMock(db_path=":memory:")),
            patch("strava_mcp.auth.TokenStore", return_value=MagicMock()),
            patch("garmin_mcp.client.GarminClient", return_value=mock_garmin_client),
            patch("garmin_mcp.config.Settings.from_env", return_value=MagicMock()),
            patch("withings_mcp.client.WithingsClient", return_value=mock_withings_client),
            patch("withings_mcp.config.Settings.from_env", return_value=MagicMock()),
            patch("notion_mcp.client.NotionClient", return_value=mock_notion_client),
            patch("notion_mcp.config.Settings.from_env", return_value=MagicMock()),
        ):
            result = await sync_all(history_db)

        assert result["sources_synced"] >= 3
        assert "strava" in result["results"]

    @pytest.mark.asyncio()
    async def test_sync_all_continues_on_failure(self, history_db):
        """If one source fails, others still sync."""
        mock_strava_client = AsyncMock()
        mock_strava_client.get_all_activities.side_effect = RuntimeError("Strava down")

        mock_garmin_client = MagicMock()
        mock_garmin_client.get_body_battery.return_value = None
        mock_garmin_client.get_sleep.return_value = None
        mock_garmin_client.get_stress.return_value = None
        mock_garmin_client.get_resting_hr.return_value = None
        mock_garmin_client.get_workouts.return_value = []

        mock_withings_client = MagicMock()
        mock_withings_client.get_measurements.return_value = []

        mock_notion_client = AsyncMock()
        mock_notion_client.fetch_all_entries.return_value = []

        with (
            patch("strava_mcp.client.StravaClient", return_value=mock_strava_client),
            patch("strava_mcp.config.Settings.from_env", return_value=MagicMock(db_path=":memory:")),
            patch("strava_mcp.auth.TokenStore", return_value=MagicMock()),
            patch("garmin_mcp.client.GarminClient", return_value=mock_garmin_client),
            patch("garmin_mcp.config.Settings.from_env", return_value=MagicMock()),
            patch("withings_mcp.client.WithingsClient", return_value=mock_withings_client),
            patch("withings_mcp.config.Settings.from_env", return_value=MagicMock()),
            patch("notion_mcp.client.NotionClient", return_value=mock_notion_client),
            patch("notion_mcp.config.Settings.from_env", return_value=MagicMock()),
        ):
            result = await sync_all(history_db)

        assert result["sources_failed"] >= 1
        assert "strava" in result["errors"]
        # Other sources should still have synced
        assert result["sources_synced"] >= 2
