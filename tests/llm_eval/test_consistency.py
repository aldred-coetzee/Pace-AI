"""Consistency evaluation: same input N times → measure structural agreement.

This test verifies that the PLAN agent (the app's real prompt, via `claude -p`)
produces structurally consistent plans when given identical inputs. It extracts structured fields from each
response and measures agreement across runs.

Live-only (requires --live-llm; calls `claude -p`).

Run:  python -m pytest tests/llm_eval/test_consistency.py -v --live-llm
"""

from __future__ import annotations

import re

import pytest

from tests.llm_eval.app_prompt import build_app_plan_prompt, plan_text
from tests.llm_eval.profiles import PROFILE_05, RunnerProfile

# Number of times to run each prompt for consistency measurement
N_RUNS = 3
# Minimum fraction of fields that must agree across all runs
MIN_AGREEMENT = 0.70


def _extract_structured_fields(response: str) -> dict[str, str | bool | None]:
    """Extract structured fields from a coaching response for comparison.

    Returns normalised values for comparison. Fields that can't be extracted
    are set to None (and excluded from agreement calculation).
    """
    text = response.lower()
    fields: dict[str, str | bool | None] = {}

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
    """Run the app's PLAN prompt N times and measure structural agreement."""

    @pytest.mark.asyncio()
    async def test_weekly_plan_consistency(self, gen_model: str) -> None:
        """Weekly plan for a healthy intermediate runner should be consistent."""
        await self._run_consistency_check(PROFILE_05, gen_model)

    async def _run_consistency_check(self, profile: RunnerProfile, gen_model: str) -> None:
        """Run the prompt N times and assert field agreement meets threshold."""
        from tests.llm_eval.llm_client import complete

        system, prompt = build_app_plan_prompt(profile)
        responses: list[str] = []
        for _ in range(N_RUNS):
            responses.append(plan_text(await complete(model=gen_model, system=system, prompt=prompt)))

        all_fields = [_extract_structured_fields(r) for r in responses]
        agreement, field_details = _compute_agreement(all_fields)

        disagreed = [k for k, v in field_details.items() if not v]

        assert agreement >= MIN_AGREEMENT, (
            f"Consistency check failed for {profile.id}.\n"
            f"Model: {gen_model}\n"
            f"Agreement: {agreement:.0%} (threshold: {MIN_AGREEMENT:.0%})\n"
            f"Disagreeing fields: {disagreed}\n"
            f"Field details: {field_details}\n"
            f"Extracted fields per run:\n" + "\n".join(f"  Run {i + 1}: {f}" for i, f in enumerate(all_fields))
        )
