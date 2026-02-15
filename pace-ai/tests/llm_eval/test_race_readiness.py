"""Evaluation tests for race readiness coaching.

Tests all 16 profiles for race readiness assessment quality.

Two modes:
- Default (mocked): scores golden responses against rubrics (deterministic)
- --live-llm: generates coaching via OpenRouter/Anthropic API, scores with LLM judge

Model selection (live mode only):
  --gen-model MODEL     Generation model (env: EVAL_GEN_MODEL)
  --judge-model MODEL   Judge model (env: EVAL_JUDGE_MODEL)

Run mocked:   python -m pytest tests/llm_eval/test_race_readiness.py -v
Run live:     python -m pytest tests/llm_eval/test_race_readiness.py -v --live-llm
Custom model: python -m pytest tests/llm_eval/test_race_readiness.py -v --live-llm --gen-model deepseek/deepseek-v3.2
"""

from __future__ import annotations

import pytest

from pace_ai.prompts.coaching import race_readiness_prompt
from tests.llm_eval.golden_responses import RACE_READINESS_GOLDEN
from tests.llm_eval.profiles import ALL_PROFILES, RunnerProfile
from tests.llm_eval.rubrics import get_race_readiness_rubric
from tests.llm_eval.scoring import score_deterministic, score_with_judge


def _build_prompt(profile: RunnerProfile) -> str:
    """Build a race readiness prompt from a profile."""
    return race_readiness_prompt(
        goals=profile.goals,
        recent_activities=profile.recent_activities,
        athlete_stats=profile.athlete_stats,
        training_load=profile.acwr if profile.acwr else None,
        training_zones=profile.zones if profile.zones else None,
        race_prediction=profile.race_prediction if profile.race_prediction else None,
    )


async def _get_llm_response(prompt: str, model: str) -> str:
    """Call the LLM API to generate a coaching response."""
    from tests.llm_eval.llm_client import complete

    return await complete(model=model, prompt=prompt)


# ── Parametrized tests ──────────────────────────────────────────────


@pytest.mark.parametrize(
    "profile",
    ALL_PROFILES,
    ids=[p.id for p in ALL_PROFILES],
)
class TestRaceReadinessCoaching:
    """Evaluate race readiness coaching for all 16 profiles."""

    @pytest.mark.asyncio()
    async def test_coaching_correctness(
        self, profile: RunnerProfile, live_llm: bool, gen_model: str, judge_model: str
    ) -> None:
        """Score race readiness coaching against the profile's rubric.

        In mocked mode: scores the golden response (should always pass).
        In live mode: generates a response via API, scores with deterministic
        checks + LLM judge.
        """
        rubric = get_race_readiness_rubric(profile.id)

        if live_llm:
            prompt = _build_prompt(profile)
            response = await _get_llm_response(prompt, model=gen_model)

            result = await score_with_judge(
                response=response,
                rubric=rubric,
                profile_id=profile.id,
                profile_description=profile.description,
                judge_model=judge_model,
                gen_model=gen_model,
            )
            assert result.passed, (
                f"Profile {profile.id} failed race readiness eval.\n"
                f"Gen model: {gen_model}\n"
                f"Judge model: {judge_model}\n"
                f"Deterministic: {result.deterministic_score:.0%}\n"
                f"Judge: {result.judge_score:.0%}  |  Mean rating: {result.mean_rating:.1f}/5\n"
                f"Missing required: {[k for k, v in result.required_present.items() if not v]}\n"
                f"Forbidden found: {[k for k, v in result.forbidden_absent.items() if not v]}\n"
                f"Failed criteria: {[k for k, v in result.criteria_scores.items() if not v]}\n"
                f"Judge reasoning:\n{result.judge_reasoning}"
            )
        else:
            # Mocked mode: score the golden response
            golden = RACE_READINESS_GOLDEN.get(profile.id)
            assert golden is not None, f"No golden race readiness response for {profile.id}"

            result = score_deterministic(golden, rubric, profile.id)
            assert result.passed, (
                f"Golden response for {profile.id} failed deterministic checks.\n"
                f"Score: {result.deterministic_score:.0%}\n"
                f"Missing required: {[k for k, v in result.required_present.items() if not v]}\n"
                f"Forbidden found: {[k for k, v in result.forbidden_absent.items() if not v]}"
            )

    def test_golden_response_exists(self, profile: RunnerProfile, live_llm: bool) -> None:
        """Verify every profile has a golden race readiness response."""
        if live_llm:
            pytest.skip("Golden response check not needed in live mode")
        assert profile.id in RACE_READINESS_GOLDEN, f"Missing golden race readiness response for {profile.id}"

    def test_prompt_generation(self, profile: RunnerProfile, live_llm: bool) -> None:
        """Verify the race readiness prompt can be generated without errors."""
        prompt = _build_prompt(profile)
        assert isinstance(prompt, str)
        assert len(prompt) > 100
        # Verify goal data is embedded in the prompt
        if profile.goals:
            assert profile.goals[0]["race_type"] in prompt

    def test_training_load_in_prompt(self, profile: RunnerProfile, live_llm: bool) -> None:
        """Verify the training load data appears in the prompt."""
        prompt = _build_prompt(profile)
        # The prompt should contain ACWR data when available
        if profile.acwr:
            assert "ACWR" in prompt or "acwr" in prompt.lower() or str(profile.acwr["acwr"]) in prompt
