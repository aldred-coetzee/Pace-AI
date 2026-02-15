"""Model sweep runner — evaluate coaching quality across multiple LLMs.

Runs the full eval suite against each model in a tier list, producing a
comparison scorecard with per-model pass rates, mean ratings, and cost
estimates.

Usage:
    # Run the default 4-model sweep
    python -m tests.llm_eval.sweep

    # Custom models (comma-separated)
    python -m tests.llm_eval.sweep --models "qwen/qwen3-235b-a22b:free,deepseek/deepseek-v3.2"

    # Override judge model
    python -m tests.llm_eval.sweep --judge claude-haiku-4-5-20251001

    # Output JSON instead of table
    python -m tests.llm_eval.sweep --format json

Requires OPENROUTER_API_KEY or ANTHROPIC_API_KEY.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import time
from dataclasses import dataclass, field
from typing import Any

from pace_ai.prompts.coaching import injury_risk_prompt, weekly_plan_prompt
from tests.llm_eval.llm_client import complete
from tests.llm_eval.profiles import ALL_PROFILES, HIGH_RISK_PROFILES, INJURY_RETURN_PROFILES, RunnerProfile
from tests.llm_eval.rubrics import get_injury_risk_rubric, get_weekly_plan_rubric
from tests.llm_eval.scoring import ScoringResult, score_with_judge

# ── Model tiers ─────────────────────────────────────────────────────

MODEL_TIERS: dict[str, dict[str, Any]] = {
    "qwen/qwen3-235b-a22b:free": {
        "tier": "free",
        "label": "Qwen3 235B (free)",
        "input_cost_per_m": 0.0,
        "output_cost_per_m": 0.0,
    },
    "deepseek/deepseek-v3.2": {
        "tier": "budget",
        "label": "DeepSeek V3.2",
        "input_cost_per_m": 0.14,
        "output_cost_per_m": 0.28,
    },
    "google/gemini-2.5-pro-preview-05-06": {
        "tier": "mid",
        "label": "Gemini 2.5 Pro",
        "input_cost_per_m": 1.25,
        "output_cost_per_m": 10.0,
    },
    "anthropic/claude-sonnet-4-5-20250929": {
        "tier": "premium",
        "label": "Claude Sonnet 4.5",
        "input_cost_per_m": 3.0,
        "output_cost_per_m": 15.0,
    },
}

DEFAULT_MODELS = list(MODEL_TIERS.keys())
DEFAULT_JUDGE = "claude-haiku-4-5-20251001"

_RISK_PROFILES = INJURY_RETURN_PROFILES + HIGH_RISK_PROFILES


@dataclass
class ModelResult:
    """Aggregated eval results for a single model."""

    model: str
    tier: str
    label: str
    weekly_plan_results: list[ScoringResult] = field(default_factory=list)
    injury_risk_results: list[ScoringResult] = field(default_factory=list)
    elapsed_seconds: float = 0.0

    @property
    def all_results(self) -> list[ScoringResult]:
        return self.weekly_plan_results + self.injury_risk_results

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
            "injury_risk_results": [r.to_dict() for r in self.injury_risk_results],
        }


# ── Eval runner ─────────────────────────────────────────────────────


async def _run_weekly_plan_eval(profile: RunnerProfile, gen_model: str, judge_model: str) -> ScoringResult:
    """Run a single weekly plan eval for a profile."""
    prompt = weekly_plan_prompt(
        goals=profile.goals,
        recent_activities=profile.recent_activities,
        athlete_stats=profile.athlete_stats,
        training_zones=profile.zones if profile.zones else None,
    )
    response = await complete(model=gen_model, prompt=prompt)
    rubric = get_weekly_plan_rubric(profile.id)
    return await score_with_judge(
        response=response,
        rubric=rubric,
        profile_id=profile.id,
        profile_description=profile.description,
        judge_model=judge_model,
        gen_model=gen_model,
    )


async def _run_injury_risk_eval(profile: RunnerProfile, gen_model: str, judge_model: str) -> ScoringResult:
    """Run a single injury risk eval for a profile."""
    prompt = injury_risk_prompt(
        weekly_distances=profile.weekly_distances,
        training_load=profile.acwr,
        recent_activities=profile.recent_activities,
    )
    response = await complete(model=gen_model, prompt=prompt)
    rubric = get_injury_risk_rubric(profile.id)
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

    # Weekly plans — all 16 profiles
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

    # Injury risk — 6 at-risk profiles
    for profile in _RISK_PROFILES:
        try:
            sr = await _run_injury_risk_eval(profile, gen_model, judge_model)
            result.injury_risk_results.append(sr)
            status = "PASS" if sr.passed else "FAIL"
            print(
                f"    [{status}] injury_risk/{profile.id}  (det={sr.deterministic_score:.0%} "
                f"judge={sr.judge_score:.0%} rating={sr.mean_rating:.1f})",
                flush=True,
            )
        except Exception as exc:
            print(f"    [ERR]  injury_risk/{profile.id}: {exc}", flush=True)

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

    # Recommendation
    best = max(results, key=lambda x: x.mean_rating) if results else None
    cheapest_passing = None
    for r in sorted(results, key=lambda x: MODEL_TIERS.get(x.model, {}).get("input_cost_per_m", 999)):
        if r.total_pass_rate >= 0.75:
            cheapest_passing = r
            break

    if best:
        lines.append(f"**Best quality:** {best.label} ({best.mean_rating:.1f}/5)")
    if cheapest_passing and cheapest_passing != best:
        lines.append(
            f"**Best value:** {cheapest_passing.label} "
            f"({cheapest_passing.total_pass_rate:.0%} pass, "
            f"${MODEL_TIERS.get(cheapest_passing.model, {}).get('input_cost_per_m', '?')}/M in)"
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
