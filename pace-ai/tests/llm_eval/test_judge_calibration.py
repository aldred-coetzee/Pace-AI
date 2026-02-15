"""Judge calibration tests — verify scoring system discriminates good from bad.

Uses synthetic responses (known-good, known-bad, edge-case) to validate that:
1. Deterministic scoring catches required/forbidden element violations
2. LLM judge (in live mode) rates good responses higher than bad ones
3. Numeric ratings (1-5) provide meaningful separation

These tests run in both mocked and live modes:
- Mocked: validates deterministic scoring only (fast, free)
- --live-llm: validates full judge pipeline including numeric ratings

Run:  python -m pytest tests/llm_eval/test_judge_calibration.py -v
Live: python -m pytest tests/llm_eval/test_judge_calibration.py -v --live-llm
"""

from __future__ import annotations

import pytest

from tests.llm_eval.rubrics import BEGINNER_HEALTHY_WEEKLY_PLAN, OVERREACHING_WEEKLY_PLAN
from tests.llm_eval.scoring import score_deterministic, score_with_judge

# ── Synthetic responses ─────────────────────────────────────────────

# A good beginner plan — hits all required elements, avoids forbidden ones
GOOD_BEGINNER_RESPONSE = """\
## Weekly Training Plan — Beginner Runner

### Day-by-Day Plan

- **Monday**: Rest day — full recovery
- **Tuesday**: Easy run — 4 km at conversational pace
- **Wednesday**: Rest or light walk
- **Thursday**: Easy run — 4.5 km at conversational pace
- **Saturday**: Long easy run — 6 km at relaxed pace
- **Sunday**: Rest day

### Weekly Summary

- Weekly total: 14.5 km (5% increase)
- Intensity distribution: 100% easy effort
- All running at conversational pace
- 3 rest days included for recovery
"""

# A bad beginner plan — includes forbidden elements, misses required ones
BAD_BEGINNER_RESPONSE = """\
## Weekly Training Plan — Beginner Runner

### Day-by-Day Plan

- **Monday**: VO2max intervals — 6x400m at max effort
- **Tuesday**: Tempo run at lactate threshold test pace
- **Wednesday**: Race pace intervals — 4x800m
- **Thursday**: Hill sprints
- **Friday**: Long run — 15 km
- **Saturday**: Recovery jog
- **Sunday**: Cross-training

### Notes
Push hard and make every session count!
"""

# Edge case: hits required words but also includes forbidden ones
MIXED_BEGINNER_RESPONSE = """\
## Weekly Plan

A plan with easy running and rest days.

Start with VO2max intervals on Monday to test fitness, then switch to
easy running for the rest of the week. Include a lactate threshold test
mid-week to establish baseline paces.

### Summary
- 3 easy days, 1 rest day, 1 interval day
"""

# Good overreaching response — correctly identifies high ACWR
GOOD_OVERREACH_RESPONSE = """\
## Training Load Alert

Your ACWR is dangerously high at 1.6. You need to reduce volume immediately.

### Immediate Action Plan

This week is a mandatory deload. Your body has been under significant strain
from the recent volume spike, and continuing at this level puts you at high
risk of injury.

- **Reduce volume by 40%** from last week
- Only easy running at conversational pace
- Include 3 rest days minimum
- No speed work, no tempo runs
- Monitor for any pain or excessive fatigue

The ACWR spike means your acute load has far exceeded what your body is
adapted to. We need to bring this back to the safe 0.8-1.3 range.
"""

# Bad overreaching response — tells runner to maintain current volume
BAD_OVERREACH_RESPONSE = """\
## Weekly Training Plan

Great training block! Your fitness is really coming along.

Keep up the volume and maintain current training load. You can push through
any tiredness — that's just fitness building. Consider adding some speed work
this week to capitalise on your fitness gains.

- **Monday**: Tempo run — 8 km
- **Tuesday**: Intervals — 6x1000m
- **Wednesday**: Easy run
- **Thursday**: Hill repeats
- **Friday**: Long run — 18 km
- **Saturday**: Recovery
- **Sunday**: Easy run
"""


# ── Deterministic calibration ──────────────────────────────────────


class TestDeterministicCalibration:
    """Verify deterministic scoring separates good from bad responses."""

    def test_good_beginner_passes(self) -> None:
        result = score_deterministic(GOOD_BEGINNER_RESPONSE, BEGINNER_HEALTHY_WEEKLY_PLAN, "calibration_good")
        assert result.passed, (
            f"Good beginner response should pass.\n"
            f"Missing required: {[k for k, v in result.required_present.items() if not v]}\n"
            f"Forbidden found: {[k for k, v in result.forbidden_absent.items() if not v]}"
        )
        assert result.deterministic_score == 1.0

    def test_bad_beginner_fails(self) -> None:
        result = score_deterministic(BAD_BEGINNER_RESPONSE, BEGINNER_HEALTHY_WEEKLY_PLAN, "calibration_bad")
        assert not result.passed, "Bad beginner response should fail deterministic checks."
        assert result.deterministic_score < 1.0
        # Should flag forbidden elements
        forbidden_violations = [k for k, v in result.forbidden_absent.items() if not v]
        assert len(forbidden_violations) > 0, "Bad response should trigger at least one forbidden element."

    def test_mixed_response_fails(self) -> None:
        result = score_deterministic(MIXED_BEGINNER_RESPONSE, BEGINNER_HEALTHY_WEEKLY_PLAN, "calibration_mixed")
        assert not result.passed, "Mixed response with forbidden elements should fail."
        # Required elements present (easy, rest)
        assert result.required_present.get("easy", False)
        assert result.required_present.get("rest", False)
        # But forbidden elements also present
        forbidden_violations = [k for k, v in result.forbidden_absent.items() if not v]
        assert len(forbidden_violations) > 0

    def test_good_overreach_passes(self) -> None:
        result = score_deterministic(GOOD_OVERREACH_RESPONSE, OVERREACHING_WEEKLY_PLAN, "calibration_overreach_good")
        assert result.passed, (
            f"Good overreaching response should pass.\n"
            f"Missing required: {[k for k, v in result.required_present.items() if not v]}\n"
            f"Forbidden found: {[k for k, v in result.forbidden_absent.items() if not v]}"
        )

    def test_bad_overreach_fails(self) -> None:
        result = score_deterministic(BAD_OVERREACH_RESPONSE, OVERREACHING_WEEKLY_PLAN, "calibration_overreach_bad")
        assert not result.passed, "Bad overreaching response should fail."

    def test_score_separation(self) -> None:
        """Good responses should score strictly higher than bad ones."""
        good = score_deterministic(GOOD_BEGINNER_RESPONSE, BEGINNER_HEALTHY_WEEKLY_PLAN, "good")
        bad = score_deterministic(BAD_BEGINNER_RESPONSE, BEGINNER_HEALTHY_WEEKLY_PLAN, "bad")
        assert good.deterministic_score > bad.deterministic_score, (
            f"Good ({good.deterministic_score:.2f}) should score higher than bad ({bad.deterministic_score:.2f})."
        )


# ── Live judge calibration (only runs with --live-llm) ─────────────


class TestJudgeCalibration:
    """Verify LLM judge provides meaningful separation between good and bad responses."""

    @pytest.mark.asyncio()
    async def test_good_response_rated_higher(self, live_llm: bool, judge_model: str) -> None:
        """Good response should receive higher judge score + rating than bad one."""
        if not live_llm:
            pytest.skip("Judge calibration requires --live-llm")

        good_result = await score_with_judge(
            response=GOOD_BEGINNER_RESPONSE,
            rubric=BEGINNER_HEALTHY_WEEKLY_PLAN,
            profile_id="calibration_good",
            profile_description="Healthy beginner runner, 30 years old, training for 5K.",
            judge_model=judge_model,
            gen_model="synthetic",
        )
        bad_result = await score_with_judge(
            response=BAD_BEGINNER_RESPONSE,
            rubric=BEGINNER_HEALTHY_WEEKLY_PLAN,
            profile_id="calibration_bad",
            profile_description="Healthy beginner runner, 30 years old, training for 5K.",
            judge_model=judge_model,
            gen_model="synthetic",
        )

        assert good_result.judge_score > bad_result.judge_score, (
            f"Good ({good_result.judge_score:.0%}) should score higher than bad ({bad_result.judge_score:.0%})."
        )
        assert good_result.mean_rating > bad_result.mean_rating, (
            f"Good rating ({good_result.mean_rating:.1f}) should be higher than bad ({bad_result.mean_rating:.1f})."
        )

    @pytest.mark.asyncio()
    async def test_good_response_passes_judge(self, live_llm: bool, judge_model: str) -> None:
        """Good synthetic response should pass the judge threshold."""
        if not live_llm:
            pytest.skip("Judge calibration requires --live-llm")

        result = await score_with_judge(
            response=GOOD_BEGINNER_RESPONSE,
            rubric=BEGINNER_HEALTHY_WEEKLY_PLAN,
            profile_id="calibration_good",
            profile_description="Healthy beginner runner, 30 years old, training for 5K.",
            judge_model=judge_model,
            gen_model="synthetic",
        )
        assert result.judge_score >= 0.75, f"Good response judge score ({result.judge_score:.0%}) should be >= 75%."

    @pytest.mark.asyncio()
    async def test_bad_response_fails_judge(self, live_llm: bool, judge_model: str) -> None:
        """Bad synthetic response should fail the judge threshold."""
        if not live_llm:
            pytest.skip("Judge calibration requires --live-llm")

        result = await score_with_judge(
            response=BAD_BEGINNER_RESPONSE,
            rubric=BEGINNER_HEALTHY_WEEKLY_PLAN,
            profile_id="calibration_bad",
            profile_description="Healthy beginner runner, 30 years old, training for 5K.",
            judge_model=judge_model,
            gen_model="synthetic",
        )
        assert result.judge_score < 0.75, f"Bad response judge score ({result.judge_score:.0%}) should be < 75%."

    @pytest.mark.asyncio()
    async def test_numeric_ratings_populated(self, live_llm: bool, judge_model: str) -> None:
        """Verify judge returns parseable 1-5 ratings."""
        if not live_llm:
            pytest.skip("Judge calibration requires --live-llm")

        result = await score_with_judge(
            response=GOOD_BEGINNER_RESPONSE,
            rubric=BEGINNER_HEALTHY_WEEKLY_PLAN,
            profile_id="calibration_ratings",
            profile_description="Healthy beginner runner, 30 years old, training for 5K.",
            judge_model=judge_model,
            gen_model="synthetic",
        )
        assert len(result.criteria_details) > 0, "Judge should return criterion details."
        for d in result.criteria_details:
            assert 1 <= d.rating <= 5, f"{d.name} rating {d.rating} out of 1-5 range."
            assert d.justification, f"{d.name} missing justification."
        assert result.mean_rating > 0, "Mean rating should be populated."
