"""Evaluation tests for weekly training plan coaching.

Two modes:
- Default (mocked): scores golden responses against rubrics (deterministic)
- --live-llm: sends the app's real PLAN prompt (built by tests/llm_eval/app_prompt.py
  from the profile) through `claude -p`, flattens the JSON plan to text and scores
  it with deterministic checks plus an LLM judge

Model selection (live mode only):
  --gen-model MODEL     Generation model (env: EVAL_GEN_MODEL; default: the app's PLAN model)
  --judge-model MODEL   Judge model (env: EVAL_JUDGE_MODEL; default: haiku)
Models are Claude Code aliases (haiku, sonnet, opus) or full ids.

Run mocked:   python -m pytest tests/llm_eval/test_weekly_plan.py -v
Run live:     python -m pytest tests/llm_eval/test_weekly_plan.py -v --live-llm
Custom model: python -m pytest tests/llm_eval/test_weekly_plan.py -v --live-llm --gen-model opus
"""

from __future__ import annotations

import pytest

from tests.llm_eval.app_prompt import build_app_plan_prompt, plan_text
from tests.llm_eval.golden_responses import WEEKLY_PLAN_GOLDEN
from tests.llm_eval.profiles import ALL_PROFILES, RunnerProfile
from tests.llm_eval.rubrics import get_weekly_plan_rubric
from tests.llm_eval.scoring import score_deterministic, score_with_judge


def _build_prompt(profile: RunnerProfile) -> tuple[str, str]:
    """(system, user) prompt exactly as the app's /plan route builds them."""
    return build_app_plan_prompt(profile)


async def _get_llm_response(system: str, prompt: str, model: str) -> str:
    """Run the app's PLAN prompt through `claude -p` and flatten the JSON plan to text."""
    from tests.llm_eval.llm_client import complete

    return plan_text(await complete(model=model, system=system, prompt=prompt))


# ── Parametrized tests ──────────────────────────────────────────────


@pytest.mark.parametrize(
    "profile",
    ALL_PROFILES,
    ids=[p.id for p in ALL_PROFILES],
)
class TestWeeklyPlanCoaching:
    """Evaluate weekly plan coaching for all 16 profiles."""

    @pytest.mark.asyncio()
    async def test_coaching_correctness(
        self, profile: RunnerProfile, live_llm: bool, gen_model: str, judge_model: str
    ) -> None:
        """Score coaching response against the profile's rubric.

        In mocked mode: scores the golden response (should always pass).
        In live mode: generates a response via API, scores with deterministic
        checks + LLM judge.
        """
        rubric = get_weekly_plan_rubric(profile.id)

        if live_llm:
            system, prompt = _build_prompt(profile)
            response = await _get_llm_response(system, prompt, model=gen_model)

            result = await score_with_judge(
                response=response,
                rubric=rubric,
                profile_id=profile.id,
                profile_description=profile.description,
                judge_model=judge_model,
                gen_model=gen_model,
            )
            assert result.passed, (
                f"Profile {profile.id} failed coaching eval.\n"
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
            golden = WEEKLY_PLAN_GOLDEN.get(profile.id)
            assert golden is not None, f"No golden response for {profile.id}"

            result = score_deterministic(golden, rubric, profile.id)
            assert result.passed, (
                f"Golden response for {profile.id} failed deterministic checks.\n"
                f"Score: {result.deterministic_score:.0%}\n"
                f"Missing required: {[k for k, v in result.required_present.items() if not v]}\n"
                f"Forbidden found: {[k for k, v in result.forbidden_absent.items() if not v]}"
            )

    def test_golden_response_exists(self, profile: RunnerProfile, live_llm: bool) -> None:
        """Verify every profile has a golden response."""
        if live_llm:
            pytest.skip("Golden response check not needed in live mode")
        assert profile.id in WEEKLY_PLAN_GOLDEN, f"Missing golden response for {profile.id}"

    def test_prompt_generation(self, profile: RunnerProfile, live_llm: bool) -> None:
        """Verify the prompt can be generated without errors."""
        system, prompt = _build_prompt(profile)
        assert prompt.startswith("Create a training plan for ")
        assert len(system) > 100
        # The athlete's goal reaches the prompt through the athlete facts.
        assert f"Goal: {profile.goals[0]['race_type']}" in system
        assert "## Current Status" in system
