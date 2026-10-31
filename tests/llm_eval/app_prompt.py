"""Build the prompt the app really sends to the PLAN agent, for a RunnerProfile.

The profile is seeded into a throwaway SQLite database, the UI is pointed at it,
and the app's own code runs the same steps as the `/status` then `/plan` routes
in `ui/app.py`: gather status data, rule-based assessments, status snapshot,
`_build_plan_context`. No prompt text is written here.

Seeding covers: activities (the profile's recent runs, plus synthetic runs for
the older weeks of `weekly_distances` so the 12-week load query sees all 8),
athlete profile (date of birth from age, gender, experience level, injury
history, notes), goals (as `goal` athlete facts, which is what the PLAN context
reads, and in the goals table) and an `injury` fact for returning-injury
profiles. Dates are shifted so the newest run is yesterday, because the app
only looks at the last 28 days. Not representable (no place in the schema, or
the app does not read them): the profile's pre-computed ACWR, VDOT, zones, race
prediction and athlete_stats; wellness, diary and body-composition rows (the
profiles have none); the Garmin calendar, which is stubbed to empty so no
network is touched.

Research claims come from the real `research/claims.db`.
"""

from __future__ import annotations

import json
import tempfile
from contextlib import ExitStack
from datetime import date, timedelta
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import patch

from pace_ai.database import GoalDB, HistoryDB
from ui import config as ui_config
from ui import context as ui_context
from ui.context import _build_plan_context, _gather_status_data
from ui.plans import _default_date_range
from ui.status import (
    assess_injury,
    assess_readiness,
    assess_recent_runs,
    assess_recovery,
    assess_training_load,
    build_status_snapshot,
)

if TYPE_CHECKING:
    from tests.llm_eval.profiles import RunnerProfile

_LEVELS = {"beginner": "beginner", "intermediate": "intermediate", "advanced": "advanced"}


def _pace_to_speed(pace: str) -> float:
    """'7:30' (min/km) -> metres per second."""
    minutes, seconds = pace.split(":")
    return 1000 / (int(minutes) * 60 + int(seconds))


def _seed(db: HistoryDB, db_path: str, profile: RunnerProfile) -> None:
    today = date.today()
    recent = profile.recent_activities
    last = max(date.fromisoformat(a["start_date"]) for a in recent)
    first = min(date.fromisoformat(a["start_date"]) for a in recent)
    shift = (today - timedelta(days=1)) - last

    activities: list[dict] = []

    def add(n: int, day: date, name: str, km: float, pace: str, hr: float) -> None:
        speed = _pace_to_speed(pace)
        activities.append(
            {
                "strava_id": f"{profile.id}-{n}",
                "date": day.isoformat(),
                "sport_type": "Run",
                "name": name,
                "distance_m": km * 1000,
                "moving_time_s": int(km * 1000 / speed),
                "elapsed_time_s": int(km * 1000 / speed),
                "average_hr": hr,
                # average_speed_ms is deliberately left unset: get_recent_activities then returns
                # pace as "m:ss" strings and ui.status.assess_recent_runs does int() on them.
            }
        )

    for i, a in enumerate(recent):
        add(
            i,
            date.fromisoformat(a["start_date"]) + shift,
            a["name"],
            a["distance_km"],
            a["pace_min_per_km"],
            a["average_heartrate"],
        )

    # Older weeks of weekly_distances: three runs a week at the profile's typical pace.
    typical_pace = recent[0]["pace_min_per_km"]
    typical_hr = recent[0]["average_heartrate"]
    older = profile.weekly_distances[: max(len(profile.weekly_distances) - 4, 0)]
    for w, km in enumerate(older):
        weeks_back = len(older) - w
        monday = first + shift - timedelta(days=7 * weeks_back)
        for r, offset in enumerate((0, 2, 4)):
            add(
                1000 + w * 10 + r,
                monday + timedelta(days=offset),
                "Easy Run",
                round(km / 3, 1),
                typical_pace,
                typical_hr,
            )
    db.upsert_activities(activities)

    dob = today - timedelta(days=int(profile.age * 365.25) + 30)
    injury_history = profile.description if profile.condition == "returning_injury" else None
    db.upsert_athlete_profile(
        {
            "date_of_birth": dob.isoformat(),
            "gender": {"M": "male", "F": "female"}.get(profile.gender, profile.gender),
            "experience_level": _LEVELS.get(profile.level, profile.level),
            "injury_history": json.dumps([injury_history]) if injury_history else None,
            "current_weekly_km": profile.weekly_distances[-1],
            "typical_weekly_km": sum(profile.weekly_distances) / len(profile.weekly_distances),
            "estimated_vdot": profile.vdot or None,
            "notes": profile.description,
        }
    )

    goals = GoalDB(db_path)
    for g in profile.goals:
        race_date = date.fromisoformat(g["race_date"]) + shift if g.get("race_date") else None
        goals.create(
            g["race_type"], g["target_time_seconds"], race_date.isoformat() if race_date else None, g.get("notes")
        )
        fact = f"Goal: {g['race_type']} in {g.get('target_time_formatted', '')}"
        if race_date:
            fact += f" on {race_date.isoformat()}"
        if g.get("notes"):
            fact += f" ({g['notes']})"
        db.add_athlete_fact("goal", fact, source="eval")
    if profile.condition == "returning_injury":
        db.add_athlete_fact("injury", profile.description, source="eval")


def build_app_plan_prompt(profile: RunnerProfile) -> tuple[str, str]:
    """Return (system_prompt, user_prompt) exactly as the app's /plan route builds them."""
    with tempfile.TemporaryDirectory(prefix="pace-ai-eval-") as tmp, ExitStack() as stack:
        db_path = str(Path(tmp) / "pace_ai.db")
        db = HistoryDB(db_path)
        _seed(db, db_path, profile)

        # Modules that captured DB_PATH at import time, plus the Garmin calendar (network).
        stack.enter_context(patch.object(ui_config, "DB_PATH", db_path))
        stack.enter_context(patch.object(ui_context, "DB_PATH", db_path))
        stack.enter_context(patch.object(ui_context, "_get_upcoming_schedule", lambda *a, **k: []))

        # Mirrors /status (and the auto-status branch of /plan) in ui/app.py.
        data = _gather_status_data(db)
        training_status, training_html = assess_training_load(data.get("weekly_distances") or [])
        _runs_status, _runs_html = assess_recent_runs(data.get("activities") or [], data.get("facts") or [])
        recovery_status, recovery_html = assess_recovery(data.get("wellness") or [])
        injury_status, injury_html = assess_injury(data.get("diary_entries") or [], data.get("facts") or [])
        readiness_status, readiness_verdict, _content = assess_readiness(
            training_status, recovery_status, injury_status, training_html, recovery_html, injury_html
        )
        snapshot = build_status_snapshot(
            training_status,
            training_html,
            recovery_status,
            recovery_html,
            injury_status,
            injury_html,
            readiness_status,
            readiness_verdict,
        )

        # Mirrors /plan.
        date_from, date_to = _default_date_range()
        date_range = f"{date_from} to {date_to}"
        system_prompt = _build_plan_context(snapshot, date_range)
        return system_prompt, f"Create a training plan for {date_range}."


def plan_text(reply: str) -> str:
    """Flatten the PLAN agent's JSON reply to plain text for keyword and judge scoring.

    Every string value is kept (report-section content, session names and
    descriptions) with the session fields in reading order; JSON keys, braces
    and fences are dropped. If the reply holds no plan JSON it is returned as is.
    """
    from ui.plans import _extract_weekly_plan

    plan = _extract_weekly_plan(reply)
    if not plan:
        return reply
    lines: list[str] = []
    for key, value in plan.items():
        if key == "sessions":
            continue
        if isinstance(value, dict):
            lines.append(
                f"{key.replace('_', ' ').title()} ({value.get('status', '')}):\n{value.get('content', '')}".replace(
                    " ():", ":"
                )
            )
        elif isinstance(value, str):
            lines.append(f"{key.replace('_', ' ').title()}: {value}")
    for sess in plan.get("sessions", []):
        head = f"{sess.get('date', '')} {sess.get('workout_type', '')} - {sess.get('name', '')}"
        lines.append(f"{head} ({sess.get('duration_minutes', '')} min): {sess.get('description', '')}")
    return "\n\n".join(lines)
