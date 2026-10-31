"""Unit tests for the eval scoring module.

Tests deterministic scoring, judge response parsing, numeric ratings,
and scorecard output formatters without any API calls.
"""

from __future__ import annotations

from tests.llm_eval.rubrics import BEGINNER_HEALTHY_WEEKLY_PLAN, OVERREACHING_WEEKLY_PLAN
from tests.llm_eval.scoring import (
    CriterionScore,
    ScoringResult,
    _parse_judge_response,
    format_scorecard_json,
    format_scorecard_table,
    format_scoring_report,
    score_deterministic,
)

# ── Deterministic scoring ──────────────────────────────────────────


class TestScoreDeterministic:
    def test_perfect_response_passes(self) -> None:
        response = "This is an easy plan with plenty of rest days."
        result = score_deterministic(response, BEGINNER_HEALTHY_WEEKLY_PLAN, "test_01")
        assert result.passed
        assert result.deterministic_score == 1.0

    def test_missing_required_element_fails(self) -> None:
        response = "This plan has rest days but no mention of difficulty level."
        result = score_deterministic(response, BEGINNER_HEALTHY_WEEKLY_PLAN, "test_02")
        assert not result.passed
        assert result.deterministic_score < 1.0
        assert result.required_present["easy"] is False

    def test_forbidden_element_fails(self) -> None:
        response = "Easy plan with rest days and VO2max intervals for speed."
        result = score_deterministic(response, BEGINNER_HEALTHY_WEEKLY_PLAN, "test_03")
        assert not result.passed
        assert result.forbidden_absent["VO2max intervals"] is False

    def test_empty_rubric_passes(self) -> None:
        from tests.llm_eval.rubrics import Rubric

        empty = Rubric(name="empty", description="Empty rubric")
        result = score_deterministic("any response", empty, "test_04")
        assert result.passed
        assert result.deterministic_score == 1.0

    def test_overreaching_rubric(self) -> None:
        response = "Your ACWR is high. You need to reduce volume immediately."
        result = score_deterministic(response, OVERREACHING_WEEKLY_PLAN, "test_05")
        assert result.passed


# ── Judge response parsing ─────────────────────────────────────────


class TestParseJudgeResponse:
    def test_parses_new_format_with_ratings(self) -> None:
        judge_output = (
            "CRITERION 1: PASS — RATING:4 — Good coverage of rest days.\n"
            "CRITERION 2: FAIL — RATING:2 — Missing intensity distribution.\n"
            "CRITERION 3: PASS — RATING:5 — Excellent pacing guidance.\n"
            "OVERALL: 2/3 criteria passed — MEAN_RATING:3.7"
        )
        details, score = _parse_judge_response(judge_output, 3)
        assert len(details) == 3
        assert details[0].passed is True
        assert details[0].rating == 4
        assert details[1].passed is False
        assert details[1].rating == 2
        assert details[2].passed is True
        assert details[2].rating == 5
        assert score == 2 / 3

    def test_parses_old_format_without_ratings(self) -> None:
        judge_output = "CRITERION 1: PASS — Good coverage.\nCRITERION 2: FAIL — Missing element.\n"
        details, score = _parse_judge_response(judge_output, 2)
        assert len(details) == 2
        assert details[0].passed is True
        assert details[0].rating == 4  # fallback for PASS
        assert details[1].passed is False
        assert details[1].rating == 2  # fallback for FAIL
        assert score == 0.5

    def test_missing_criterion_defaults_to_fail(self) -> None:
        judge_output = "CRITERION 1: PASS — RATING:4 — Good.\n"
        details, _score = _parse_judge_response(judge_output, 3)
        assert len(details) == 3
        assert details[0].passed is True
        # Missing criteria default to fail with rating 1
        assert details[1].passed is False
        assert details[1].rating == 1
        assert details[2].passed is False
        assert details[2].rating == 1

    def test_rating_clamped_to_1_5(self) -> None:
        judge_output = "CRITERION 1: PASS — RATING:9 — Incredible.\n"
        details, _ = _parse_judge_response(judge_output, 1)
        assert details[0].rating == 5  # clamped to max

    def test_empty_response(self) -> None:
        details, score = _parse_judge_response("", 2)
        assert len(details) == 2
        assert all(not d.passed for d in details)
        assert score == 0.0


# ── ScoringResult properties ──────────────────────────────────────


class TestScoringResult:
    def test_total_score_without_judge(self) -> None:
        r = ScoringResult(profile_id="x", rubric_name="y", passed=True, deterministic_score=0.8)
        assert r.total_score == 0.8

    def test_total_score_with_judge(self) -> None:
        r = ScoringResult(
            profile_id="x",
            rubric_name="y",
            passed=True,
            deterministic_score=1.0,
            judge_score=0.8,
        )
        assert r.total_score == 0.9

    def test_mean_rating_empty(self) -> None:
        r = ScoringResult(profile_id="x", rubric_name="y", passed=True)
        assert r.mean_rating == 0.0

    def test_mean_rating_computed(self) -> None:
        r = ScoringResult(
            profile_id="x",
            rubric_name="y",
            passed=True,
            criteria_details=[
                CriterionScore(name="c1", passed=True, rating=4),
                CriterionScore(name="c2", passed=True, rating=5),
                CriterionScore(name="c3", passed=False, rating=2),
            ],
        )
        assert r.mean_rating == (4 + 5 + 2) / 3

    def test_to_dict_includes_computed_fields(self) -> None:
        r = ScoringResult(
            profile_id="x",
            rubric_name="y",
            passed=True,
            deterministic_score=1.0,
            judge_score=0.8,
            gen_model="test-gen",
            judge_model="test-judge",
        )
        d = r.to_dict()
        assert d["total_score"] == 0.9
        assert d["mean_rating"] == 0.0
        assert d["gen_model"] == "test-gen"


# ── Output formatters ─────────────────────────────────────────────


class TestFormatters:
    def _make_results(self) -> list[ScoringResult]:
        return [
            ScoringResult(
                profile_id="01_beginner_m30_healthy",
                rubric_name="beginner_healthy_weekly_plan",
                passed=True,
                deterministic_score=1.0,
                judge_score=0.875,
                gen_model="test-model",
                judge_model="test-judge",
                criteria_details=[
                    CriterionScore(name="c1", passed=True, rating=4, justification="Good."),
                    CriterionScore(name="c2", passed=True, rating=5, justification="Excellent."),
                ],
            ),
            ScoringResult(
                profile_id="07_intermediate_m40_overreaching",
                rubric_name="overreaching_weekly_plan",
                passed=False,
                deterministic_score=0.8,
                judge_score=0.5,
                gen_model="test-model",
                judge_model="test-judge",
                criteria_details=[
                    CriterionScore(name="c1", passed=True, rating=3, justification="OK."),
                    CriterionScore(name="c2", passed=False, rating=2, justification="Missing."),
                ],
            ),
        ]

    def test_format_scoring_report(self) -> None:
        report = format_scoring_report(self._make_results())
        assert "COACHING EVALUATION REPORT" in report
        assert "1/2 profiles passed" in report
        assert "Gen model:   test-model" in report
        assert "[PASS]" in report
        assert "[FAIL]" in report
        assert "Mean rating:" in report

    def test_format_scorecard_json(self) -> None:
        import json

        output = format_scorecard_json(self._make_results())
        data = json.loads(output)
        assert len(data) == 2
        assert data[0]["gen_model"] == "test-model"
        assert data[0]["total_score"] == (1.0 + 0.875) / 2
        assert data[0]["mean_rating"] == (4 + 5) / 2

    def test_format_scorecard_table(self) -> None:
        table = format_scorecard_table(self._make_results())
        assert "| Profile |" in table
        assert "PASS" in table
        assert "FAIL" in table
        assert "1/2 passed" in table
        assert "test-model" in table
