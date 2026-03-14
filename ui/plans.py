"""Plan extraction, formatting, and exercise enrichment."""

from __future__ import annotations

import json
import re
import subprocess

from ui.config import CLAUDE_CMD, PROJECT_ROOT, log


def _extract_weekly_plan(text: str) -> dict | None:
    """Try to extract a weekly plan JSON block from Claude's response.

    Looks for a JSON object with 'week_starting' and 'sessions' keys,
    either bare or inside markdown code fences.
    """
    # Try to find JSON in code fences first (greedy — capture full nested JSON)
    fence_match = re.search(r"```(?:json)?\s*\n(\{.+\})\s*\n```", text, re.DOTALL)
    if fence_match:
        candidate = fence_match.group(1)
        try:
            data = json.loads(candidate)
            if "week_starting" in data and "sessions" in data:
                return data
        except json.JSONDecodeError:
            pass

    # Try to find bare JSON by locating "week_starting" and finding the enclosing {}
    if '"week_starting"' not in text:
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
                        if "week_starting" in data and "sessions" in data:
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
        '- Each exercise: {"name": "...", "sets": N, "reps": N} or '
        '{"name": "...", "duration_s": N}\n'
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
    from datetime import date, timedelta

    today = date.today()
    days_ahead = (7 - today.weekday()) % 7
    if days_ahead == 0:
        days_ahead = 7
    monday = today + timedelta(days=days_ahead)
    sunday = monday + timedelta(days=6)
    return monday.isoformat(), sunday.isoformat()
