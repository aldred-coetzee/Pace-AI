"""Scoring logic for evaluating coaching responses against rubrics.

Three scoring layers:
1. Deterministic: substring checks for required/forbidden elements (free, fast)
2. LLM judge: sends response + rubric to a judge model for nuanced scoring (costs $, slower)
3. Numeric: 1-5 scale per criterion alongside PASS/FAIL for fine-grained comparison
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from tests.llm_eval.rubrics import Rubric


@dataclass
class CriterionScore:
    """Individual criterion result with both binary and numeric scores."""

    name: str
    passed: bool
    rating: int  # 1-5 scale
    justification: str = ""


@dataclass
class ScoringResult:
    """Result of evaluating a response against a rubric."""

    profile_id: str
    rubric_name: str
    passed: bool

    # Model metadata (populated in live mode)
    gen_model: str = ""
    judge_model: str = ""

    # Deterministic checks
    required_present: dict[str, bool] = field(default_factory=dict)
    forbidden_absent: dict[str, bool] = field(default_factory=dict)

    # LLM judge results (only populated in live mode)
    criteria_scores: dict[str, bool] = field(default_factory=dict)
    criteria_details: list[CriterionScore] = field(default_factory=list)
    judge_reasoning: str = ""

    # Overall
    deterministic_score: float = 0.0
    judge_score: float = 0.0

    @property
    def total_score(self) -> float:
        """Combined score: deterministic if no judge, else average of both."""
        if self.judge_score > 0:
            return (self.deterministic_score + self.judge_score) / 2
        return self.deterministic_score

    @property
    def mean_rating(self) -> float:
        """Mean numeric rating across all criteria (1-5 scale). 0 if no ratings."""
        if not self.criteria_details:
            return 0.0
        return sum(c.rating for c in self.criteria_details) / len(self.criteria_details)

    def to_dict(self) -> dict[str, Any]:
        """Serialise to a JSON-friendly dict."""
        d = asdict(self)
        d["total_score"] = self.total_score
        d["mean_rating"] = self.mean_rating
        return d


def score_deterministic(response: str, rubric: Rubric, profile_id: str) -> ScoringResult:
    """Score a response using deterministic substring checks.

    Checks:
    1. All required_elements appear (case-insensitive)
    2. No forbidden_elements appear (case-insensitive)

    Returns a ScoringResult with deterministic_score between 0.0 and 1.0.
    """
    response_lower = response.lower()

    required_present = {}
    for elem in rubric.required_elements:
        required_present[elem] = elem.lower() in response_lower

    forbidden_absent = {}
    for elem in rubric.forbidden_elements:
        forbidden_absent[elem] = elem.lower() not in response_lower

    # Calculate score
    total_checks = len(required_present) + len(forbidden_absent)
    if total_checks == 0:
        score = 1.0
    else:
        passed_checks = sum(required_present.values()) + sum(forbidden_absent.values())
        score = passed_checks / total_checks

    # Pass if score is 1.0 (all checks passed)
    passed = score == 1.0

    return ScoringResult(
        profile_id=profile_id,
        rubric_name=rubric.name,
        passed=passed,
        required_present=required_present,
        forbidden_absent=forbidden_absent,
        deterministic_score=score,
    )


def _build_judge_prompt(response: str, rubric: Rubric, profile_description: str) -> str:
    """Build the prompt for the LLM judge with 1-5 numeric scoring."""
    criteria_text = "\n".join(f"  {i + 1}. {c}" for i, c in enumerate(rubric.scoring_criteria))
    return f"""You are evaluating a running coaching response for correctness and safety.

## Runner Profile
{profile_description}

## Rubric: {rubric.name}
{rubric.description}

## Scoring Criteria
Evaluate the coaching response against EACH of these criteria.

For each criterion, provide:
1. A PASS or FAIL verdict
2. A numeric rating from 1 to 5:
   1 = Dangerous/completely wrong
   2 = Poor — major issues
   3 = Adequate — meets minimum bar
   4 = Good — solid coaching
   5 = Excellent — expert-level coaching
3. A brief (1-sentence) justification

{criteria_text}

## Coaching Response to Evaluate
{response}

## Output Format
For each criterion, output exactly one line in this format:
CRITERION <number>: PASS|FAIL — RATING:<1-5> — <brief justification>

After all criteria, output a final line:
OVERALL: <number of passes>/{len(rubric.scoring_criteria)} criteria passed — MEAN_RATING:<mean>
"""


def _parse_judge_response(judge_response: str, num_criteria: int) -> tuple[list[CriterionScore], float]:
    """Parse the LLM judge response into structured scores with ratings."""
    details: list[CriterionScore] = []
    for i in range(num_criteria):
        pattern = rf"CRITERION\s+{i + 1}\s*:\s*(PASS|FAIL)\s*[—\-]\s*RATING\s*:\s*(\d)\s*[—\-]\s*(.*)"
        match = re.search(pattern, judge_response, re.IGNORECASE)
        if match:
            details.append(
                CriterionScore(
                    name=f"criterion_{i + 1}",
                    passed=match.group(1).upper() == "PASS",
                    rating=max(1, min(5, int(match.group(2)))),
                    justification=match.group(3).strip(),
                )
            )
        else:
            # Fallback 1: try numbered list format (e.g., "1. ... PASS — RATING:4 — ...")
            alt_pattern = rf"(?:^|\n)\s*{i + 1}[\.\)]\s+.*?(PASS|FAIL)\s*[—\-]\s*RATING\s*:\s*(\d)\s*[—\-]\s*(.*)"
            alt_match = re.search(alt_pattern, judge_response, re.IGNORECASE)
            if alt_match:
                details.append(
                    CriterionScore(
                        name=f"criterion_{i + 1}",
                        passed=alt_match.group(1).upper() == "PASS",
                        rating=max(1, min(5, int(alt_match.group(2)))),
                        justification=alt_match.group(3).strip(),
                    )
                )
            else:
                # Fallback 2: try old format without rating
                old_pattern = rf"CRITERION\s+{i + 1}\s*:\s*(PASS|FAIL)"
                old_match = re.search(old_pattern, judge_response, re.IGNORECASE)
                if old_match:
                    passed = old_match.group(1).upper() == "PASS"
                    details.append(
                        CriterionScore(
                            name=f"criterion_{i + 1}",
                            passed=passed,
                            rating=4 if passed else 2,
                            justification="(no justification provided)",
                        )
                    )
                else:
                    details.append(
                        CriterionScore(
                            name=f"criterion_{i + 1}",
                            passed=False,
                            rating=1,
                            justification="(criterion not found in judge output)",
                        )
                    )

    score = sum(1 for d in details if d.passed) / len(details) if details else 0.0
    return details, score


async def score_with_judge(
    response: str,
    rubric: Rubric,
    profile_id: str,
    profile_description: str,
    *,
    judge_model: str = "claude-haiku-4-5-20251001",
    gen_model: str = "",
) -> ScoringResult:
    """Score a response using an LLM judge.

    Requires OPENROUTER_API_KEY or ANTHROPIC_API_KEY environment variable.

    Returns a ScoringResult with both deterministic and judge scores,
    including per-criterion 1-5 ratings.
    """
    # Always run deterministic checks first
    result = score_deterministic(response, rubric, profile_id)
    result.gen_model = gen_model
    result.judge_model = judge_model

    from tests.llm_eval.llm_client import complete

    judge_prompt = _build_judge_prompt(response, rubric, profile_description)

    judge_text = await complete(
        model=judge_model,
        prompt=judge_prompt,
        max_tokens=2048,
    )
    criteria_details, judge_score = _parse_judge_response(judge_text, len(rubric.scoring_criteria))

    result.criteria_details = criteria_details
    result.criteria_scores = {d.name: d.passed for d in criteria_details}
    result.judge_score = judge_score
    result.judge_reasoning = judge_text
    result.passed = result.deterministic_score == 1.0 and judge_score >= 0.75

    return result


# ── Reporting ───────────────────────────────────────────────────────


def format_scoring_report(results: list[ScoringResult]) -> str:
    """Format a human-readable report from scoring results."""
    lines = ["=" * 70, "COACHING EVALUATION REPORT", "=" * 70, ""]

    passed = sum(1 for r in results if r.passed)
    total = len(results)
    lines.append(f"Overall: {passed}/{total} profiles passed\n")

    if results and results[0].gen_model:
        lines.append(f"Gen model:   {results[0].gen_model}")
        lines.append(f"Judge model: {results[0].judge_model}")
        lines.append("")

    for r in results:
        status = "PASS" if r.passed else "FAIL"
        lines.append(f"[{status}] {r.profile_id} — {r.rubric_name}")
        lines.append(f"  Deterministic: {r.deterministic_score:.0%}")

        if r.required_present:
            missing = [k for k, v in r.required_present.items() if not v]
            if missing:
                lines.append(f"  Missing required: {', '.join(missing)}")

        if r.forbidden_absent:
            present = [k for k, v in r.forbidden_absent.items() if not v]
            if present:
                lines.append(f"  Forbidden found: {', '.join(present)}")

        if r.judge_score > 0:
            lines.append(f"  Judge: {r.judge_score:.0%}  |  Mean rating: {r.mean_rating:.1f}/5")
            for d in r.criteria_details:
                flag = "PASS" if d.passed else "FAIL"
                lines.append(f"    [{flag}] {d.name}: {d.rating}/5 — {d.justification}")

        lines.append("")

    return "\n".join(lines)


def format_scorecard_json(results: list[ScoringResult]) -> str:
    """Serialise results list to JSON."""
    return json.dumps([r.to_dict() for r in results], indent=2, default=str)


def format_scorecard_table(results: list[ScoringResult]) -> str:
    """Render a compact markdown comparison table."""
    lines = [
        "| Profile | Rubric | Det | Judge | Rating | Result |",
        "|---------|--------|-----|-------|--------|--------|",
    ]
    for r in results:
        status = "PASS" if r.passed else "FAIL"
        det = f"{r.deterministic_score:.0%}"
        judge = f"{r.judge_score:.0%}" if r.judge_score > 0 else "—"
        rating = f"{r.mean_rating:.1f}" if r.mean_rating > 0 else "—"
        lines.append(f"| {r.profile_id} | {r.rubric_name} | {det} | {judge} | {rating} | {status} |")

    passed = sum(1 for r in results if r.passed)
    total = len(results)
    lines.append(f"\n**{passed}/{total} passed**")

    if results and results[0].gen_model:
        lines.append(f"\nGen: `{results[0].gen_model}` | Judge: `{results[0].judge_model}`")

    return "\n".join(lines)
