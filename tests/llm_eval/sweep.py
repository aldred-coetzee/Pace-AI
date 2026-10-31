"""Model sweep runner — evaluate coaching quality across multiple LLMs.

Runs the PLAN eval (the app's real prompt, via `claude -p`) over all 16
profiles for each model, producing a comparison scorecard with per-model pass
rates and mean ratings.

Usage:
    # Run the default sweep (haiku, sonnet, opus)
    python -m tests.llm_eval.sweep

    # Custom models (comma-separated)
    python -m tests.llm_eval.sweep --models "haiku,sonnet"

    # Override judge model
    python -m tests.llm_eval.sweep --judge sonnet

    # Output JSON instead of table
    python -m tests.llm_eval.sweep --format json

Needs the `claude` CLI logged in on the box; no API keys.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import time
from dataclasses import dataclass, field
from typing import Any

from tests.llm_eval.app_prompt import build_app_plan_prompt, plan_text
from tests.llm_eval.llm_client import complete
from tests.llm_eval.profiles import ALL_PROFILES, RunnerProfile
from tests.llm_eval.rubrics import get_weekly_plan_rubric
from tests.llm_eval.scoring import ScoringResult, score_with_judge

# ── Models ──────────────────────────────────────────────────────────

# Claude Code aliases, run through `claude -p`. Cost is the subscription's, so
# there is no per-token price table; the tier is just a label for the report.
MODEL_TIERS: dict[str, dict[str, Any]] = {
    "haiku": {"tier": "budget", "label": "Haiku"},
    "sonnet": {"tier": "mid", "label": "Sonnet"},
    "opus": {"tier": "premium", "label": "Opus"},
}

DEFAULT_MODELS = list(MODEL_TIERS.keys())
DEFAULT_JUDGE = "haiku"


@dataclass
class ModelResult:
    """Aggregated eval results for a single model."""

    model: str
    tier: str
    label: str
    weekly_plan_results: list[ScoringResult] = field(default_factory=list)
    elapsed_seconds: float = 0.0

    @property
    def all_results(self) -> list[ScoringResult]:
        return self.weekly_plan_results

    @property
    def total_pass_rate(self) -> float:
        results = self.all_results
        if not results:
            return 0.0
        return sum(1 for r in results if r.passed) / len(results)

    @property
    def mean_rating(self) -> float:
        results = [r for r in self.all_results if r.mean_rating > 0]
        if not results:
            return 0.0
        return sum(r.mean_rating for r in results) / len(results)

    @property
    def mean_det_score(self) -> float:
        results = self.all_results
        if not results:
            return 0.0
        return sum(r.deterministic_score for r in results) / len(results)

    @property
    def mean_judge_score(self) -> float:
        results = [r for r in self.all_results if r.judge_score > 0]
        if not results:
            return 0.0
        return sum(r.judge_score for r in results) / len(results)

    def to_dict(self) -> dict[str, Any]:
        return {
            "model": self.model,
            "tier": self.tier,
            "label": self.label,
            "total_profiles": len(self.all_results),
            "passed": sum(1 for r in self.all_results if r.passed),
            "pass_rate": self.total_pass_rate,
            "mean_det_score": self.mean_det_score,
            "mean_judge_score": self.mean_judge_score,
            "mean_rating": self.mean_rating,
            "elapsed_seconds": self.elapsed_seconds,
            "weekly_plan_results": [r.to_dict() for r in self.weekly_plan_results],
        }


# ── Eval runner ─────────────────────────────────────────────────────


async def _run_weekly_plan_eval(profile: RunnerProfile, gen_model: str, judge_model: str) -> ScoringResult:
    """Run a single weekly plan eval for a profile."""
    system, prompt = build_app_plan_prompt(profile)
    response = plan_text(await complete(model=gen_model, system=system, prompt=prompt))
    rubric = get_weekly_plan_rubric(profile.id)
    return await score_with_judge(
        response=response,
        rubric=rubric,
        profile_id=profile.id,
        profile_description=profile.description,
        judge_model=judge_model,
        gen_model=gen_model,
    )


async def evaluate_model(gen_model: str, judge_model: str) -> ModelResult:
    """Run the full eval suite for a single generation model."""
    info = MODEL_TIERS.get(gen_model, {"tier": "unknown", "label": gen_model})
    result = ModelResult(model=gen_model, tier=info["tier"], label=info["label"])

    start = time.monotonic()
    print(f"  Evaluating {info['label']} ({gen_model})...", flush=True)

    # PLAN — all 16 profiles
    for profile in ALL_PROFILES:
        try:
            sr = await _run_weekly_plan_eval(profile, gen_model, judge_model)
            result.weekly_plan_results.append(sr)
            status = "PASS" if sr.passed else "FAIL"
            print(
                f"    [{status}] weekly_plan/{profile.id}  (det={sr.deterministic_score:.0%} "
                f"judge={sr.judge_score:.0%} rating={sr.mean_rating:.1f})",
                flush=True,
            )
        except Exception as exc:
            print(f"    [ERR]  weekly_plan/{profile.id}: {exc}", flush=True)

    result.elapsed_seconds = time.monotonic() - start
    print(
        f"  Done: {result.total_pass_rate:.0%} pass rate, "
        f"{result.mean_rating:.1f}/5 mean rating, "
        f"{result.elapsed_seconds:.0f}s",
        flush=True,
    )
    return result


# ── Output formatters ───────────────────────────────────────────────


def format_sweep_table(results: list[ModelResult], judge_model: str) -> str:
    """Render a markdown comparison table across models."""
    lines = [
        f"# Model Sweep Results  (judge: `{judge_model}`)\n",
        "| Tier | Model | Pass Rate | Det | Judge | Rating | Time |",
        "|------|-------|-----------|-----|-------|--------|------|",
    ]
    for r in sorted(results, key=lambda x: x.mean_rating, reverse=True):
        lines.append(
            f"| {r.tier} | {r.label} | {r.total_pass_rate:.0%} "
            f"| {r.mean_det_score:.0%} | {r.mean_judge_score:.0%} "
            f"| {r.mean_rating:.1f}/5 | {r.elapsed_seconds:.0f}s |"
        )

    lines.append("")

    # Recommendation: DEFAULT_MODELS runs cheapest first, so the first model that
    # clears the bar is the best value.
    best = max(results, key=lambda x: x.mean_rating) if results else None
    cheapest_passing = next((r for r in results if r.total_pass_rate >= 0.75), None)

    if best:
        lines.append(f"**Best quality:** {best.label} ({best.mean_rating:.1f}/5)")
    if cheapest_passing and cheapest_passing != best:
        lines.append(
            f"**Best value:** {cheapest_passing.label} "
            f"({cheapest_passing.total_pass_rate:.0%} pass, cheapest to clear 75%)"
        )

    return "\n".join(lines)


def format_sweep_json(results: list[ModelResult], judge_model: str) -> str:
    """Serialise full sweep results to JSON."""
    return json.dumps(
        {
            "judge_model": judge_model,
            "models": [r.to_dict() for r in results],
        },
        indent=2,
        default=str,
    )


# ── CLI ─────────────────────────────────────────────────────────────


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run model sweep across the eval suite.")
    parser.add_argument(
        "--models",
        default=None,
        help=f"Comma-separated list of model IDs (default: {', '.join(DEFAULT_MODELS)})",
    )
    parser.add_argument("--judge", default=DEFAULT_JUDGE, help=f"Judge model (default: {DEFAULT_JUDGE})")
    parser.add_argument("--format", choices=["table", "json"], default="table", help="Output format")
    return parser.parse_args()


async def _main() -> None:
    args = _parse_args()
    models = [m.strip() for m in args.models.split(",")] if args.models else DEFAULT_MODELS
    judge = args.judge

    print(f"Sweep: {len(models)} models, judge={judge}\n", flush=True)

    results: list[ModelResult] = []
    for model in models:
        mr = await evaluate_model(model, judge)
        results.append(mr)
        print("", flush=True)

    if args.format == "json":
        print(format_sweep_json(results, judge))
    else:
        print(format_sweep_table(results, judge))


if __name__ == "__main__":
    asyncio.run(_main())
