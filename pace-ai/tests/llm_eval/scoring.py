"""Scoring logic for evaluating coaching responses against rubrics.

Two modes:
1. Deterministic: substring checks for required/forbidden elements (free, fast)
2. LLM judge: sends response + rubric to a judge model for nuanced scoring (costs $, slower)
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tests.llm_eval.rubrics import Rubric


@dataclass
class ScoringResult:
    """Result of evaluating a response against a rubric."""

    profile_id: str
    rubric_name: str
    passed: bool

    # Deterministic checks
    required_present: dict[str, bool] = field(default_factory=dict)
    forbidden_absent: dict[str, bool] = field(default_factory=dict)

    # LLM judge results (only populated in live mode)
    criteria_scores: dict[str, bool] = field(default_factory=dict)
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
    """Build the prompt for the LLM judge."""
    criteria_text = "\n".join(f"  {i + 1}. {c}" for i, c in enumerate(rubric.scoring_criteria))
    return f"""You are evaluating a running coaching response for correctness and safety.

## Runner Profile
{profile_description}

## Rubric: {rubric.name}
{rubric.description}

## Scoring Criteria
Evaluate the coaching response against EACH of these criteria. For each criterion,
respond with PASS or FAIL and a brief (1-sentence) justification.

{criteria_text}

## Coaching Response to Evaluate
{response}

## Output Format
For each criterion, output exactly one line in this format:
CRITERION <number>: PASS|FAIL — <brief justification>

After all criteria, output a final line:
OVERALL: <number of passes>/{len(rubric.scoring_criteria)} criteria passed
"""


def _parse_judge_response(judge_response: str, num_criteria: int) -> tuple[dict[str, bool], float]:
    """Parse the LLM judge response into structured scores."""
    scores: dict[str, bool] = {}
    for i in range(num_criteria):
        pattern = rf"CRITERION\s+{i + 1}\s*:\s*(PASS|FAIL)"
        match = re.search(pattern, judge_response, re.IGNORECASE)
        if match:
            scores[f"criterion_{i + 1}"] = match.group(1).upper() == "PASS"
        else:
            scores[f"criterion_{i + 1}"] = False

    score = sum(scores.values()) / len(scores) if scores else 0.0

    return scores, score


async def score_with_judge(
    response: str,
    rubric: Rubric,
    profile_id: str,
    profile_description: str,
) -> ScoringResult:
    """Score a response using an LLM judge (Haiku 4.5).

    Requires ANTHROPIC_API_KEY environment variable.

    Returns a ScoringResult with both deterministic and judge scores.
    """
    # Always run deterministic checks first
    result = score_deterministic(response, rubric, profile_id)

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        msg = "ANTHROPIC_API_KEY required for LLM judge scoring."
        raise RuntimeError(msg)

    import anthropic

    client = anthropic.AsyncAnthropic(api_key=api_key)

    judge_prompt = _build_judge_prompt(response, rubric, profile_description)

    judge_response = await client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=2048,
        messages=[{"role": "user", "content": judge_prompt}],
    )

    judge_text = judge_response.content[0].text
    criteria_scores, judge_score = _parse_judge_response(judge_text, len(rubric.scoring_criteria))

    result.criteria_scores = criteria_scores
    result.judge_score = judge_score
    result.judge_reasoning = judge_text
    result.passed = result.deterministic_score == 1.0 and judge_score >= 0.75

    return result


def format_scoring_report(results: list[ScoringResult]) -> str:
    """Format a human-readable report from scoring results."""
    lines = ["=" * 70, "COACHING EVALUATION REPORT", "=" * 70, ""]

    passed = sum(1 for r in results if r.passed)
    total = len(results)
    lines.append(f"Overall: {passed}/{total} profiles passed\n")

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
            lines.append(f"  Judge: {r.judge_score:.0%}")
            failed_criteria = [k for k, v in r.criteria_scores.items() if not v]
            if failed_criteria:
                lines.append(f"  Failed criteria: {', '.join(failed_criteria)}")

        lines.append("")

    return "\n".join(lines)
