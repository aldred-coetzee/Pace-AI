"""Shared constants, paths, and imports for the Pace-AI UI package."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

# Add pace-ai src to import path before importing pace_ai modules
PROJECT_ROOT = Path(__file__).resolve().parent.parent
_pace_src = str(PROJECT_ROOT / "pace-ai" / "src")
if _pace_src not in sys.path:
    sys.path.insert(0, _pace_src)

# Add garmin-mcp src to import path for direct workout scheduling
_garmin_src = str(PROJECT_ROOT / "garmin-mcp" / "src")
if _garmin_src not in sys.path:
    sys.path.insert(0, _garmin_src)

# ruff: noqa: E402
from pace_ai.database import HistoryDB
from pace_ai.tools.memory import (
    append_coaching_log,
    get_athlete_facts,
    get_coaching_context,
    get_recent_coaching_log,
    update_coaching_context,
)
from pace_ai.tools.history import get_recent_activities, get_weekly_distances
from pace_ai.tools.profile import get_athlete_profile
from pace_ai.tools.sync import sync_all as _sync_all

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")
log = logging.getLogger("pace-ui")

DB_PATH = str(PROJECT_ROOT / "pace_ai.db")
_SESSION_DB = str(PROJECT_ROOT / "ui_sessions.db")

CLAUDE_CMD = [
    "claude",
    "-p",
    "--dangerously-skip-permissions",
]

# ── Structured output schema ──
# Each agent defines sections as (key, title, has_status, content_hint).
# content_hint tells Claude what to write in the content field.
# The generic renderer handles layout; Claude handles content.

STATUS_SECTIONS = [
    (
        "training_load",
        "Training Load",
        True,
        "Weekly volume, trend table, consistency assessment",
    ),
    (
        "recent_runs",
        "Recent Runs",
        True,
        "Pace range, HR vs zones, pace discipline, notable runs",
    ),
    (
        "recovery",
        "Recovery",
        True,
        "RHR, HRV, stress, sleep, BP — table or bullet format",
    ),
    (
        "injury_status",
        "Injury Status",
        True,
        "Current niggles, rehab compliance, pattern changes",
    ),
    (
        "overall_readiness",
        "Overall Readiness",
        True,
        "Green lights, amber flags, key priorities this week",
    ),
]
# upcoming_schedule and body_composition are rendered directly — no LLM needed

# ── Parallel STATUS sub-group section definitions ──
# Each group gets its own focused prompt with only the data it needs.

STATUS_TRAINING_SECTIONS = [
    (
        "training_load",
        "Training Load",
        True,
        "Weekly volume, trend table, consistency assessment",
    ),
    (
        "recent_runs",
        "Recent Runs",
        True,
        "Pace range, HR vs zones, pace discipline, notable runs",
    ),
]

STATUS_RECOVERY_SECTIONS = [
    (
        "recovery",
        "Recovery",
        True,
        "RHR, HRV, stress, sleep, BP — table or bullet format",
    ),
]

STATUS_INJURY_SECTIONS = [
    (
        "injury_status",
        "Injury Status",
        True,
        "Current niggles, rehab compliance, pattern changes",
    ),
]

STATUS_READINESS_SECTIONS = [
    (
        "overall_readiness",
        "Overall Readiness",
        True,
        "Green lights, amber flags, key priorities this week",
    ),
]

NUTRITION_GENERAL_SECTIONS = [
    (
        "daily_eating",
        "Daily Eating Patterns",
        False,
        "Meal structure and timing around training days vs rest days",
    ),
    (
        "pre_post_run",
        "Pre & Post Run Nutrition",
        True,
        "What and when to eat before and after runs — timing, food types",
    ),
    (
        "hydration",
        "Hydration",
        True,
        "Daily fluid targets, electrolytes, signs of under-hydration",
    ),
    (
        "supplements",
        "Supplements",
        True,
        "What is worth considering and what to skip — cite evidence",
    ),
    (
        "key_recommendations",
        "Key Recommendations",
        False,
        "Top 3-5 practical takeaways for this athlete",
    ),
]

NUTRITION_PLAN_SECTIONS = [
    (
        "easy_days",
        "Easy / Recovery Days",
        False,
        "Nutrition approach for easy run days",
    ),
    (
        "long_run",
        "Long Run Day",
        True,
        "Pre, during (if applicable), and post-run nutrition",
    ),
    (
        "strength_mobility",
        "Strength & Mobility Days",
        False,
        "Nutrition around cross-training sessions",
    ),
    (
        "rest_days",
        "Rest Days",
        False,
        "Eating on rest days — what changes, what stays the same",
    ),
    ("hydration", "Hydration", True, "Daily fluid guidance across the training week"),
    ("weekly_summary", "Weekly Summary", False, "Day-by-day quick reference table"),
]

NUTRITION_RACE_SECTIONS = [
    (
        "race_week",
        "Race Week Loading",
        True,
        "Carb loading timeline, what to eat, what to avoid",
    ),
    ("race_eve", "Night Before", False, "Evening meal guidance — timing, composition"),
    (
        "race_morning",
        "Race Morning",
        True,
        "Pre-race meal — timing, specific food suggestions",
    ),
    (
        "during_race",
        "During Race",
        True,
        "In-race fueling — gels, fluid, electrolytes, timing",
    ),
    (
        "post_race",
        "Post Race Recovery",
        False,
        "Immediate and same-day recovery nutrition",
    ),
    (
        "key_warnings",
        "Key Warnings",
        False,
        "Nothing new on race day — things to avoid",
    ),
]


def _build_structured_prompt(
    sections: list[tuple], *, verdict_section: str | None = None
) -> str:
    """Generate the JSON schema instruction block for any agent.

    Args:
        sections: List of (key, title, has_status, content_hint) tuples.
        verdict_section: If set, this section key gets an extra "verdict" field.
    """
    lines = [
        "Output ONLY a JSON object inside ```json fences with this exact structure:",
        "",
        "```json",
        "{",
    ]
    entries = []
    for key, _title, has_status, hint in sections:
        fields = []
        if has_status:
            fields.append('    "status": "ok|caution|concern"')
        if key == verdict_section:
            fields.append('    "verdict": "Short headline phrase"')
        fields.append(f'    "content": "Markdown: {hint}"')
        entries.append(f'  "{key}": {{\n' + ",\n".join(fields) + "\n  }")
    lines.append((",\n").join(entries))
    lines.extend(["}", "```", ""])
    lines.append("Rules:")
    lines.append('- status values: "ok" (green), "caution" (amber), "concern" (red)')
    lines.append(
        "- content fields are markdown strings — use tables, bullets, bold as needed"
    )
    if verdict_section:
        lines.append(
            f"- {verdict_section}.verdict is a short phrase shown as the headline"
        )
    lines.append("- Be concise in each section — 2-4 sentences or a short table")
    lines.append("- Do not use emoji")
    return "\n".join(lines)


STATUS_SYSTEM_PROMPT = """\
You are a running coach reviewing an athlete's current status.
Today is {today_weekday}, {today_date}.
All paces in minutes per mile. Distances in miles.
Be specific with numbers.

""" + _build_structured_prompt(STATUS_SECTIONS, verdict_section="overall_readiness")

# ── Parallel STATUS sub-group prompts ──

_STATUS_PREAMBLE = """\
You are a running coach reviewing an athlete's current status.
Today is {today_weekday}, {today_date}.
All paces in minutes per mile. Distances in miles.
Be specific with numbers.

"""

STATUS_TRAINING_PROMPT = _STATUS_PREAMBLE + _build_structured_prompt(
    STATUS_TRAINING_SECTIONS
)
STATUS_RECOVERY_PROMPT = _STATUS_PREAMBLE + _build_structured_prompt(
    STATUS_RECOVERY_SECTIONS
)
STATUS_INJURY_PROMPT = _STATUS_PREAMBLE + _build_structured_prompt(
    STATUS_INJURY_SECTIONS
)
STATUS_READINESS_PROMPT = _STATUS_PREAMBLE + _build_structured_prompt(
    STATUS_READINESS_SECTIONS, verdict_section="overall_readiness"
)

PLAN_REPORT_SECTIONS = [
    (
        "rationale",
        "Coaching Rationale",
        False,
        "Key coaching decisions, progressive overload logic, injury considerations",
    ),
    (
        "research_basis",
        "Research Basis",
        False,
        "Key research claims this plan is built on — cite specific evidence",
    ),
    (
        "weekly_summary",
        "Weekly Summary",
        False,
        "Total volume, intensity distribution, key sessions",
    ),
]


def _build_plan_prompt() -> str:
    """Generate the combined PLAN JSON schema with report sections + sessions."""
    lines = [
        "Output ONLY a JSON object inside ```json fences with this exact structure:",
        "",
        "```json",
        "{",
    ]
    # Report sections
    entries = []
    for key, _title, has_status, hint in PLAN_REPORT_SECTIONS:
        fields = []
        if has_status:
            fields.append('    "status": "ok|caution|concern"')
        fields.append(f'    "content": "Markdown: {hint}"')
        entries.append(f'  "{key}": {{\n' + ",\n".join(fields) + "\n  }")
    # Sessions array
    entries.append(
        '  "week_starting": "YYYY-MM-DD",\n'
        '  "sessions": [\n'
        "    {\n"
        '      "date": "YYYY-MM-DD",\n'
        '      "workout_type": "easy_run|run_walk|tempo|intervals|strides|strength|mobility|yoga|cardio|hiit|walking|rest",\n'
        '      "name": "Short name shown on watch",\n'
        '      "duration_minutes": 30,\n'
        '      "description": "Full exercise details for strength/mobility — sets, reps, duration"\n'
        "    }\n"
        "  ]"
    )
    lines.append((",\n").join(entries))
    lines.extend(["}", "```", ""])
    lines.append("Rules:")
    lines.append(
        "- content fields are markdown strings — use tables, bullets, bold as needed"
    )
    lines.append("- Be concise in each section — 2-4 sentences or a short table")
    lines.append("- Do not use emoji")
    lines.append(
        "- Do NOT include an exercises array — exercises are added automatically at scheduling time"
    )
    lines.append("- week_starting is the date of the FIRST session in the plan")
    lines.append(
        '- Include an entry for every day in the requested range (rest days use workout_type "rest")'
    )
    lines.append(
        "- Saturday is ALWAYS the long run day. Never schedule strength or rest on Saturday"
    )
    return "\n".join(lines)


PLAN_SYSTEM_PROMPT = """\
You are a running coach creating a training plan.
All paces in minutes per mile. Saturday is ALWAYS the long run day.
Coaching must cite the research evidence provided.
Every mobility/recovery session MUST include foam rolling.
Do not use emoji.
The description field MUST contain full exercise details for strength/mobility sessions.

""" + _build_plan_prompt()

CHAT_SYSTEM_PROMPT = """\
You are a running coach in a conversation with your athlete.
All paces in minutes per mile. Distances in miles.
{plan_instruction}\
Keep responses concise and practical. Do not use emoji."""

PLAN_JSON_SCHEMA = """\
## Plan JSON Schema

Output the plan as a JSON block inside ```json code fences:

```json
{
  "week_starting": "YYYY-MM-DD",
  "sessions": [
    {
      "date": "YYYY-MM-DD",
      "workout_type": "easy_run|run_walk|tempo|intervals|strides|strength|mobility|yoga|cardio|hiit|walking|rest",
      "name": "Short name shown on watch",
      "duration_minutes": 30,
      "description": "Full exercise details for strength/mobility — sets, reps, duration"
    }
  ]
}
```

Do NOT include an exercises array — exercises are added automatically at scheduling time.
week_starting is the date of the FIRST session in the plan.
Include an entry for every day in the requested range (rest days use workout_type "rest").
Saturday is ALWAYS the long run day. Never schedule strength or rest on Saturday."""

NUTRITION_SYSTEM_PROMPT = """\
You are a sports nutritionist advising a distance runner.
All paces in minutes per mile. Distances in miles.
Base all advice on the research evidence provided — cite claims when relevant.
Tailor advice to the athlete's training load, body composition, and goals.

## Hard Boundaries
- NO calorie counting or specific macro gram prescriptions — that is dietitian territory
- NO medical nutrition advice (RED-S, eating disorders, clinical deficiencies) — flag and recommend professional consultation
- Focus on timing, food types, hydration principles, and practical suggestions
- Respect stated dietary preferences absolutely — never suggest foods the athlete has said they don't eat
- Frame advice as general sports nutrition principles, not individualised medical nutrition therapy

{mode_instruction}
Keep responses practical and specific. Use metric for nutrition (grams, ml) but miles for running."""

NUTRITION_MODE_GENERAL = _build_structured_prompt(NUTRITION_GENERAL_SECTIONS)

NUTRITION_MODE_PLAN = """\
Map nutrition to specific training days in the confirmed plan.
Reference specific days, e.g. "Tuesday tempo — increase carbs at lunch, recovery protein within 30min."
If no nutrition preferences are recorded, note this and give generic advice.

""" + _build_structured_prompt(NUTRITION_PLAN_SECTIONS)

NUTRITION_MODE_RACE = """\
Create a race-week and race-day nutrition and hydration strategy.
Be specific about timing and quantities where general principles allow.
If no nutrition preferences are recorded, note this and give generic advice.

""" + _build_structured_prompt(NUTRITION_RACE_SECTIONS)

# Nutrition research categories to query
NUTRITION_CLAIM_CATEGORIES = [
    "nutrition_general",
    "carbohydrate_fueling",
    "protein_runners",
    "hydration",
    "supplements",
    "iron_bone_health",
]

# Re-export for convenience
__all__ = [
    "PROJECT_ROOT",
    "DB_PATH",
    "_SESSION_DB",
    "CLAUDE_CMD",
    "STATUS_SECTIONS",
    "STATUS_TRAINING_SECTIONS",
    "STATUS_RECOVERY_SECTIONS",
    "STATUS_INJURY_SECTIONS",
    "STATUS_READINESS_SECTIONS",
    "STATUS_SYSTEM_PROMPT",
    "STATUS_TRAINING_PROMPT",
    "STATUS_RECOVERY_PROMPT",
    "STATUS_INJURY_PROMPT",
    "STATUS_READINESS_PROMPT",
    "PLAN_REPORT_SECTIONS",
    "PLAN_SYSTEM_PROMPT",
    "CHAT_SYSTEM_PROMPT",
    "PLAN_JSON_SCHEMA",
    "NUTRITION_SYSTEM_PROMPT",
    "NUTRITION_MODE_GENERAL",
    "NUTRITION_MODE_PLAN",
    "NUTRITION_MODE_RACE",
    "NUTRITION_GENERAL_SECTIONS",
    "NUTRITION_PLAN_SECTIONS",
    "NUTRITION_RACE_SECTIONS",
    "NUTRITION_CLAIM_CATEGORIES",
    "HistoryDB",
    "append_coaching_log",
    "get_athlete_facts",
    "get_coaching_context",
    "get_recent_coaching_log",
    "update_coaching_context",
    "get_recent_activities",
    "get_weekly_distances",
    "get_athlete_profile",
    "_sync_all",
    "log",
]
