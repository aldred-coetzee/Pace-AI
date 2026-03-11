"""Unit tests for athlete profile tools."""

from __future__ import annotations

import pytest

from pace_ai.tools.profile import (
    generate_athlete_profile,
    get_athlete_profile,
    update_athlete_profile_manual,
)
from pace_ai.tools.sync import (
    sync_garmin_wellness,
    sync_strava,
    sync_withings,
)
from tests.conftest import (
    sample_strava_activities,
    sample_wellness_data,
    sample_withings_measurements,
)


class TestGetAthleteProfile:
    def test_returns_none_when_empty(self, history_db):
        assert get_athlete_profile(history_db) is None


class TestGenerateAthleteProfile:
    def test_basic_generation(self, history_db):
        sync_strava(history_db, sample_strava_activities())
        profile = generate_athlete_profile(history_db)
        assert profile is not None
        assert profile["id"] == 1
        assert profile["updated_at"] is not None

    def test_vdot_from_race(self, history_db):
        sync_strava(history_db, sample_strava_activities())
        profile = generate_athlete_profile(history_db)
        # parkrun was detected as a race with VDOT calculated
        assert profile["estimated_vdot"] is not None
        assert profile["estimated_vdot"] > 0

    def test_vdot_peak(self, history_db):
        sync_strava(history_db, sample_strava_activities())
        profile = generate_athlete_profile(history_db)
        assert profile["vdot_peak"] is not None
        assert profile["vdot_peak"] > 0
        assert profile["vdot_peak_date"] is not None

    def test_vdot_current_from_recent_race(self, history_db):
        sync_strava(history_db, sample_strava_activities())
        profile = generate_athlete_profile(history_db)
        # parkrun (workout_type=1) is detected as a race, so vdot_current comes from it
        assert profile["vdot_current"] is not None
        assert profile["vdot_current"] > 0

    def test_vdot_current_none_without_recent_race(self, history_db):
        # Activities without any race (workout_type != 1, no race name pattern)
        non_race_activities = [a for a in sample_strava_activities() if a.get("workout_type") != 1]
        sync_strava(history_db, non_race_activities)
        profile = generate_athlete_profile(history_db)
        assert profile["vdot_current"] is None

    def test_weekly_km_computed(self, history_db):
        sync_strava(history_db, sample_strava_activities())
        profile = generate_athlete_profile(history_db)
        # We have activities, so weekly km should be computed
        assert profile["typical_weekly_km"] is not None or profile["current_weekly_km"] is not None

    def test_wellness_baselines(self, history_db):
        sync_garmin_wellness(history_db, sample_wellness_data())
        profile = generate_athlete_profile(history_db)
        assert profile["resting_hr_baseline"] is not None
        assert profile["hrv_baseline"] is not None

    def test_weight_from_withings(self, history_db):
        sync_withings(history_db, sample_withings_measurements())
        profile = generate_athlete_profile(history_db)
        assert profile["weight_kg_current"] is not None

    def test_empty_history_still_creates_profile(self, history_db):
        profile = generate_athlete_profile(history_db)
        assert profile is not None
        assert profile["id"] == 1
        assert profile["estimated_vdot"] is None
        assert profile["vdot_peak"] is None
        assert profile["vdot_peak_date"] is None
        assert profile["vdot_current"] is None
        assert profile["typical_weekly_km"] is None

    def test_training_age_uses_earliest_race(self, history_db):
        # Insert a race older than any activity
        history_db.upsert_race_result(
            {
                "date": "2010-05-23",
                "distance_m": 42195,
                "distance_label": "marathon",
                "time_s": 13682,
                "event_name": "Old Marathon",
                "course_type": "road",
                "vdot": 40.0,
                "source": "manual",
            }
        )
        sync_strava(history_db, sample_strava_activities())
        profile = generate_athlete_profile(history_db)
        # Training age should be based on 2010 race, not 2026 activity
        assert profile["training_age_years"] >= 15.0

    def test_regeneration_preserves_manual_fields(self, history_db):
        update_athlete_profile_manual(history_db, {"gender": "male", "experience_level": "advanced"})
        sync_strava(history_db, sample_strava_activities())
        profile = generate_athlete_profile(history_db)
        assert profile["gender"] == "male"
        assert profile["experience_level"] == "advanced"


class TestUpdateAthleteProfileManual:
    def test_update_manual_fields(self, history_db):
        profile = update_athlete_profile_manual(
            history_db,
            {
                "gender": "male",
                "experience_level": "advanced",
                "preferred_long_run_day": "Saturday",
                "available_days_per_week": 5,
            },
        )
        assert profile["gender"] == "male"
        assert profile["experience_level"] == "advanced"
        assert profile["preferred_long_run_day"] == "Saturday"
        assert profile["available_days_per_week"] == 5

    def test_rejects_auto_fields(self, history_db):
        with pytest.raises(ValueError, match="auto-derived"):
            update_athlete_profile_manual(history_db, {"estimated_vdot": 50.0})

    def test_rejects_vdot_peak_manual(self, history_db):
        with pytest.raises(ValueError, match="auto-derived"):
            update_athlete_profile_manual(history_db, {"vdot_peak": 50.0})

    def test_injury_history_serialization(self, history_db):
        injuries = [{"date": "2025-03", "injury": "achilles", "duration_weeks": 12, "resolved": False}]
        profile = update_athlete_profile_manual(history_db, {"injury_history": injuries})
        assert "achilles" in profile["injury_history"]

    def test_date_of_birth(self, history_db):
        profile = update_athlete_profile_manual(history_db, {"date_of_birth": "1990-05-15"})
        assert profile["date_of_birth"] == "1990-05-15"

    def test_notes(self, history_db):
        profile = update_athlete_profile_manual(history_db, {"notes": "Recovering from injury"})
        assert profile["notes"] == "Recovering from injury"
