"""Evaluation tests for injury risk coaching.

Tests profiles with ACWR concerns: returning-from-injury, overreaching,
and injury-risk profiles.

Two modes:
- Default (mocked): scores golden responses against rubrics (deterministic)
- --live-llm: generates coaching via the Anthropic API, scores with LLM judge

Run mocked:   python -m pytest tests/llm_eval/test_injury_risk.py -v
Run live:     python -m pytest tests/llm_eval/test_injury_risk.py -v --live-llm
"""

from __future__ import annotations

import pytest

from pace_ai.prompts.coaching import injury_risk_prompt
from tests.llm_eval.golden_responses import INJURY_RISK_GOLDEN
from tests.llm_eval.profiles import (
    HIGH_RISK_PROFILES,
    INJURY_RETURN_PROFILES,
    RunnerProfile,
)
from tests.llm_eval.rubrics import get_injury_risk_rubric
from tests.llm_eval.scoring import score_deterministic, score_with_judge

# All profiles that have injury risk rubrics
_RISK_PROFILES = INJURY_RETURN_PROFILES + HIGH_RISK_PROFILES


def _build_prompt(profile: RunnerProfile) -> str:
    """Build an injury risk prompt from a profile."""
    return injury_risk_prompt(
        weekly_distances=profile.weekly_distances,
        training_load=profile.acwr,
        recent_activities=profile.recent_activities,
    )


async def _get_llm_response(prompt: str) -> str:
    """Call the Anthropic API to generate a coaching response."""
    import os

    import anthropic

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        pytest.skip("ANTHROPIC_API_KEY not set")

    client = anthropic.AsyncAnthropic(api_key=api_key)
    response = await client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


# ── Parametrized tests ──────────────────────────────────────────────


@pytest.mark.parametrize(
    "profile",
    _RISK_PROFILES,
    ids=[p.id for p in _RISK_PROFILES],
)
class TestInjuryRiskCoaching:
    """Evaluate injury risk coaching for at-risk profiles."""

    @pytest.mark.asyncio()
    async def test_coaching_correctness(self, profile: RunnerProfile, live_llm: bool) -> None:
        """Score injury risk coaching against the profile's rubric."""
        rubric = get_injury_risk_rubric(profile.id)

        if live_llm:
            prompt = _build_prompt(profile)
            response = await _get_llm_response(prompt)

            result = await score_with_judge(
                response=response,
                rubric=rubric,
                profile_id=profile.id,
                profile_description=profile.description,
            )
            assert result.passed, (
                f"Profile {profile.id} failed injury risk eval.\n"
                f"Deterministic: {result.deterministic_score:.0%}\n"
                f"Judge: {result.judge_score:.0%}\n"
                f"Missing required: {[k for k, v in result.required_present.items() if not v]}\n"
                f"Forbidden found: {[k for k, v in result.forbidden_absent.items() if not v]}\n"
                f"Failed criteria: {[k for k, v in result.criteria_scores.items() if not v]}\n"
                f"Judge reasoning:\n{result.judge_reasoning}"
            )
        else:
            golden = INJURY_RISK_GOLDEN.get(profile.id)
            assert golden is not None, f"No golden injury risk response for {profile.id}"

            result = score_deterministic(golden, rubric, profile.id)
            assert result.passed, (
                f"Golden response for {profile.id} failed deterministic checks.\n"
                f"Score: {result.deterministic_score:.0%}\n"
                f"Missing required: {[k for k, v in result.required_present.items() if not v]}\n"
                f"Forbidden found: {[k for k, v in result.forbidden_absent.items() if not v]}"
            )

    def test_golden_response_exists(self, profile: RunnerProfile, live_llm: bool) -> None:
        """Verify every at-risk profile has a golden injury risk response."""
        if live_llm:
            pytest.skip("Golden response check not needed in live mode")
        assert profile.id in INJURY_RISK_GOLDEN, f"Missing golden injury risk response for {profile.id}"

    def test_prompt_generation(self, profile: RunnerProfile, live_llm: bool) -> None:
        """Verify the injury risk prompt can be generated without errors."""
        prompt = _build_prompt(profile)
        assert isinstance(prompt, str)
        assert len(prompt) > 100
        # Verify ACWR data is embedded
        assert "ACWR" in prompt or "acwr" in prompt.lower()

    def test_acwr_data_in_prompt(self, profile: RunnerProfile, live_llm: bool) -> None:
        """Verify the ACWR analysis data appears in the prompt."""
        prompt = _build_prompt(profile)
        # The prompt should contain the risk level
        assert profile.acwr["risk_level"] in prompt.lower() or str(profile.acwr["acwr"]) in prompt
