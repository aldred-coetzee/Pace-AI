"""Garmin workout step builders and scheduling logic."""

from __future__ import annotations

from ui.config import log

_STEP_INTERVAL = {"stepTypeId": 3, "stepTypeKey": "interval"}
_CONDITION_LAP = {"conditionTypeId": 1, "conditionTypeKey": "lap.button"}
_CONDITION_TIME = {"conditionTypeId": 2, "conditionTypeKey": "time"}
_TARGET_NONE = {"workoutTargetTypeId": 1, "workoutTargetTypeKey": "no.target"}
_DURATION_TYPES = {"easy_run", "run_walk", "tempo", "yoga", "cardio", "walking"}
_STRUCTURED_TYPES = {"strength", "mobility", "yoga"}


def _format_exercises_as_description(exercises: list[dict]) -> str:
    """Format structured exercises into a text description for Garmin Connect.

    The description is visible in the Garmin Connect phone app so the athlete
    can read what to do while a simple single-step workout runs on the watch.
    """
    lines: list[str] = []
    for ex in exercises:
        name = ex.get("name", "Exercise")
        sets = ex.get("sets")
        reps = ex.get("reps")
        duration_s = ex.get("duration_s")
        notes = ex.get("notes")

        if sets and reps:
            line = f"{sets}x{reps} {name}"
        elif duration_s:
            line = f"{name} ({duration_s}s)"
        elif sets:
            line = f"{sets}x {name}"
        else:
            line = name

        if notes:
            line += f" — {notes}"
        lines.append(line)
    return "\n".join(lines)


def _build_simple_steps(description: str, duration_minutes: int | None) -> list[dict]:
    """Build a single lap-button step for non-running workouts.

    The athlete hits start on the watch, reads instructions on their phone
    via the Garmin Connect app description, and hits stop when done.
    """
    step_label = description[:50] if description else "Workout"
    return [
        {
            "type": "ExecutableStepDTO",
            "stepId": None,
            "stepOrder": 1,
            "stepType": _STEP_INTERVAL,
            "endCondition": _CONDITION_LAP,
            "targetType": _TARGET_NONE,
            "description": step_label,
        }
    ]


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

                # Simple single-step workout — hit start, read exercises on phone, hit stop
                if exercises and isinstance(exercises, list):
                    exercise_desc = _format_exercises_as_description(exercises)
                    full_desc = (
                        f"{description}\n\n{exercise_desc}"
                        if description
                        else exercise_desc
                    )
                else:
                    full_desc = description
                steps = _build_simple_steps(full_desc, duration)
                workout_json = custom_workout(
                    name,
                    steps_json=steps,
                    description=full_desc,
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
