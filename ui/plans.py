"""Plan extraction, formatting, exercise enrichment, and date utilities."""

from __future__ import annotations

import json
import re
import subprocess
from datetime import date, timedelta

from ui.config import CLAUDE_CMD, PROJECT_ROOT, log

# ── Date utilities ──

# Day-of-week abbreviations and full names for matching
_DAY_ABBREVS = {0: "Mon", 1: "Tue", 2: "Wed", 3: "Thu", 4: "Fri", 5: "Sat", 6: "Sun"}
_DAY_FULL = {
    0: "Monday",
    1: "Tuesday",
    2: "Wednesday",
    3: "Thursday",
    4: "Friday",
    5: "Saturday",
    6: "Sunday",
}
# Reverse lookups (case-insensitive)
_NAME_TO_WEEKDAY: dict[str, int] = {}
for _wd, _name in _DAY_FULL.items():
    _NAME_TO_WEEKDAY[_name.lower()] = _wd
    _NAME_TO_WEEKDAY[_name[:3].lower()] = _wd
    _NAME_TO_WEEKDAY[_name[:4].lower()] = _wd  # "Thur", "Tues"

# Pattern to match day-of-week labels before or near a date-like string
# e.g. "Mon 27th Apr", "Tuesday 28 April", "Wed 29/04"
_DAY_LABEL_RE = re.compile(
    r"\b(Mon(?:day)?|Tue(?:s(?:day)?)?|Wed(?:nesday)?|Thu(?:r(?:s(?:day)?)?)?|"
    r"Fri(?:day)?|Sat(?:urday)?|Sun(?:day)?)\b",
    re.IGNORECASE,
)


def _date_calendar(start_iso: str, end_iso: str) -> str:
    """Build a date-to-day-name reference for a date range.

    Returns lines like:
      Mon 2026-04-27
      Tue 2026-04-28
      ...

    This is injected into the plan prompt so the LLM knows exactly which
    day of the week each date falls on.
    """
    try:
        start = date.fromisoformat(start_iso)
        end = date.fromisoformat(end_iso)
    except (ValueError, TypeError):
        return ""

    lines: list[str] = []
    current = start
    while current <= end:
        day_name = _DAY_ABBREVS[current.weekday()]
        lines.append(f"  {day_name} {current.isoformat()}")
        current += timedelta(days=1)
    return "\n".join(lines)


def _validate_plan_dates(plan: dict) -> dict:
    """Validate and fix day-of-week labels in plan sessions.

    If a session name or description contains a day-of-week that doesn't
    match the session's date field, replace it with the correct day name.
    Also validates that dates fall within a reasonable range.

    Mutates and returns the plan dict.
    """
    for session in plan.get("sessions", []):
        date_str = session.get("date", "")
        try:
            d = date.fromisoformat(date_str)
        except (ValueError, TypeError):
            continue

        # Fix day-of-week mismatches in name and description
        for field in ("name", "description"):
            value = session.get(field, "")
            if not value:
                continue

            fixed = _fix_day_label(value, d.weekday())
            if fixed != value:
                log.warning(
                    "Fixed day-of-week in session %s %s: %r -> %r",
                    date_str,
                    field,
                    value,
                    fixed,
                )
                session[field] = fixed

    return plan


def _fix_day_label(text: str, correct_weekday: int) -> str:
    """Replace any incorrect day-of-week names in text with the correct one.

    Preserves the original format (abbreviated vs full name).
    """

    def _replace_if_wrong(match: re.Match) -> str:
        found = match.group(0)
        found_wd = _NAME_TO_WEEKDAY.get(found.lower())
        if found_wd is None or found_wd == correct_weekday:
            return found  # correct or unrecognised — leave it
        # Preserve format: if original was full name, use full; otherwise abbrev
        if len(found) > 3 and found[3:4].isalpha():
            return _DAY_FULL[correct_weekday]
        return _DAY_ABBREVS[correct_weekday]

    return _DAY_LABEL_RE.sub(_replace_if_wrong, text)


def _extract_weekly_plan(text: str) -> dict | None:
    """Try to extract a weekly plan JSON block from Claude's response.

    Looks for a JSON object with 'sessions' key (and optionally report
    sections like 'rationale', 'research_basis', 'weekly_summary'),
    either bare or inside markdown code fences.

    Returns the full parsed JSON dict (including report sections if present).
    The caller can extract 'sessions' and 'week_starting' as needed.
    """
    # Try to find JSON in code fences first (greedy — capture full nested JSON)
    fence_match = re.search(r"```(?:json)?\s*\n(\{.+\})\s*\n```", text, re.DOTALL)
    if fence_match:
        candidate = fence_match.group(1)
        try:
            data = json.loads(candidate)
            if "sessions" in data:
                # Derive week_starting if missing but sessions exist
                if "week_starting" not in data and data["sessions"]:
                    data["week_starting"] = data["sessions"][0].get("date", "")
                return data
        except json.JSONDecodeError:
            pass

    # Try to find bare JSON by locating "sessions" and finding the enclosing {}
    if '"sessions"' not in text:
        return None
    # Find all top-level { that could start a plan JSON
    for match in re.finditer(r"\{", text):
        start = match.start()
        # Try progressively longer substrings to find valid JSON
        depth = 0
        for i in range(start, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    candidate = text[start : i + 1]
                    try:
                        data = json.loads(candidate)
                        if "sessions" in data:
                            if "week_starting" not in data and data["sessions"]:
                                data["week_starting"] = data["sessions"][0].get(
                                    "date", ""
                                )
                            return data
                    except json.JSONDecodeError:
                        pass
                    break

    return None


def _strip_plan_json(text: str) -> str:
    """Remove bare JSON plan blocks (containing week_starting) from text."""
    if '"week_starting"' not in text:
        return text
    result = text
    for match in re.finditer(r"\{", text):
        start = match.start()
        depth = 0
        for i in range(start, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    candidate = text[start : i + 1]
                    if '"week_starting"' in candidate and '"sessions"' in candidate:
                        try:
                            json.loads(candidate)
                            result = result.replace(candidate, "")
                        except json.JSONDecodeError:
                            pass
                    break
    return result


def _format_plan_table(plan: dict) -> str:
    """Build a markdown table of a weekly plan for display in chat."""
    table = f"\n\n**Proposed plan — week of {plan.get('week_starting', '?')}:**\n\n"
    table += (
        "| Date | Session | Type | Duration |\n|------|---------|------|----------|\n"
    )
    for s in plan.get("sessions", []):
        table += (
            f"| {s.get('date', '')} | {s.get('name', '')} "
            f"| {s.get('workout_type', '')} | {s.get('duration_minutes', '')}min |\n"
        )
    table += "\nSuggest changes, or click **Schedule** when ready."
    return table


def _enrich_plan_with_exercises(plan: dict) -> dict | None:
    """Send a focused claude -p call to generate exercises for strength/mobility sessions.

    Returns the enriched plan with exercises arrays, or None on failure.
    """
    prompt = (
        "Convert this training plan to JSON with exercises arrays for every "
        "strength, mobility, and yoga session.\n\n"
        "Input plan:\n" + json.dumps(plan, indent=2) + "\n\n"
        "Rules:\n"
        "- Add an exercises array to every strength/mobility/yoga session\n"
        "- Rep-based exercises MUST use sets/reps format: "
        '{"name": "...", "sets": N, "reps": N} — this creates a lap-button step '
        "the athlete advances manually when done\n"
        "- Timed holds/stretches MUST use duration_s format: "
        '{"name": "...", "duration_s": N}\n'
        "- NEVER put duration_s on rep-based exercises — the athlete controls pacing\n"
        "- Eccentric exercises (heel drops, Nordic curls) are slow (~5s per rep). "
        "Always specify per-leg reps explicitly in the name if bilateral "
        '(e.g. "Heel drops (each leg)" with reps: 15)\n'
        "- For bilateral timed holds (e.g. single-leg balance), duration_s must be "
        "the TOTAL time for both legs (e.g. 30s/leg = duration_s: 60)\n"
        "- Include foam rolling exercises with duration_s (e.g. 60 or 120)\n"
        "- Include Achilles-specific exercises (heel drops, calf raises) if relevant\n"
        "- Keep all other fields exactly as they are\n"
        "- Output ONLY the JSON, no commentary\n"
    )
    try:
        result = subprocess.run(
            CLAUDE_CMD,
            input=prompt,
            capture_output=True,
            text=True,
            timeout=120,
            cwd=str(PROJECT_ROOT),
        )
        enriched = _extract_weekly_plan(result.stdout.strip())
        if enriched and enriched.get("sessions"):
            # Verify exercises were actually added
            has_exercises = any(
                s.get("exercises")
                for s in enriched.get("sessions", [])
                if s.get("workout_type") in ("strength", "mobility", "yoga")
            )
            if has_exercises:
                log.info("Exercise enrichment succeeded")
                return enriched
            log.warning("Exercise enrichment returned no exercises")
        else:
            log.warning("Exercise enrichment failed to parse plan")
    except Exception:
        log.exception("Exercise enrichment call failed")
    return None


def _default_date_range() -> tuple[str, str]:
    """Return (next_monday, next_sunday) as ISO strings."""
    today = date.today()
    days_ahead = (7 - today.weekday()) % 7
    if days_ahead == 0:
        days_ahead = 7
    monday = today + timedelta(days=days_ahead)
    sunday = monday + timedelta(days=6)
    return monday.isoformat(), sunday.isoformat()
