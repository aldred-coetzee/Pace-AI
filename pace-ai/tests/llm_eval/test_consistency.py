"""Consistency evaluation: same input N times → measure structural agreement.

This test verifies that the coaching LLM produces structurally consistent
advice when given identical inputs. It extracts structured fields from each
response and measures agreement across runs.

Live-only (requires --live-llm flag and API key).

Run:  python -m pytest tests/llm_eval/test_consistency.py -v --live-llm
"""

from __future__ import annotations

import re

import pytest

from pace_ai.prompts.coaching import injury_risk_prompt, race_readiness_prompt, weekly_plan_prompt
from tests.llm_eval.profiles import PROFILE_05, PROFILE_07, PROFILE_11, RunnerProfile

# Number of times to run each prompt for consistency measurement
N_RUNS = 3
# Minimum fraction of fields that must agree across all runs
MIN_AGREEMENT = 0.70

# Profiles chosen to cover healthy, overreaching, and injury-risk conditions
_CONSISTENCY_PROFILES = [
    PROFILE_05,  # Intermediate healthy — weekly plan
    PROFILE_07,  # Intermediate overreaching — injury risk
    PROFILE_11,  # Advanced injury risk — race readiness
]


def _extract_structured_fields(response: str, prompt_type: str) -> dict[str, str | bool | None]:
    """Extract structured fields from a coaching response for comparison.

    Returns normalised values for comparison. Fields that can't be extracted
    are set to None (and excluded from agreement calculation).
    """
    text = response.lower()
    fields: dict[str, str | bool | None] = {}

    if prompt_type == "weekly_plan":
        # Does it include a rest day?
        fields["includes_rest_day"] = "rest day" in text or "rest" in text

        # Number of running days mentioned
        day_match = re.search(r"(\d)\s*(?:running|run)\s*days?\s*(?:per|a|/)\s*week", text)
        fields["run_days_per_week"] = day_match.group(1) if day_match else None

        # Does it recommend easy running as majority?
        fields["majority_easy"] = "easy" in text and ("80" in text or "majority" in text or "most" in text)

        # Does it mention long run?
        fields["includes_long_run"] = "long run" in text

        # Does it mention tempo/threshold/intervals?
        fields["includes_quality"] = any(w in text for w in ["tempo", "threshold", "interval"])

    elif prompt_type == "injury_risk":
        # Risk level classification
        if "high" in text and "risk" in text:
            fields["risk_level"] = "high"
        elif "moderate" in text or "elevated" in text:
            fields["risk_level"] = "moderate"
        elif "low" in text and "risk" in text:
            fields["risk_level"] = "low"
        else:
            fields["risk_level"] = None

        # Does it recommend volume reduction?
        fields["recommends_reduction"] = any(w in text for w in ["reduce", "deload", "decrease", "cut back", "lower"])

        # Does it flag ACWR?
        fields["flags_acwr"] = "acwr" in text

        # Does it warn against racing/hard training?
        fields["warns_against_intensity"] = any(
            w in text for w in ["no intensity", "no speed", "easy only", "drop all intensity", "suspend"]
        )

        # Does it provide a timeline?
        fields["provides_timeline"] = any(w in text for w in ["7-10 days", "7-14 days", "1-2 weeks", "week"])

    elif prompt_type == "race_readiness":
        # Readiness assessment direction
        if "not ready" in text or "not race-ready" in text or "inadvisable" in text:
            fields["readiness_direction"] = "not_ready"
        elif "ready" in text or "on track" in text or "strong" in text:
            fields["readiness_direction"] = "ready"
        else:
            fields["readiness_direction"] = None

        # Does it reference ACWR?
        fields["references_acwr"] = "acwr" in text

        # Does it flag risk?
        fields["flags_risk"] = "risk" in text

        # Readiness score extraction (X/10)
        score_match = re.search(r"(\d+)\s*/\s*10", text)
        fields["readiness_score"] = score_match.group(1) if score_match else None

        # Does it provide recommendations?
        fields["provides_recommendations"] = "recommend" in text or "suggestion" in text or "week" in text

    return fields


def _compute_agreement(all_fields: list[dict[str, str | bool | None]]) -> tuple[float, dict[str, bool]]:
    """Compute field-level agreement across N runs.

    Returns (overall_agreement_fraction, {field_name: all_agree}).
    Fields that are None in any run are excluded from the calculation.
    """
    if not all_fields:
        return 0.0, {}

    all_keys = set()
    for f in all_fields:
        all_keys.update(f.keys())

    field_agreement: dict[str, bool] = {}
    for key in sorted(all_keys):
        values = [f.get(key) for f in all_fields]
        # Exclude fields where any run returned None
        non_none = [v for v in values if v is not None]
        if len(non_none) < 2:
            continue
        # All non-None values must agree
        field_agreement[key] = len(set(str(v) for v in non_none)) == 1

    if not field_agreement:
        return 1.0, {}

    agreed = sum(field_agreement.values())
    return agreed / len(field_agreement), field_agreement


# ── Test cases ───────────────────────────────────────────────────────


@pytest.mark.skipif("not config.getoption('--live-llm')", reason="Consistency tests require --live-llm")
class TestConsistency:
    """Run identical prompts N times and measure structural agreement."""

    @pytest.mark.asyncio()
    async def test_weekly_plan_consistency(self, gen_model: str) -> None:
        """Weekly plan for a healthy intermediate runner should be consistent."""
        profile = PROFILE_05
        prompt = weekly_plan_prompt(
            goals=profile.goals,
            recent_activities=profile.recent_activities,
            athlete_stats=profile.athlete_stats,
            training_zones=profile.zones if profile.zones else None,
            training_load=profile.acwr if profile.acwr else None,
            athlete_context={
                "age": profile.age,
                "gender": profile.gender,
                "level": profile.level,
                "condition": profile.condition,
                "description": profile.description,
            },
        )
        await self._run_consistency_check(prompt, "weekly_plan", profile, gen_model)

    @pytest.mark.asyncio()
    async def test_injury_risk_consistency(self, gen_model: str) -> None:
        """Injury risk for an overreaching runner should be consistent."""
        profile = PROFILE_07
        prompt = injury_risk_prompt(
            weekly_distances=profile.weekly_distances,
            training_load=profile.acwr,
            recent_activities=profile.recent_activities,
        )
        await self._run_consistency_check(prompt, "injury_risk", profile, gen_model)

    @pytest.mark.asyncio()
    async def test_race_readiness_consistency(self, gen_model: str) -> None:
        """Race readiness for a high-risk runner should be consistent."""
        profile = PROFILE_11
        prompt = race_readiness_prompt(
            goals=profile.goals,
            recent_activities=profile.recent_activities,
            athlete_stats=profile.athlete_stats,
            training_load=profile.acwr if profile.acwr else None,
            training_zones=profile.zones if profile.zones else None,
            race_prediction=profile.race_prediction if profile.race_prediction else None,
        )
        await self._run_consistency_check(prompt, "race_readiness", profile, gen_model)

    async def _run_consistency_check(
        self,
        prompt: str,
        prompt_type: str,
        profile: RunnerProfile,
        gen_model: str,
    ) -> None:
        """Run the prompt N times and assert field agreement meets threshold."""
        from tests.llm_eval.llm_client import complete

        responses: list[str] = []
        for _ in range(N_RUNS):
            resp = await complete(model=gen_model, prompt=prompt)
            responses.append(resp)

        all_fields = [_extract_structured_fields(r, prompt_type) for r in responses]
        agreement, field_details = _compute_agreement(all_fields)

        disagreed = [k for k, v in field_details.items() if not v]

        assert agreement >= MIN_AGREEMENT, (
            f"Consistency check failed for {profile.id} ({prompt_type}).\n"
            f"Model: {gen_model}\n"
            f"Agreement: {agreement:.0%} (threshold: {MIN_AGREEMENT:.0%})\n"
            f"Disagreeing fields: {disagreed}\n"
            f"Field details: {field_details}\n"
            f"Extracted fields per run:\n" + "\n".join(f"  Run {i + 1}: {f}" for i, f in enumerate(all_fields))
        )
