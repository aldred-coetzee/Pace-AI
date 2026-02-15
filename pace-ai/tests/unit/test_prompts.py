"""Unit tests for coaching prompt templates."""

from __future__ import annotations

from pace_ai.prompts.coaching import (
    injury_risk_prompt,
    race_readiness_prompt,
    run_analysis_prompt,
    weekly_plan_prompt,
)

from ..conftest import sample_activities, sample_activity_detail, sample_athlete_stats, sample_goal


class TestWeeklyPlanPrompt:
    def test_contains_framework(self):
        prompt = weekly_plan_prompt(
            goals=[sample_goal()],
            recent_activities=sample_activities(),
            athlete_stats=sample_athlete_stats(),
        )
        assert "Progressive overload" in prompt
        assert "80/20" in prompt
        assert "Recovery" in prompt
        assert "Specificity" in prompt

    def test_includes_goal_data(self):
        goal = sample_goal(race_type="marathon", target_time_formatted="3:30:00")
        prompt = weekly_plan_prompt(
            goals=[goal],
            recent_activities=[],
            athlete_stats={},
        )
        assert "marathon" in prompt
        assert "3:30:00" in prompt

    def test_includes_activities(self):
        prompt = weekly_plan_prompt(
            goals=[],
            recent_activities=sample_activities(),
            athlete_stats={},
        )
        assert "Morning Run" in prompt
        assert "Tempo Run" in prompt

    def test_output_format_specified(self):
        prompt = weekly_plan_prompt(goals=[], recent_activities=[], athlete_stats={})
        assert "Session type" in prompt
        assert "Distance" in prompt
        assert "Target pace" in prompt

    def test_no_goals(self):
        prompt = weekly_plan_prompt(goals=[], recent_activities=[], athlete_stats={})
        assert "No goals set" in prompt

    def test_with_zones(self):
        zones = {"zones": {"easy": {"pace_range_per_km": "5:24 - 6:05/km"}}}
        prompt = weekly_plan_prompt(goals=[], recent_activities=[], athlete_stats={}, training_zones=zones)
        assert "5:24" in prompt


class TestRunAnalysisPrompt:
    def test_contains_framework(self):
        prompt = run_analysis_prompt(activity=sample_activity_detail())
        assert "Pace consistency" in prompt
        assert "Heart rate drift" in prompt
        assert "Cadence" in prompt

    def test_includes_activity_data(self):
        prompt = run_analysis_prompt(activity=sample_activity_detail())
        assert "Tempo Run" in prompt
        assert "km 1" in prompt  # splits

    def test_output_format(self):
        prompt = run_analysis_prompt(activity=sample_activity_detail())
        assert "What went well" in prompt
        assert "What to improve" in prompt
        assert "Training context" in prompt


class TestRaceReadinessPrompt:
    def test_contains_framework(self):
        prompt = race_readiness_prompt(
            goals=[sample_goal()],
            recent_activities=sample_activities(),
            athlete_stats=sample_athlete_stats(),
        )
        assert "Volume adequacy" in prompt
        assert "Key workouts" in prompt
        assert "Taper" in prompt
        assert "VDOT" in prompt

    def test_readiness_score_requested(self):
        prompt = race_readiness_prompt(goals=[], recent_activities=[], athlete_stats={})
        assert "Readiness score" in prompt


class TestInjuryRiskPrompt:
    def test_contains_framework(self):
        distances = [30.0, 35.0, 32.0, 40.0, 35.0, 38.0, 42.0, 45.0]
        load = {
            "acwr": 1.07,
            "risk_level": "optimal",
            "acute_load": 45,
            "chronic_load": 40,
            "load_variability_cv": 0.12,
        }
        prompt = injury_risk_prompt(weekly_distances=distances, training_load=load)
        assert "10% rule" in prompt
        assert "ACWR" in prompt
        assert "Load variability" in prompt

    def test_includes_weekly_data(self):
        distances = [30.0, 35.0, 32.0, 40.0]
        load = {"acwr": 1.17}
        prompt = injury_risk_prompt(weekly_distances=distances, training_load=load)
        assert "Week 1: 30.0" in prompt
        assert "Week 4: 40.0" in prompt

    def test_output_format(self):
        prompt = injury_risk_prompt(weekly_distances=[30, 30, 30, 30], training_load={})
        assert "Risk level" in prompt
        assert "Recommendations" in prompt
