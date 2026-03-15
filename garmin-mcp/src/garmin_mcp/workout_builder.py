"""Pure functions that build Garmin workout JSON.

No state, no API calls — trivially testable.
Builds the JSON structure expected by Garmin Connect's workout-service API.

Garmin workout JSON structure:
- sportType: {sportTypeId: 1, sportTypeKey: "running"}
- workoutSegments: [{segmentOrder: 1, sportType: ..., workoutSteps: [...]}]
- Each step is either ExecutableStepDTO (single step) or RepeatGroupDTO (repeats)
- Steps have endCondition (time/distance/lap.button), targetType (hr.zone/no.target)
- HR zones use Garmin's 1-5 system (zoneNumber field)
"""

from __future__ import annotations

from typing import Any

# ── Constants ──────────────────────────────────────────────────────────

# Canonical Garmin Connect sport type IDs
SPORT_TYPE_CUSTOM = {"sportTypeId": 0, "sportTypeKey": "custom"}
SPORT_TYPE_RUNNING = {"sportTypeId": 1, "sportTypeKey": "running"}
SPORT_TYPE_STRENGTH = {"sportTypeId": 5, "sportTypeKey": "strength_training"}
SPORT_TYPE_CARDIO = {"sportTypeId": 6, "sportTypeKey": "cardio"}
SPORT_TYPE_YOGA = {"sportTypeId": 7, "sportTypeKey": "yoga"}
SPORT_TYPE_PILATES = {"sportTypeId": 8, "sportTypeKey": "pilates"}
SPORT_TYPE_HIIT = {"sportTypeId": 9, "sportTypeKey": "hiit"}
SPORT_TYPE_MOBILITY = {"sportTypeId": 11, "sportTypeKey": "mobility"}
SPORT_TYPE_WALKING = {"sportTypeId": 12, "sportTypeKey": "walking"}

# ── Device-aware sport type mapping ───────────────────────────────────
# Maps Pace-AI session types to the Garmin sport type dict to use.
# Not all devices support all sport types. The Forerunner 245 does NOT
# support mobility (11), hiit (9), or cardio (6).
# Single source of truth — used by workout_builder, server, and UI scheduling.

SPORT_TYPE_MAP: dict[str, dict[str, Any]] = {
    "running": SPORT_TYPE_RUNNING,
    "easy_run": SPORT_TYPE_RUNNING,
    "run_walk": SPORT_TYPE_RUNNING,
    "tempo": SPORT_TYPE_RUNNING,
    "intervals": SPORT_TYPE_RUNNING,
    "strides": SPORT_TYPE_RUNNING,
    "strength": SPORT_TYPE_STRENGTH,
    "yoga": SPORT_TYPE_YOGA,
    "mobility": SPORT_TYPE_YOGA,      # FR245: mobility unsupported, use yoga
    "hiit": SPORT_TYPE_CUSTOM,        # FR245: hiit unsupported, use custom
    "cardio": SPORT_TYPE_CUSTOM,      # FR245: cardio unsupported, use custom
    "walking": SPORT_TYPE_WALKING,
    "custom": SPORT_TYPE_CUSTOM,
    "other": SPORT_TYPE_CUSTOM,
}


def resolve_sport_type(workout_type: str) -> dict[str, Any]:
    """Resolve a Pace-AI workout type to the correct Garmin sport type.

    Uses the device-compatible mapping table. Falls back to custom (0)
    for unknown types.
    """
    return SPORT_TYPE_MAP.get(workout_type, SPORT_TYPE_CUSTOM).copy()

# Step types
STEP_TYPE_WARMUP = {"stepTypeId": 1, "stepTypeKey": "warmup"}
STEP_TYPE_COOLDOWN = {"stepTypeId": 2, "stepTypeKey": "cooldown"}
STEP_TYPE_INTERVAL = {"stepTypeId": 3, "stepTypeKey": "interval"}
STEP_TYPE_RECOVERY = {"stepTypeId": 4, "stepTypeKey": "recovery"}
STEP_TYPE_REST = {"stepTypeId": 5, "stepTypeKey": "rest"}
STEP_TYPE_REPEAT = {"stepTypeId": 6, "stepTypeKey": "repeat"}

# End conditions
CONDITION_TIME = {"conditionTypeId": 2, "conditionTypeKey": "time"}
CONDITION_DISTANCE = {"conditionTypeId": 3, "conditionTypeKey": "distance"}
CONDITION_LAP_BUTTON = {"conditionTypeId": 1, "conditionTypeKey": "lap.button"}
CONDITION_ITERATIONS = {"conditionTypeId": 7, "conditionTypeKey": "iterations"}

# Target types
TARGET_NO_TARGET = {"workoutTargetTypeId": 1, "workoutTargetTypeKey": "no.target"}
TARGET_HR_ZONE = {"workoutTargetTypeId": 4, "workoutTargetTypeKey": "heart.rate.zone"}


# ── Step Builders ──────────────────────────────────────────────────────


def _time_step(
    step_order: int,
    step_type: dict[str, Any],
    duration_seconds: float,
    *,
    hr_zone: int | None = None,
    description: str | None = None,
) -> dict[str, Any]:
    """Build a time-based executable step."""
    step: dict[str, Any] = {
        "type": "ExecutableStepDTO",
        "stepId": None,
        "stepOrder": step_order,
        "stepType": step_type,
        "endCondition": CONDITION_TIME,
        "endConditionValue": duration_seconds,
        "preferredEndConditionUnit": {"unitId": 27, "unitKey": "second"},
    }
    if hr_zone is not None:
        step["targetType"] = TARGET_HR_ZONE
        step["zoneNumber"] = hr_zone
    else:
        step["targetType"] = TARGET_NO_TARGET
    if description:
        step["description"] = description
    return step


def _distance_step(
    step_order: int,
    step_type: dict[str, Any],
    distance_meters: float,
    *,
    hr_zone: int | None = None,
    description: str | None = None,
) -> dict[str, Any]:
    """Build a distance-based executable step."""
    step: dict[str, Any] = {
        "type": "ExecutableStepDTO",
        "stepId": None,
        "stepOrder": step_order,
        "stepType": step_type,
        "endCondition": CONDITION_DISTANCE,
        "endConditionValue": distance_meters,
        "preferredEndConditionUnit": {"unitId": 1, "unitKey": "meter"},
    }
    if hr_zone is not None:
        step["targetType"] = TARGET_HR_ZONE
        step["zoneNumber"] = hr_zone
    else:
        step["targetType"] = TARGET_NO_TARGET
    if description:
        step["description"] = description
    return step


def _lap_button_step(
    step_order: int,
    step_type: dict[str, Any],
    *,
    hr_zone: int | None = None,
    description: str | None = None,
) -> dict[str, Any]:
    """Build a lap-button (open-ended) step."""
    step: dict[str, Any] = {
        "type": "ExecutableStepDTO",
        "stepId": None,
        "stepOrder": step_order,
        "stepType": step_type,
        "endCondition": CONDITION_LAP_BUTTON,
    }
    if hr_zone is not None:
        step["targetType"] = TARGET_HR_ZONE
        step["zoneNumber"] = hr_zone
    else:
        step["targetType"] = TARGET_NO_TARGET
    if description:
        step["description"] = description
    return step


def _repeat_group(
    step_order: int,
    iterations: int,
    steps: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build a repeat group wrapping inner steps."""
    return {
        "type": "RepeatGroupDTO",
        "stepId": None,
        "stepOrder": step_order,
        "stepType": STEP_TYPE_REPEAT,
        "numberOfIterations": iterations,
        "workoutSteps": steps,
    }


# ── Workout Wrapper ───────────────────────────────────────────────────


def _wrap_workout(
    name: str,
    steps: list[dict[str, Any]],
    *,
    sport_type: dict[str, Any] | None = None,
    description: str | None = None,
) -> dict[str, Any]:
    """Wrap steps into a complete Garmin workout JSON payload."""
    st = sport_type or SPORT_TYPE_RUNNING
    workout: dict[str, Any] = {
        "workoutId": None,
        "ownerId": None,
        "workoutName": name,
        "sportType": st,
        "workoutSegments": [
            {
                "segmentOrder": 1,
                "sportType": st,
                "workoutSteps": steps,
            }
        ],
    }
    if description:
        workout["description"] = description
    return workout


# ── Convenience Builders ──────────────────────────────────────────────


def easy_run(
    name: str,
    duration_minutes: float,
    hr_zone: int = 1,
    *,
    warmup_minutes: float = 0,
    cooldown_minutes: float = 0,
) -> dict[str, Any]:
    """Build an easy run workout with optional warmup/cooldown.

    Args:
        name: Workout name.
        duration_minutes: Main run duration in minutes.
        hr_zone: Garmin HR zone (1-5) for the main run. Default 1 (easy).
        warmup_minutes: Warmup duration. 0 = no warmup step.
        cooldown_minutes: Cooldown duration. 0 = no cooldown step.
    """
    steps: list[dict[str, Any]] = []
    order = 1

    if warmup_minutes > 0:
        steps.append(_time_step(order, STEP_TYPE_WARMUP, warmup_minutes * 60, description="Warmup"))
        order += 1

    steps.append(_time_step(order, STEP_TYPE_INTERVAL, duration_minutes * 60, hr_zone=hr_zone, description="Easy run"))
    order += 1

    if cooldown_minutes > 0:
        steps.append(_time_step(order, STEP_TYPE_COOLDOWN, cooldown_minutes * 60, description="Cooldown"))

    return _wrap_workout(name, steps, description=f"Easy run — {duration_minutes:.0f} min in Zone {hr_zone}")


def run_walk(
    name: str,
    intervals: int,
    run_minutes: float,
    walk_minutes: float,
    hr_zone: int = 1,
    *,
    warmup_minutes: float = 0,
    cooldown_minutes: float = 0,
) -> dict[str, Any]:
    """Build a run/walk interval workout.

    Args:
        name: Workout name.
        intervals: Number of run/walk cycles.
        run_minutes: Duration of each run interval.
        walk_minutes: Duration of each walk interval.
        hr_zone: Garmin HR zone for run intervals. Default 1.
        warmup_minutes: Warmup duration. 0 = no warmup step.
        cooldown_minutes: Cooldown duration. 0 = no cooldown step.
    """
    steps: list[dict[str, Any]] = []
    order = 1

    if warmup_minutes > 0:
        steps.append(_time_step(order, STEP_TYPE_WARMUP, warmup_minutes * 60, description="Warmup"))
        order += 1

    # Build the run/walk repeat group
    inner_steps = [
        _time_step(1, STEP_TYPE_INTERVAL, run_minutes * 60, hr_zone=hr_zone, description="Run"),
        _time_step(2, STEP_TYPE_RECOVERY, walk_minutes * 60, description="Walk"),
    ]
    steps.append(_repeat_group(order, intervals, inner_steps))
    order += 1

    if cooldown_minutes > 0:
        steps.append(_time_step(order, STEP_TYPE_COOLDOWN, cooldown_minutes * 60, description="Cooldown"))

    total_time = intervals * (run_minutes + walk_minutes) + warmup_minutes + cooldown_minutes
    return _wrap_workout(
        name,
        steps,
        description=(
            f"Run/Walk — {intervals}x ({run_minutes:.0f}min run / {walk_minutes:.0f}min walk)"
            f", ~{total_time:.0f} min total"
        ),
    )


def tempo_run(
    name: str,
    warmup_minutes: float,
    tempo_minutes: float,
    cooldown_minutes: float,
    tempo_hr_zone: int = 3,
) -> dict[str, Any]:
    """Build a tempo run workout.

    Args:
        name: Workout name.
        warmup_minutes: Warmup duration.
        tempo_minutes: Tempo portion duration.
        cooldown_minutes: Cooldown duration.
        tempo_hr_zone: Garmin HR zone for tempo portion. Default 3 (threshold).
    """
    steps = [
        _time_step(1, STEP_TYPE_WARMUP, warmup_minutes * 60, description="Warmup"),
        _time_step(2, STEP_TYPE_INTERVAL, tempo_minutes * 60, hr_zone=tempo_hr_zone, description="Tempo"),
        _time_step(3, STEP_TYPE_COOLDOWN, cooldown_minutes * 60, description="Cooldown"),
    ]
    total = warmup_minutes + tempo_minutes + cooldown_minutes
    return _wrap_workout(
        name,
        steps,
        description=f"Tempo — {tempo_minutes:.0f} min in Zone {tempo_hr_zone}, {total:.0f} min total",
    )


def interval_repeats(
    name: str,
    warmup_minutes: float,
    repeats: int,
    distance_meters: float,
    recovery_minutes: float,
    cooldown_minutes: float,
    hr_zone: int = 4,
) -> dict[str, Any]:
    """Build an interval workout with distance-based repeats.

    Args:
        name: Workout name.
        warmup_minutes: Warmup duration.
        repeats: Number of interval repeats.
        distance_meters: Distance of each repeat in meters.
        recovery_minutes: Recovery jog duration between repeats.
        cooldown_minutes: Cooldown duration.
        hr_zone: Garmin HR zone for hard intervals. Default 4.
    """
    inner_steps = [
        _distance_step(1, STEP_TYPE_INTERVAL, distance_meters, hr_zone=hr_zone, description="Hard"),
        _time_step(2, STEP_TYPE_RECOVERY, recovery_minutes * 60, description="Recovery jog"),
    ]
    steps = [
        _time_step(1, STEP_TYPE_WARMUP, warmup_minutes * 60, description="Warmup"),
        _repeat_group(2, repeats, inner_steps),
        _time_step(3, STEP_TYPE_COOLDOWN, cooldown_minutes * 60, description="Cooldown"),
    ]
    return _wrap_workout(
        name,
        steps,
        description=f"Intervals — {repeats}x {distance_meters:.0f}m in Zone {hr_zone}",
    )


def strides(
    name: str,
    easy_minutes: float,
    stride_count: int,
    stride_seconds: float = 20,
    recovery_seconds: float = 60,
    hr_zone: int = 1,
    *,
    warmup_minutes: float = 0,
    cooldown_minutes: float = 0,
) -> dict[str, Any]:
    """Build an easy run with strides workout.

    Args:
        name: Workout name.
        easy_minutes: Duration of the easy run portion.
        stride_count: Number of strides to do.
        stride_seconds: Duration of each stride. Default 20s.
        recovery_seconds: Recovery between strides. Default 60s.
        hr_zone: Garmin HR zone for easy portion. Default 1.
        warmup_minutes: Warmup duration. 0 = no warmup step.
        cooldown_minutes: Cooldown duration. 0 = no cooldown step.
    """
    steps: list[dict[str, Any]] = []
    order = 1

    if warmup_minutes > 0:
        steps.append(_time_step(order, STEP_TYPE_WARMUP, warmup_minutes * 60, description="Warmup"))
        order += 1

    # Easy run portion
    steps.append(_time_step(order, STEP_TYPE_INTERVAL, easy_minutes * 60, hr_zone=hr_zone, description="Easy run"))
    order += 1

    # Strides as a repeat group
    inner_steps = [
        _time_step(1, STEP_TYPE_INTERVAL, stride_seconds, description="Stride"),
        _time_step(2, STEP_TYPE_RECOVERY, recovery_seconds, description="Recovery"),
    ]
    steps.append(_repeat_group(order, stride_count, inner_steps))
    order += 1

    if cooldown_minutes > 0:
        steps.append(_time_step(order, STEP_TYPE_COOLDOWN, cooldown_minutes * 60, description="Cooldown"))

    return _wrap_workout(
        name,
        steps,
        description=f"Easy + {stride_count} strides ({stride_seconds:.0f}s each)",
    )


def custom_workout(
    name: str,
    steps_json: list[dict[str, Any]],
    *,
    description: str | None = None,
    sport_type: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a workout from raw step JSON — escape hatch for arbitrary workouts.

    Args:
        name: Workout name.
        steps_json: List of raw Garmin step dicts (ExecutableStepDTO or RepeatGroupDTO).
        description: Optional description.
        sport_type: Optional sport type dict. Defaults to running if not specified.
    """
    return _wrap_workout(name, steps_json, sport_type=sport_type, description=description)


# ── Non-Running Builders ─────────────────────────────────────────────


def _format_exercise_desc(exercise: dict[str, Any]) -> str:
    """Build a step description string from an exercise dict."""
    name = exercise["name"]
    sets = exercise.get("sets", 1)
    reps = exercise.get("reps")
    duration_s = exercise.get("duration_s")
    notes = exercise.get("notes")

    if reps:
        desc = f"{name} — {sets}x{reps}"
    elif duration_s:
        desc = f"{name} — {sets}x{duration_s}s"
    else:
        desc = name

    if notes:
        desc += f" ({notes})"
    return desc


def build_strength_workout(name: str, exercises: list[dict[str, Any]]) -> dict[str, Any]:
    """Build a strength training workout with lap-button steps.

    Each exercise is expanded into per-set steps with rest steps between exercises.

    Args:
        name: Workout name.
        exercises: List of exercise dicts with keys: name (str), sets (int),
            reps (int|None), duration_s (int|None), rest_s (int), notes (str|None).
    """
    steps: list[dict[str, Any]] = []
    order = 1

    # Warmup
    steps.append(_lap_button_step(order, STEP_TYPE_WARMUP, description="Warmup — press lap when ready"))
    order += 1

    for i, ex in enumerate(exercises):
        desc = _format_exercise_desc(ex)
        sets = ex.get("sets", 1)
        rest_s = ex.get("rest_s", 60)

        for s in range(sets):
            set_desc = f"{desc} (set {s + 1}/{sets})"
            if ex.get("duration_s"):
                steps.append(_time_step(order, STEP_TYPE_INTERVAL, ex["duration_s"], description=set_desc))
            else:
                steps.append(_lap_button_step(order, STEP_TYPE_INTERVAL, description=set_desc))
            order += 1

            # Rest between sets (but not after last set of last exercise)
            if s < sets - 1 or i < len(exercises) - 1:
                steps.append(_time_step(order, STEP_TYPE_REST, rest_s, description="Rest"))
                order += 1

    # Cooldown
    steps.append(_lap_button_step(order, STEP_TYPE_COOLDOWN, description="Cooldown"))

    exercise_names = [ex["name"] for ex in exercises]
    return _wrap_workout(
        name,
        steps,
        sport_type=SPORT_TYPE_STRENGTH,
        description=f"Strength — {', '.join(exercise_names)}",
    )


def build_mobility_workout(name: str, exercises: list[dict[str, Any]]) -> dict[str, Any]:
    """Build a mobility/stretching workout with timed holds.

    Args:
        name: Workout name.
        exercises: List of exercise dicts with keys: name (str), sets (int),
            duration_s (int), rest_s (int), notes (str|None).
    """
    steps: list[dict[str, Any]] = []
    order = 1

    steps.append(_lap_button_step(order, STEP_TYPE_WARMUP, description="Warmup — press lap when ready"))
    order += 1

    for i, ex in enumerate(exercises):
        desc = _format_exercise_desc(ex)
        sets = ex.get("sets", 1)
        duration_s = ex.get("duration_s", 30)
        rest_s = ex.get("rest_s", 15)

        for s in range(sets):
            set_desc = f"{desc} (set {s + 1}/{sets})"
            steps.append(_time_step(order, STEP_TYPE_INTERVAL, duration_s, description=set_desc))
            order += 1

            if s < sets - 1 or i < len(exercises) - 1:
                steps.append(_time_step(order, STEP_TYPE_REST, rest_s, description="Rest"))
                order += 1

    steps.append(_lap_button_step(order, STEP_TYPE_COOLDOWN, description="Cooldown"))

    return _wrap_workout(
        name,
        steps,
        sport_type=resolve_sport_type("mobility"),
        description=f"Mobility — {len(exercises)} exercises",
    )


def build_yoga_workout(name: str, duration_minutes: int, style: str | None = None) -> dict[str, Any]:
    """Build a yoga workout — single timed step.

    Args:
        name: Workout name.
        duration_minutes: Total session duration in minutes.
        style: Optional style label (e.g. "Yin", "Vinyasa", "Restorative").
    """
    desc = f"{style} yoga" if style else "Yoga"
    steps = [
        _time_step(1, STEP_TYPE_INTERVAL, duration_minutes * 60, description=f"{desc} — {duration_minutes} min"),
    ]
    return _wrap_workout(
        name,
        steps,
        sport_type=SPORT_TYPE_YOGA,
        description=f"{desc} — {duration_minutes} min",
    )


def build_cardio_workout(name: str, duration_minutes: int, intensity: str = "moderate") -> dict[str, Any]:
    """Build a cardio workout — duration-based with HR zone target.

    Args:
        name: Workout name.
        duration_minutes: Session duration in minutes.
        intensity: One of "easy" (zone 1), "moderate" (zone 2), "hard" (zone 3).
    """
    zone_map = {"easy": 1, "moderate": 2, "hard": 3}
    hr_zone = zone_map.get(intensity)
    if hr_zone is None:
        msg = f"Invalid intensity '{intensity}'. Must be one of: easy, moderate, hard"
        raise ValueError(msg)

    steps = [
        _time_step(1, STEP_TYPE_WARMUP, 300, description="Warmup"),
        _time_step(2, STEP_TYPE_INTERVAL, (duration_minutes - 10) * 60, hr_zone=hr_zone, description="Main effort"),
        _time_step(3, STEP_TYPE_COOLDOWN, 300, description="Cooldown"),
    ]
    return _wrap_workout(
        name,
        steps,
        sport_type=resolve_sport_type("cardio"),
        description=f"Cardio — {duration_minutes} min, {intensity} intensity (Zone {hr_zone})",
    )


def build_hiit_workout(
    name: str,
    rounds: int,
    work_s: int,
    rest_s: int,
    exercises: list[str],
) -> dict[str, Any]:
    """Build a HIIT workout with repeating rounds.

    Args:
        name: Workout name.
        rounds: Number of rounds.
        work_s: Work interval duration in seconds.
        rest_s: Rest interval duration in seconds.
        exercises: List of exercise names (cycled through per interval).
    """
    steps: list[dict[str, Any]] = []

    # Warmup
    steps.append(_time_step(1, STEP_TYPE_WARMUP, 300, description="Warmup"))

    # Build inner steps — one work+rest pair per exercise
    inner_steps: list[dict[str, Any]] = []
    inner_order = 1
    for ex_name in exercises:
        inner_steps.append(_time_step(inner_order, STEP_TYPE_INTERVAL, work_s, description=ex_name))
        inner_order += 1
        inner_steps.append(_time_step(inner_order, STEP_TYPE_REST, rest_s, description="Rest"))
        inner_order += 1

    steps.append(_repeat_group(2, rounds, inner_steps))

    # Cooldown
    steps.append(_time_step(3, STEP_TYPE_COOLDOWN, 300, description="Cooldown"))

    return _wrap_workout(
        name,
        steps,
        sport_type=resolve_sport_type("hiit"),
        description=f"HIIT — {rounds} rounds, {work_s}s work / {rest_s}s rest, {len(exercises)} exercises",
    )


def build_walking_workout(name: str, duration_minutes: int, hr_zone: int = 1) -> dict[str, Any]:
    """Build a walking workout — simple timed step.

    Args:
        name: Workout name.
        duration_minutes: Walk duration in minutes.
        hr_zone: Garmin HR zone (default: 1).
    """
    steps = [
        _time_step(1, STEP_TYPE_INTERVAL, duration_minutes * 60, hr_zone=hr_zone, description="Walk"),
    ]
    return _wrap_workout(
        name,
        steps,
        sport_type=SPORT_TYPE_WALKING,
        description=f"Walking — {duration_minutes} min",
    )


# ── Workout Type Registry ─────────────────────────────────────────────

WORKOUT_TYPES = {
    "easy_run": {
        "builder": "easy_run",
        "description": "Steady easy run at low HR",
        "parameters": {
            "duration_minutes": "Main run duration in minutes (required)",
            "hr_zone": "Garmin HR zone 1-5 (default: 1)",
            "warmup_minutes": "Warmup duration (default: 0)",
            "cooldown_minutes": "Cooldown duration (default: 0)",
        },
    },
    "run_walk": {
        "builder": "run_walk",
        "description": "Run/walk intervals — great for return to running",
        "parameters": {
            "intervals": "Number of run/walk cycles (required)",
            "run_minutes": "Duration of each run interval (required)",
            "walk_minutes": "Duration of each walk interval (required)",
            "hr_zone": "Garmin HR zone for run intervals (default: 1)",
            "warmup_minutes": "Warmup duration (default: 0)",
            "cooldown_minutes": "Cooldown duration (default: 0)",
        },
    },
    "tempo": {
        "builder": "tempo_run",
        "description": "Tempo run with warmup and cooldown",
        "parameters": {
            "warmup_minutes": "Warmup duration (required)",
            "tempo_minutes": "Tempo portion duration (required)",
            "cooldown_minutes": "Cooldown duration (required)",
            "tempo_hr_zone": "Garmin HR zone for tempo (default: 3)",
        },
    },
    "intervals": {
        "builder": "interval_repeats",
        "description": "Distance-based interval repeats",
        "parameters": {
            "warmup_minutes": "Warmup duration (required)",
            "repeats": "Number of repeats (required)",
            "distance_meters": "Distance per repeat in meters (required)",
            "recovery_minutes": "Recovery jog between repeats (required)",
            "cooldown_minutes": "Cooldown duration (required)",
            "hr_zone": "Garmin HR zone for hard intervals (default: 4)",
        },
    },
    "strides": {
        "builder": "strides",
        "description": "Easy run with strides at the end",
        "parameters": {
            "easy_minutes": "Duration of easy run portion (required)",
            "stride_count": "Number of strides (required)",
            "stride_seconds": "Duration of each stride (default: 20)",
            "recovery_seconds": "Recovery between strides (default: 60)",
            "hr_zone": "Garmin HR zone for easy portion (default: 1)",
            "warmup_minutes": "Warmup duration (default: 0)",
            "cooldown_minutes": "Cooldown duration (default: 0)",
        },
    },
    "strength": {
        "builder": "build_strength_workout",
        "description": "Strength training with exercises, sets, reps, and rest periods",
        "parameters": {
            "exercises": "List of exercise dicts: {name, sets, reps, duration_s, rest_s, notes} (required)",
        },
    },
    "mobility": {
        "builder": "build_mobility_workout",
        "description": "Mobility/stretching with timed holds",
        "parameters": {
            "exercises": "List of exercise dicts: {name, sets, duration_s, rest_s, notes} (required)",
        },
    },
    "yoga": {
        "builder": "build_yoga_workout",
        "description": "Yoga session — single timed block",
        "parameters": {
            "duration_minutes": "Session duration in minutes (required)",
            "style": "Style label e.g. 'Yin', 'Vinyasa', 'Restorative' (optional)",
        },
    },
    "cardio": {
        "builder": "build_cardio_workout",
        "description": "General cardio with HR zone target",
        "parameters": {
            "duration_minutes": "Session duration in minutes (required)",
            "intensity": "One of: easy, moderate, hard (default: moderate)",
        },
    },
    "hiit": {
        "builder": "build_hiit_workout",
        "description": "HIIT with repeating rounds of timed work/rest intervals",
        "parameters": {
            "rounds": "Number of rounds (required)",
            "work_s": "Work interval duration in seconds (required)",
            "rest_s": "Rest interval duration in seconds (required)",
            "exercises": "List of exercise name strings (required)",
        },
    },
    "walking": {
        "builder": "build_walking_workout",
        "description": "Simple timed walk",
        "parameters": {
            "duration_minutes": "Walk duration in minutes (required)",
            "hr_zone": "Garmin HR zone (default: 1)",
        },
    },
    "custom": {
        "builder": "custom_workout",
        "description": "Arbitrary workout from raw step JSON",
        "parameters": {
            "steps_json": "List of raw Garmin step dicts (required)",
            "description": "Optional description",
        },
    },
}
