"""Unit tests for HistoryDB database layer."""

from __future__ import annotations

from tests.conftest import (
    sample_diary_entries,
    sample_garmin_workouts,
    sample_wellness_data,
    sample_withings_measurements,
)


class TestActivities:
    def test_upsert_and_query(self, history_db):
        activities = [
            {
                "strava_id": "100",
                "date": "2026-03-01",
                "sport_type": "Run",
                "name": "Easy Run",
                "distance_m": 10000,
                "moving_time_s": 3000,
            },
        ]
        count = history_db.upsert_activities(activities)
        assert count == 1

        result = history_db.get_activities(days=30, sport_type="run")
        assert len(result) == 1
        assert result[0]["strava_id"] == "100"
        assert result[0]["name"] == "Easy Run"

    def test_upsert_idempotent(self, history_db):
        activity = {
            "strava_id": "100",
            "date": "2026-03-01",
            "sport_type": "Run",
            "name": "Easy Run",
            "distance_m": 10000,
        }
        history_db.upsert_activities([activity])
        activity["name"] = "Updated Name"
        history_db.upsert_activities([activity])

        result = history_db.get_activities(days=30)
        assert len(result) == 1
        assert result[0]["name"] == "Updated Name"

    def test_sport_type_filter(self, history_db):
        history_db.upsert_activities(
            [
                {"strava_id": "1", "date": "2026-03-01", "sport_type": "Run", "distance_m": 10000},
                {"strava_id": "2", "date": "2026-03-01", "sport_type": "Ride", "distance_m": 30000},
            ]
        )
        runs = history_db.get_activities(days=30, sport_type="run")
        assert len(runs) == 1
        assert runs[0]["sport_type"] == "Run"

    def test_weekly_distances(self, history_db):
        history_db.upsert_activities(
            [
                {"strava_id": "1", "date": "2026-03-01", "sport_type": "Run", "distance_m": 10000},
                {"strava_id": "2", "date": "2026-03-02", "sport_type": "Run", "distance_m": 5000},
                {"strava_id": "3", "date": "2026-03-08", "sport_type": "Run", "distance_m": 12000},
            ]
        )
        weeks = history_db.get_weekly_distances(weeks=4, sport_type="run")
        assert len(weeks) >= 1
        total_km = sum(w["distance_km"] for w in weeks)
        assert total_km > 0


class TestWellness:
    def test_upsert_and_query(self, history_db):
        data = sample_wellness_data()
        count = history_db.upsert_wellness(data)
        assert count == 2

        result = history_db.get_wellness(days=7)
        assert len(result) == 2

    def test_upsert_idempotent(self, history_db):
        data = [{"date": "2026-03-10", "resting_hr": 48}]
        history_db.upsert_wellness(data)
        data[0]["resting_hr"] = 50
        history_db.upsert_wellness(data)

        result = history_db.get_wellness(days=7)
        assert len(result) == 1
        assert result[0]["resting_hr"] == 50


class TestBodyMeasurements:
    def test_upsert_and_query(self, history_db):
        data = sample_withings_measurements()
        count = history_db.upsert_body_measurements(data)
        assert count == 2

        result = history_db.get_body_measurements(days=30)
        assert len(result) == 2

    def test_upsert_idempotent(self, history_db):
        m = {"date": "2026-03-10", "weight_kg": 75.2, "body_fat_pct": 15.0}
        history_db.upsert_body_measurements([m])
        m["body_fat_pct"] = 14.8
        history_db.upsert_body_measurements([m])

        result = history_db.get_body_measurements(days=30)
        assert len(result) == 1
        assert result[0]["body_fat_pct"] == 14.8


class TestDiaryEntries:
    def test_upsert_and_query(self, history_db):
        data = sample_diary_entries()
        count = history_db.upsert_diary_entries(data)
        assert count == 2

        result = history_db.get_diary_entries(days=7)
        assert len(result) == 2

    def test_upsert_idempotent(self, history_db):
        entry = {"date": "2026-03-10", "stress_1_5": 2, "notes": "original"}
        history_db.upsert_diary_entries([entry])
        entry["notes"] = "updated"
        history_db.upsert_diary_entries([entry])

        result = history_db.get_diary_entries(days=7)
        assert len(result) == 1
        assert result[0]["notes"] == "updated"


class TestScheduledWorkouts:
    def test_upsert_and_query(self, history_db):
        data = sample_garmin_workouts()
        count = history_db.upsert_scheduled_workouts(data)
        assert count == 2

        result = history_db.get_scheduled_workouts(days=30)
        assert len(result) == 2

    def test_upsert_idempotent(self, history_db):
        w = {"garmin_workout_id": "WK001", "sport_type": "running", "workout_name": "Easy"}
        history_db.upsert_scheduled_workouts([w])
        w["workout_name"] = "Updated Easy"
        history_db.upsert_scheduled_workouts([w])

        # May or may not appear depending on scheduled_date, query by direct SQL
        with history_db._connect() as conn:
            rows = conn.execute("SELECT * FROM scheduled_workouts").fetchall()
        assert len(rows) == 1
        assert rows[0]["workout_name"] == "Updated Easy"


class TestRaceResults:
    def test_upsert_and_query(self, history_db):
        result = history_db.upsert_race_result(
            {
                "date": "2026-03-08",
                "distance_m": 5000,
                "distance_label": "5k",
                "time_s": 1320,
                "event_name": "parkrun",
                "vdot": 42.0,
                "source": "1003",
            }
        )
        assert result["distance_label"] == "5k"
        assert result["time_s"] == 1320

        races = history_db.get_race_results()
        assert len(races) == 1

    def test_pb_marking(self, history_db):
        history_db.upsert_race_result(
            {
                "date": "2026-01-01",
                "distance_m": 5000,
                "distance_label": "5k",
                "time_s": 1400,
                "source": "a",
            }
        )
        history_db.upsert_race_result(
            {
                "date": "2026-02-01",
                "distance_m": 5000,
                "distance_label": "5k",
                "time_s": 1320,
                "source": "b",
            }
        )
        history_db.mark_pbs()

        pbs = history_db.get_pbs()
        assert len(pbs) == 1
        assert pbs[0]["best_time_s"] == 1320

        races = history_db.get_race_results()
        pb_race = [r for r in races if r["pb"] == 1]
        assert len(pb_race) == 1
        assert pb_race[0]["time_s"] == 1320

    def test_upsert_idempotent(self, history_db):
        r = {"date": "2026-03-08", "distance_m": 5000, "time_s": 1320, "event_name": "parkrun"}
        history_db.upsert_race_result(r)
        r["event_name"] = "Updated parkrun"
        history_db.upsert_race_result(r)

        races = history_db.get_race_results()
        assert len(races) == 1
        assert races[0]["event_name"] == "Updated parkrun"


class TestAthleteProfile:
    def test_empty_profile(self, history_db):
        assert history_db.get_athlete_profile() is None

    def test_create_and_get(self, history_db):
        profile = history_db.upsert_athlete_profile(
            {
                "estimated_vdot": 45.0,
                "typical_weekly_km": 40.0,
            }
        )
        assert profile["estimated_vdot"] == 45.0
        assert profile["id"] == 1

        fetched = history_db.get_athlete_profile()
        assert fetched["estimated_vdot"] == 45.0

    def test_update_preserves_existing(self, history_db):
        history_db.upsert_athlete_profile({"estimated_vdot": 45.0, "gender": "male"})
        updated = history_db.upsert_athlete_profile({"estimated_vdot": 47.0})
        assert updated["estimated_vdot"] == 47.0
        assert updated["gender"] == "male"


class TestSyncLog:
    def test_log_and_query(self, history_db):
        history_db.log_sync("strava", 10, "success", earliest_date="2026-03-01", latest_date="2026-03-10")
        history_db.log_sync("garmin_wellness", 5, "success")

        status = history_db.get_sync_status()
        assert len(status) == 2
        sources = {s["source"] for s in status}
        assert sources == {"strava", "garmin_wellness"}

    def test_only_latest_per_source(self, history_db):
        history_db.log_sync("strava", 5, "success")
        history_db.log_sync("strava", 10, "success")

        status = history_db.get_sync_status()
        assert len(status) == 1
        assert status[0]["records_added"] == 10
