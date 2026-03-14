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

STATUS_SYSTEM_PROMPT = """\
You are a running coach reviewing an athlete's current status.
All paces in minutes per mile. Distances in miles.
Produce a concise status report: training load trends, recent run quality, \
recovery indicators, body composition, injury/niggle status, overall readiness.
Be specific with numbers. Keep under 500 words. Markdown format."""

PLAN_SYSTEM_PROMPT = """\
You are a running coach creating a training plan.
All paces in minutes per mile. Saturday is ALWAYS the long run day.
Coaching must cite the research evidence provided.
Every mobility/recovery session MUST include foam rolling.
Output plan as JSON (schema provided). Do NOT include exercises array.
The description field MUST contain full exercise details for strength/mobility sessions.
Include coaching rationale before the JSON."""

CHAT_SYSTEM_PROMPT = """\
You are a running coach in a conversation with your athlete.
All paces in minutes per mile. Distances in miles.
{plan_instruction}\
Keep responses concise and practical."""

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

{mode_instruction}\
Keep responses practical and specific. Use metric for nutrition (grams, ml) but miles for running."""

NUTRITION_MODE_GENERAL = """\
Provide weekly nutrition principles based on the athlete's current training load.
Cover: daily eating patterns, hydration, pre/post-run nutrition, and any supplements worth considering.
If no nutrition preferences are recorded, note this and give generic advice with a suggestion to add dietary preferences."""

NUTRITION_MODE_PLAN = """\
Map nutrition to specific training days in the confirmed plan.
Reference specific days, e.g. "Tuesday tempo — increase carbs at lunch, recovery protein within 30min post-session."
Cover pre-workout, during (if applicable), and post-workout nutrition for each session type.
If no nutrition preferences are recorded, note this and give generic advice with a suggestion to add dietary preferences."""

NUTRITION_MODE_RACE = """\
Create a race-week and race-day nutrition and hydration strategy.
Cover: carb loading timeline (days before), race morning meal, in-race fueling (gels/timing/fluid), post-race recovery nutrition.
Be specific about timing and quantities where general principles allow.
If no nutrition preferences are recorded, note this and give generic advice with a suggestion to add dietary preferences."""

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
    "STATUS_SYSTEM_PROMPT",
    "PLAN_SYSTEM_PROMPT",
    "CHAT_SYSTEM_PROMPT",
    "PLAN_JSON_SCHEMA",
    "NUTRITION_SYSTEM_PROMPT",
    "NUTRITION_MODE_GENERAL",
    "NUTRITION_MODE_PLAN",
    "NUTRITION_MODE_RACE",
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
