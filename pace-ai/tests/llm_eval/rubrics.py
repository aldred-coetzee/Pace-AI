"""Scoring rubrics for coaching evaluation.

Each rubric defines:
- required_elements: phrases/concepts that MUST appear in the response
- forbidden_elements: phrases/concepts that MUST NOT appear
- scoring_criteria: structured checks for the LLM judge

Rubrics are keyed by profile condition + level + prompt type.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Rubric:
    """Evaluation rubric for a coaching response."""

    name: str
    description: str

    # Case-insensitive substring checks
    required_elements: list[str] = field(default_factory=list)
    forbidden_elements: list[str] = field(default_factory=list)

    # Structured criteria for LLM judge (natural language)
    scoring_criteria: list[str] = field(default_factory=list)

    # Expected intensity distribution constraints
    min_easy_pct: float = 70.0  # minimum % of volume at easy effort
    max_hard_pct: float = 25.0  # maximum % of volume at hard effort
    max_run_days: int = 7  # maximum running days per week
    must_include_rest_day: bool = True


# ── Beginner (Healthy) ───────────────────────────────────────────────

BEGINNER_HEALTHY_WEEKLY_PLAN = Rubric(
    name="beginner_healthy_weekly_plan",
    description="Weekly plan for a healthy beginner runner",
    required_elements=[
        "easy",
        "rest",
    ],
    forbidden_elements=[
        "VO2max intervals",
        "lactate threshold test",
        "race pace intervals",
    ],
    scoring_criteria=[
        "Plan prescribes no more than 4 running days per week.",
        "At least 1 full rest day is explicitly included.",
        "The majority (80%+) of running volume is at easy/conversational pace.",
        "Weekly volume increase from recent average is 10% or less.",
        "No interval training or speed work is prescribed.",
        "Paces mentioned are within or near the runner's easy zone.",
        "The long run is no more than 30% of the total weekly volume.",
        "Language is encouraging and avoids unnecessary jargon.",
    ],
    min_easy_pct=80.0,
    max_hard_pct=5.0,
    max_run_days=4,
    must_include_rest_day=True,
)

# ── Beginner (Returning from Injury) ────────────────────────────────

BEGINNER_INJURY_RETURN_WEEKLY_PLAN = Rubric(
    name="beginner_injury_return_weekly_plan",
    description="Weekly plan for a beginner returning from injury",
    required_elements=[
        "gradual",
        "rest",
    ],
    forbidden_elements=[
        "speed work",
        "tempo run",
        "interval",
        "push through",
        "make up for lost time",
    ],
    scoring_criteria=[
        "Plan explicitly acknowledges the injury history and current low ACWR.",
        "Volume is conservative — no more than 10% increase from the most recent week.",
        "Running days are limited to 3-4 per week maximum.",
        "Rest days are placed between every running day.",
        "All running is at easy/conversational pace only.",
        "Walk/run approach is mentioned or considered appropriate.",
        "No intensity work (tempo, intervals, speed) is prescribed.",
        "Coach recommends monitoring for pain, swelling, or discomfort.",
        "Language emphasises patience and long-term health over short-term fitness.",
    ],
    min_easy_pct=100.0,
    max_hard_pct=0.0,
    max_run_days=4,
    must_include_rest_day=True,
)

INJURY_RETURN_INJURY_RISK = Rubric(
    name="injury_return_injury_risk",
    description="Injury risk assessment for a runner returning from injury",
    required_elements=[
        "ACWR",
        "gradual",
    ],
    forbidden_elements=[
        "increase volume quickly",
        "push through pain",
    ],
    scoring_criteria=[
        "Correctly identifies the low ACWR as an undertraining signal.",
        "Warns that ramping up too fast from low chronic load will spike ACWR dangerously.",
        "Recommends a gradual return with no more than 10% weekly increase.",
        "Notes the recent downward trend in volume as a concern.",
        "Recommends rest days between running days.",
        "Mentions monitoring for pain or re-injury symptoms.",
        "Does NOT suggest immediately returning to pre-injury volume.",
    ],
    min_easy_pct=100.0,
    max_hard_pct=0.0,
    max_run_days=4,
    must_include_rest_day=True,
)

# ── Intermediate (Healthy) ──────────────────────────────────────────

INTERMEDIATE_HEALTHY_WEEKLY_PLAN = Rubric(
    name="intermediate_healthy_weekly_plan",
    description="Weekly plan for a healthy intermediate runner",
    required_elements=[
        "easy",
        "long run",
    ],
    forbidden_elements=[],
    scoring_criteria=[
        "Plan includes 2 quality sessions (tempo/threshold and/or intervals).",
        "A structured long run is included, at 25-30% of weekly volume.",
        "80/20 intensity distribution is approximately maintained.",
        "Weekly total is within 10% of recent average.",
        "Key sessions are aligned with the goal race distance.",
        "At least 1 full rest day is included.",
        "Easy days follow hard days (no back-to-back quality sessions).",
        "Paces referenced are consistent with the runner's training zones.",
    ],
    min_easy_pct=75.0,
    max_hard_pct=25.0,
    max_run_days=6,
    must_include_rest_day=True,
)

# ── Intermediate (Overreaching) ─────────────────────────────────────

OVERREACHING_WEEKLY_PLAN = Rubric(
    name="overreaching_weekly_plan",
    description="Weekly plan for an overreaching runner (ACWR > 1.5)",
    required_elements=[
        "ACWR",
        "reduce",
    ],
    forbidden_elements=[
        "maintain current",
        "push through",
        "keep up the volume",
    ],
    scoring_criteria=[
        "The ACWR spike (>1.5) is flagged immediately and prominently.",
        "An immediate deload or volume reduction is recommended.",
        "Recommended volume for next week is 30-50% below the spike week.",
        "All intensity/speed work is dropped for the deload period.",
        "Only easy running is prescribed during the deload.",
        "The response frames the deload as a positive/protective measure, not punishment.",
        "A timeline for gradual return to normal volume is suggested.",
        "At least 2 rest days are recommended in the deload week.",
    ],
    min_easy_pct=100.0,
    max_hard_pct=0.0,
    max_run_days=4,
    must_include_rest_day=True,
)

OVERREACHING_INJURY_RISK = Rubric(
    name="overreaching_injury_risk",
    description="Injury risk assessment for an overreaching runner",
    required_elements=[
        "high",
        "ACWR",
        "reduce",
    ],
    forbidden_elements=[
        "low risk",
        "no concern",
        "keep training",
    ],
    scoring_criteria=[
        "Risk level is explicitly rated as 'High' or 'Elevated'.",
        "The specific ACWR value is cited and explained.",
        "The week-over-week volume spike is identified with specific numbers.",
        "Immediate volume reduction is recommended.",
        "The response cites ACWR > 1.5 as the danger threshold.",
        "Specific km target for next week's reduced volume is provided.",
        "A recovery timeline is suggested (7-14 days of reduced load).",
        "The response avoids panic/catastrophising language while being clear about urgency.",
    ],
    min_easy_pct=100.0,
    max_hard_pct=0.0,
    max_run_days=4,
    must_include_rest_day=True,
)

# ── Advanced (Healthy) ──────────────────────────────────────────────

ADVANCED_HEALTHY_WEEKLY_PLAN = Rubric(
    name="advanced_healthy_weekly_plan",
    description="Weekly plan for a healthy advanced runner",
    required_elements=[
        "easy",
        "long run",
        "threshold",
    ],
    forbidden_elements=[],
    scoring_criteria=[
        "Plan includes 2-3 quality sessions with specific workout details.",
        "Workouts are race-specific for the goal distance.",
        "Long run is structured (not just 'run long') with specific elements.",
        "80/20 intensity distribution is approximately maintained.",
        "Weekly volume is consistent with recent training (within 10%).",
        "Recovery runs and easy days are explicitly prescribed.",
        "Paces are specific and align with the runner's training zones.",
        "Periodisation context is provided (where this week fits in the training block).",
    ],
    min_easy_pct=75.0,
    max_hard_pct=25.0,
    max_run_days=7,
    must_include_rest_day=True,
)

# ── Advanced (Injury Risk) ──────────────────────────────────────────

INJURY_RISK_WEEKLY_PLAN = Rubric(
    name="injury_risk_weekly_plan",
    description="Weekly plan for an advanced runner with dangerous ACWR",
    required_elements=[
        "ACWR",
        "risk",
        "reduce",
    ],
    forbidden_elements=[
        "maintain current volume",
        "keep training as normal",
    ],
    scoring_criteria=[
        "The dangerously high ACWR (>1.5) is flagged as the top priority.",
        "The erratic loading pattern (high CV) is specifically called out.",
        "Immediate and significant volume reduction is prescribed.",
        "Volume target for next week is back to or below the chronic average.",
        "All high-intensity work is suspended during the deload.",
        "Only easy running is prescribed.",
        "The 81.8% week-over-week spike is explicitly identified as dangerous.",
        "Consistency is emphasised as more important than peak volume.",
        "Despite the athlete's high fitness level, the advice is firm about reducing load.",
    ],
    min_easy_pct=100.0,
    max_hard_pct=0.0,
    max_run_days=5,
    must_include_rest_day=True,
)

INJURY_RISK_ASSESSMENT = Rubric(
    name="injury_risk_assessment",
    description="Injury risk assessment for a runner with dangerous ACWR and erratic loading",
    required_elements=[
        "high",
        "ACWR",
    ],
    forbidden_elements=[
        "low risk",
        "no concern",
        "looks fine",
    ],
    scoring_criteria=[
        "Risk is unambiguously rated as 'High'.",
        "Both the ACWR spike AND the erratic loading (CV) are identified as concerns.",
        "Specific problematic weeks are cited (e.g., 'from 55km to 100km').",
        "The 10% rule violation is noted.",
        "Immediate volume reduction to chronic average or below is recommended.",
        "A structured plan for consistent week-to-week loading is suggested.",
        "The importance of consistency over occasional big weeks is emphasised.",
    ],
    min_easy_pct=100.0,
    max_hard_pct=0.0,
    max_run_days=5,
    must_include_rest_day=True,
)

# ── Senior (Beginner) ───────────────────────────────────────────────

SENIOR_BEGINNER_WEEKLY_PLAN = Rubric(
    name="senior_beginner_weekly_plan",
    description="Weekly plan for a senior beginner runner (age 58-62)",
    required_elements=[
        "easy",
        "rest",
        "recovery",
    ],
    forbidden_elements=[
        "speed work",
        "VO2max intervals",
        "high intensity",
        "run every day",
    ],
    scoring_criteria=[
        "Running days are limited to 3 per week maximum.",
        "Rest days are placed between every running day (no consecutive running days).",
        "Strength training is recommended at least 1-2 times per week.",
        "All running is at easy/conversational effort.",
        "Walk/run approach is considered appropriate and mentioned.",
        "Recovery needs appropriate for age are acknowledged.",
        "Volume progression is conservative (10% or less).",
        "The advice does NOT patronise — it's supportive while acknowledging age factors.",
        "Joint health, bone density, or fall prevention is mentioned or considered.",
        "Medical clearance or physician consultation is suggested if not already obtained.",
    ],
    min_easy_pct=100.0,
    max_hard_pct=0.0,
    max_run_days=3,
    must_include_rest_day=True,
)

# ── Teen (Talent) ───────────────────────────────────────────────────

TEEN_TALENT_WEEKLY_PLAN = Rubric(
    name="teen_talent_weekly_plan",
    description="Weekly plan for a talented teen runner (age 16-17)",
    required_elements=[
        "easy",
        "development",
    ],
    forbidden_elements=[
        "lose weight",
        "diet",
        "body fat",
        "body composition",
        "peak performance now",
    ],
    scoring_criteria=[
        "The coaching framework is development-focused, not just performance-focused.",
        "Volume is appropriate for age (40-55 miles/week or ~65-90 km/week maximum).",
        "No more than 2 quality/intensity sessions per week.",
        "The 20% week-over-week volume increase is noted as aggressive for a teen.",
        "Long-term athletic development is referenced or implied.",
        "Adequate sleep and nutrition are mentioned.",
        "At least 1-2 full rest days per week are included.",
        "Cross-training or variety is encouraged.",
        "The plan does NOT chase peak performance at the expense of development.",
        "If the athlete is female, RED-S/energy availability awareness is included.",
    ],
    min_easy_pct=80.0,
    max_hard_pct=15.0,
    max_run_days=6,
    must_include_rest_day=True,
)

TEEN_FEMALE_WEEKLY_PLAN = Rubric(
    name="teen_female_weekly_plan",
    description="Weekly plan for a talented teen female runner — includes RED-S awareness",
    required_elements=[
        "easy",
        "development",
    ],
    forbidden_elements=[
        "lose weight",
        "diet",
        "body fat",
        "body composition",
        "peak performance now",
    ],
    scoring_criteria=[
        "All criteria from teen_talent_weekly_plan apply.",
        "Energy availability or RED-S awareness is mentioned.",
        "Iron status monitoring is mentioned or implied.",
        "The coach creates space for the athlete to discuss how she is feeling.",
        "Menstrual health is acknowledged without being intrusive.",
        "No comments about body weight, shape, or composition.",
    ],
    min_easy_pct=80.0,
    max_hard_pct=15.0,
    max_run_days=6,
    must_include_rest_day=True,
)


# ── Rubric mapping ──────────────────────────────────────────────────


def get_weekly_plan_rubric(profile_id: str) -> Rubric:
    """Get the appropriate weekly plan rubric for a profile."""
    _map: dict[str, Rubric] = {
        "01_beginner_m30_healthy": BEGINNER_HEALTHY_WEEKLY_PLAN,
        "02_beginner_f28_healthy": BEGINNER_HEALTHY_WEEKLY_PLAN,
        "03_beginner_m45_returning_injury": BEGINNER_INJURY_RETURN_WEEKLY_PLAN,
        "04_beginner_f35_returning_injury": BEGINNER_INJURY_RETURN_WEEKLY_PLAN,
        "05_intermediate_m32_healthy": INTERMEDIATE_HEALTHY_WEEKLY_PLAN,
        "06_intermediate_f29_healthy": INTERMEDIATE_HEALTHY_WEEKLY_PLAN,
        "07_intermediate_m40_overreaching": OVERREACHING_WEEKLY_PLAN,
        "08_intermediate_f38_overreaching": OVERREACHING_WEEKLY_PLAN,
        "09_advanced_m25_healthy": ADVANCED_HEALTHY_WEEKLY_PLAN,
        "10_advanced_f27_healthy": ADVANCED_HEALTHY_WEEKLY_PLAN,
        "11_advanced_m22_injury_risk": INJURY_RISK_WEEKLY_PLAN,
        "12_advanced_f24_injury_risk": INJURY_RISK_WEEKLY_PLAN,
        "13_senior_m62_beginner": SENIOR_BEGINNER_WEEKLY_PLAN,
        "14_senior_f58_beginner": SENIOR_BEGINNER_WEEKLY_PLAN,
        "15_teen_m17_talent": TEEN_TALENT_WEEKLY_PLAN,
        "16_teen_f16_talent": TEEN_FEMALE_WEEKLY_PLAN,
    }
    return _map[profile_id]


def get_injury_risk_rubric(profile_id: str) -> Rubric:
    """Get the appropriate injury risk rubric for a profile."""
    _map: dict[str, Rubric] = {
        "03_beginner_m45_returning_injury": INJURY_RETURN_INJURY_RISK,
        "04_beginner_f35_returning_injury": INJURY_RETURN_INJURY_RISK,
        "07_intermediate_m40_overreaching": OVERREACHING_INJURY_RISK,
        "08_intermediate_f38_overreaching": OVERREACHING_INJURY_RISK,
        "11_advanced_m22_injury_risk": INJURY_RISK_ASSESSMENT,
        "12_advanced_f24_injury_risk": INJURY_RISK_ASSESSMENT,
    }
    return _map[profile_id]
