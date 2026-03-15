"""Garmin workout step builders and scheduling logic."""

from __future__ import annotations

import re

from ui.config import log

_STEP_INTERVAL = {"stepTypeId": 3, "stepTypeKey": "interval"}
_CONDITION_LAP = {"conditionTypeId": 1, "conditionTypeKey": "lap.button"}
_CONDITION_TIME = {"conditionTypeId": 2, "conditionTypeKey": "time"}
_TARGET_NONE = {"workoutTargetTypeId": 1, "workoutTargetTypeKey": "no.target"}
_DURATION_TYPES = {"easy_run", "run_walk", "tempo", "yoga", "cardio", "walking"}
_STRUCTURED_TYPES = {"strength", "mobility", "yoga"}


def _exercises_to_steps(exercises: list[dict]) -> list[dict]:
    """Convert structured exercises array into Garmin workout steps.

    Each exercise dict has 'name' and either 'sets'+'reps' or 'duration_s'.
    """

    steps: list[dict] = []
    for i, ex in enumerate(exercises, 1):
        name = ex.get("name", "Exercise")
        sets = ex.get("sets")
        reps = ex.get("reps")
        duration_s = ex.get("duration_s")

        if sets and reps:
            label = f"{sets}x{reps} {name}"
        elif duration_s:
            label = f"{name} ({duration_s}s)"
        else:
            label = name

        if len(label) > 50:
            label = label[:47] + "..."

        # Use timed step if duration_s given, lap-button otherwise
        if duration_s:
            steps.append(
                {
                    "type": "ExecutableStepDTO",
                    "stepId": None,
                    "stepOrder": i,
                    "stepType": _STEP_INTERVAL,
                    "endCondition": _CONDITION_TIME,
                    "endConditionValue": float(duration_s),
                    "targetType": _TARGET_NONE,
                    "description": label,
                }
            )
        else:
            steps.append(
                {
                    "type": "ExecutableStepDTO",
                    "stepId": None,
                    "stepOrder": i,
                    "stepType": _STEP_INTERVAL,
                    "endCondition": _CONDITION_LAP,
                    "targetType": _TARGET_NONE,
                    "description": label,
                }
            )

    return steps


def _description_to_steps(description: str, duration_minutes: int | None) -> list[dict]:
    """Parse a workout description into Garmin custom workout steps.

    Extracts exercises in various formats:
    - "3x15 heel drops" or "heel drops 3x15"
    - "calves 60s/side" or "foam roll calves 60 sec"
    Creates a lap-button step per exercise. Falls back to a single timed step
    if no exercises are found.

    Returns raw Garmin ExecutableStepDTO dicts.
    """
    # Each item is (label, duration_s or None)
    items: list[tuple[str, int | None]] = []

    # Pattern 1: "3x15 exercise name" (sets before name)
    for m in re.finditer(
        r"(\d+)\s*x\s*(\d+)\s+([a-zA-Z][\w\s\-()]+?)(?:\.|,|$)", description
    ):
        sets, reps, name = m.group(1), m.group(2), m.group(3).strip().rstrip(")")
        items.append((f"{sets}x{reps} {name}", None))

    # Pattern 2: "exercise name (qualifier) 3x15" (sets after name)
    for m in re.finditer(
        r"([a-zA-Z][\w\s\-]+(?:\([^)]*\))?)\s+(\d+)\s*x\s*(\d+)(?:\s|,|\.|$)",
        description,
    ):
        name, sets, reps = m.group(1).strip(), m.group(2), m.group(3)
        label = f"{sets}x{reps} {name}"
        if not any(label == it[0] for it in items):
            items.append((label, None))

    # Pattern 3: timed items — "calves 60s/side", "foam roll quads 60 sec each"
    for m in re.finditer(
        r"([a-zA-Z][\w\s\-]+?)\s+(\d+)\s*s(?:ec)?(?:\s+each|/side)?(?:\.|,|$)",
        description,
    ):
        name, secs = m.group(1).strip(), int(m.group(2))
        # Split compound items like "Foam roll calves and quads" into separate steps
        if " and " in name:
            prefix = ""
            parts = name.split(" and ")
            words = parts[0].split()
            if len(words) > 1 and not words[-1][0].isupper():
                prefix = " ".join(words[:-1]) + " "
                parts[0] = words[-1]
            for part in parts:
                part_label = f"{prefix}{part.strip()} ({secs}s)"
                if not any(
                    part.strip().lower() in existing[0].lower() for existing in items
                ):
                    items.append((part_label, secs))
        else:
            label = f"{name} ({secs}s)"
            if not any(name.lower() in existing[0].lower() for existing in items):
                items.append((label, secs))

    if not items:
        step_seconds = (duration_minutes or 30) * 60
        return [
            {
                "type": "ExecutableStepDTO",
                "stepId": None,
                "stepOrder": 1,
                "stepType": _STEP_INTERVAL,
                "endCondition": _CONDITION_TIME,
                "endConditionValue": float(step_seconds),
                "targetType": _TARGET_NONE,
                "description": description[:50] if description else "Workout",
            }
        ]

    steps: list[dict] = []
    for i, (label, dur_s) in enumerate(items, 1):
        if len(label) > 50:
            label = label[:47] + "..."
        step: dict = {
            "type": "ExecutableStepDTO",
            "stepId": None,
            "stepOrder": i,
            "stepType": _STEP_INTERVAL,
            "targetType": _TARGET_NONE,
            "description": label,
        }
        if dur_s:
            step["endCondition"] = _CONDITION_TIME
            step["endConditionValue"] = float(dur_s)
        else:
            step["endCondition"] = _CONDITION_LAP
        steps.append(step)

    return steps


def schedule_plan_to_garmin(plan: dict) -> tuple[list[dict], int, int, int]:
    """Create and schedule workouts in Garmin Connect for a confirmed plan.

    Returns (results_list, ok_count, fail_count, skip_count).
    """
    from garmin_mcp.client import GarminClient
    from garmin_mcp.config import Settings as GarminSettings
    from garmin_mcp.server import _build_workout
    from garmin_mcp.workout_builder import WORKOUT_TYPES

    garmin_settings = GarminSettings.from_env()
    garmin_client = GarminClient(garmin_settings)

    results = []
    ok_count = 0
    fail_count = 0
    skip_count = 0

    for s in plan.get("sessions", []):
        workout_type = s.get("workout_type", "")
        name = s.get("name", "Workout")
        date = s.get("date", "")

        if workout_type == "rest":
            results.append(
                {
                    "date": date,
                    "name": name,
                    "status": "skipped (rest day)",
                    "css": "skip",
                }
            )
            skip_count += 1
            continue

        if workout_type not in WORKOUT_TYPES:
            results.append(
                {
                    "date": date,
                    "name": name,
                    "status": f"skipped (unknown type: {workout_type})",
                    "css": "skip",
                }
            )
            skip_count += 1
            continue

        # Build params from the session data — only pass what each builder accepts
        params = {}
        duration = s.get("duration_minutes")
        if duration and workout_type in _DURATION_TYPES:
            params["duration_minutes"] = duration

        try:
            description = s.get("description", "")
            exercises = s.get("exercises")
            if workout_type in _STRUCTURED_TYPES:
                from garmin_mcp.workout_builder import (
                    custom_workout,
                    resolve_sport_type,
                )

                if exercises and isinstance(exercises, list):
                    # Structured exercises from JSON — reliable
                    steps = _exercises_to_steps(exercises)
                else:
                    # Fallback: parse from description text
                    steps = _description_to_steps(description, duration)
                workout_json = custom_workout(
                    name,
                    steps_json=steps,
                    description=description,
                    sport_type=resolve_sport_type(workout_type),
                )
            else:
                workout_json = _build_workout(workout_type, name, params)
                # Inject the plan description so it shows in Garmin Connect
                if description:
                    workout_json["description"] = description
            result = garmin_client.create_workout(workout_json)
            workout_id = result.get("workoutId") if isinstance(result, dict) else None
            if not workout_id:
                results.append(
                    {
                        "date": date,
                        "name": name,
                        "status": "created but no ID returned",
                        "css": "fail",
                    }
                )
                fail_count += 1
                continue
            garmin_client.schedule_workout(workout_id, date)
            results.append(
                {
                    "date": date,
                    "name": name,
                    "status": f"scheduled (ID {workout_id})",
                    "css": "ok",
                }
            )
            ok_count += 1
        except Exception as e:
            log.exception("Failed to create/schedule workout: %s", name)
            results.append(
                {"date": date, "name": name, "status": f"error: {e}", "css": "fail"}
            )
            fail_count += 1

    return results, ok_count, fail_count, skip_count
