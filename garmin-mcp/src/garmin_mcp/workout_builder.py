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

SPORT_TYPE_RUNNING = {"sportTypeId": 1, "sportTypeKey": "running"}

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


def _wrap_workout(name: str, steps: list[dict[str, Any]], *, description: str | None = None) -> dict[str, Any]:
    """Wrap steps into a complete Garmin workout JSON payload."""
    workout: dict[str, Any] = {
        "workoutId": None,
        "ownerId": None,
        "workoutName": name,
        "sportType": SPORT_TYPE_RUNNING,
        "workoutSegments": [
            {
                "segmentOrder": 1,
                "sportType": SPORT_TYPE_RUNNING,
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


def custom_workout(name: str, steps_json: list[dict[str, Any]], *, description: str | None = None) -> dict[str, Any]:
    """Build a workout from raw step JSON — escape hatch for arbitrary workouts.

    Args:
        name: Workout name.
        steps_json: List of raw Garmin step dicts (ExecutableStepDTO or RepeatGroupDTO).
        description: Optional description.
    """
    return _wrap_workout(name, steps_json, description=description)


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
    "custom": {
        "builder": "custom_workout",
        "description": "Arbitrary workout from raw step JSON",
        "parameters": {
            "steps_json": "List of raw Garmin step dicts (required)",
            "description": "Optional description",
        },
    },
}
