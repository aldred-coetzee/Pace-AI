"""Unit tests for coaching prompt templates."""

from __future__ import annotations

from pace_ai.prompts.coaching import (
    _format_evidence,
    injury_risk_prompt,
    race_readiness_prompt,
    run_analysis_prompt,
    weekly_plan_prompt,
)

from ..conftest import sample_activities, sample_activity_detail, sample_athlete_stats, sample_goal

# Use a nonexistent DB path so prompts gracefully fall back to "not found" message.
_NO_DB = "/nonexistent/claims.db"


class TestWeeklyPlanPrompt:
    def test_contains_evidence_section(self):
        prompt = weekly_plan_prompt(
            goals=[sample_goal()],
            recent_activities=sample_activities(),
            athlete_stats=sample_athlete_stats(),
            db_path=_NO_DB,
        )
        assert "Research Evidence" in prompt

    def test_contains_instructions(self):
        prompt = weekly_plan_prompt(
            goals=[sample_goal()],
            recent_activities=sample_activities(),
            athlete_stats=sample_athlete_stats(),
            db_path=_NO_DB,
        )
        assert "progressive overload" in prompt
        assert "80/20" in prompt
        assert "recovery" in prompt

    def test_includes_goal_data(self):
        goal = sample_goal(race_type="marathon", target_time_formatted="3:30:00")
        prompt = weekly_plan_prompt(
            goals=[goal],
            recent_activities=[],
            athlete_stats={},
            db_path=_NO_DB,
        )
        assert "marathon" in prompt
        assert "3:30:00" in prompt

    def test_includes_activities(self):
        prompt = weekly_plan_prompt(
            goals=[],
            recent_activities=sample_activities(),
            athlete_stats={},
            db_path=_NO_DB,
        )
        assert "Morning Run" in prompt
        assert "Tempo Run" in prompt

    def test_output_format_specified(self):
        prompt = weekly_plan_prompt(goals=[], recent_activities=[], athlete_stats={}, db_path=_NO_DB)
        assert "Session type" in prompt
        assert "Distance" in prompt
        assert "Target pace" in prompt

    def test_no_goals(self):
        prompt = weekly_plan_prompt(goals=[], recent_activities=[], athlete_stats={}, db_path=_NO_DB)
        assert "No goals set" in prompt

    def test_with_zones(self):
        zones = {"zones": {"easy": {"pace_range_per_km": "5:24 - 6:05/km"}}}
        prompt = weekly_plan_prompt(
            goals=[], recent_activities=[], athlete_stats={}, training_zones=zones, db_path=_NO_DB
        )
        # 5:24/km ≈ 8:41/mi, 6:05/km ≈ 9:47/mi (converted to miles)
        assert "8:41" in prompt
        assert "/mi" in prompt

    def test_graceful_without_db(self):
        """Prompt should still render when claims DB is missing."""
        prompt = weekly_plan_prompt(
            goals=[sample_goal()],
            recent_activities=[],
            athlete_stats={},
            db_path=_NO_DB,
        )
        assert "claims database not found" in prompt or "No research evidence" in prompt


class TestRunAnalysisPrompt:
    def test_contains_framework(self):
        prompt = run_analysis_prompt(activity=sample_activity_detail(), db_path=_NO_DB)
        assert "Pace consistency" in prompt
        assert "Heart rate drift" in prompt
        assert "Cadence" in prompt

    def test_contains_evidence_section(self):
        prompt = run_analysis_prompt(activity=sample_activity_detail(), db_path=_NO_DB)
        assert "Research Evidence" in prompt

    def test_includes_activity_data(self):
        prompt = run_analysis_prompt(activity=sample_activity_detail(), db_path=_NO_DB)
        assert "Tempo Run" in prompt
        assert "km 1" in prompt  # splits

    def test_output_format(self):
        prompt = run_analysis_prompt(activity=sample_activity_detail(), db_path=_NO_DB)
        assert "What went well" in prompt
        assert "What to improve" in prompt
        assert "Training context" in prompt


class TestRaceReadinessPrompt:
    def test_contains_framework(self):
        prompt = race_readiness_prompt(
            goals=[sample_goal()],
            recent_activities=sample_activities(),
            athlete_stats=sample_athlete_stats(),
            db_path=_NO_DB,
        )
        assert "Volume adequacy" in prompt
        assert "Key workouts" in prompt
        assert "Taper" in prompt
        assert "VDOT" in prompt

    def test_contains_evidence_section(self):
        prompt = race_readiness_prompt(
            goals=[sample_goal()],
            recent_activities=[],
            athlete_stats={},
            db_path=_NO_DB,
        )
        assert "Research Evidence" in prompt

    def test_readiness_score_requested(self):
        prompt = race_readiness_prompt(goals=[], recent_activities=[], athlete_stats={}, db_path=_NO_DB)
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
        prompt = injury_risk_prompt(weekly_distances=distances, training_load=load, db_path=_NO_DB)
        assert "10% rule" in prompt
        assert "ACWR" in prompt
        assert "Load variability" in prompt

    def test_contains_evidence_section(self):
        prompt = injury_risk_prompt(
            weekly_distances=[30, 30, 30, 30],
            training_load={},
            db_path=_NO_DB,
        )
        assert "Research Evidence" in prompt

    def test_includes_weekly_data(self):
        distances = [30.0, 35.0, 32.0, 40.0]
        load = {"acwr": 1.17}
        prompt = injury_risk_prompt(weekly_distances=distances, training_load=load, db_path=_NO_DB)
        # Distances shown in miles with km in parentheses
        assert "Week 1: 18.6 mi (30.0 km)" in prompt
        assert "Week 4: 24.9 mi (40.0 km)" in prompt

    def test_output_format(self):
        prompt = injury_risk_prompt(weekly_distances=[30, 30, 30, 30], training_load={}, db_path=_NO_DB)
        assert "Risk level" in prompt
        assert "Recommendations" in prompt


class TestFormatEvidence:
    def test_empty_claims(self):
        result = _format_evidence([])
        assert "No research evidence" in result

    def test_formats_claim_text(self):
        claims = [
            {
                "text": "ACWR 0.8-1.3 is optimal",
                "specific_value": "0.8-1.3",
                "category": "training_load",
                "population": "all",
                "confidence": 0.9,
                "paper_id": "paper_a",
                "score": 0.63,
            }
        ]
        result = _format_evidence(claims)
        assert "ACWR 0.8-1.3 is optimal" in result
        assert "value: 0.8-1.3" in result
        assert "paper_a" in result

    def test_handles_null_specific_value(self):
        claims = [
            {
                "text": "Recovery matters",
                "specific_value": None,
                "category": "training_load",
                "population": "all",
                "confidence": 0.8,
                "paper_id": "paper_b",
                "score": 0.56,
            }
        ]
        result = _format_evidence(claims)
        assert "Recovery matters" in result
        assert "value:" not in result
