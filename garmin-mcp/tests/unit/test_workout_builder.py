"""Unit tests for workout_builder module."""

from __future__ import annotations

import pytest

from garmin_mcp.workout_builder import (
    WORKOUT_TYPES,
    custom_workout,
    easy_run,
    interval_repeats,
    run_walk,
    strides,
    tempo_run,
)


class TestEasyRun:
    def test_basic_easy_run(self):
        w = easy_run("Easy 30", 30)
        assert w["workoutName"] == "Easy 30"
        assert w["sportType"]["sportTypeKey"] == "running"

        steps = w["workoutSegments"][0]["workoutSteps"]
        assert len(steps) == 1
        assert steps[0]["stepType"]["stepTypeKey"] == "interval"
        assert steps[0]["endConditionValue"] == 1800.0  # 30 min in seconds
        assert steps[0]["targetType"]["workoutTargetTypeKey"] == "heart.rate.zone"
        assert steps[0]["zoneNumber"] == 1

    def test_easy_run_with_warmup_cooldown(self):
        w = easy_run("Easy 25", 25, hr_zone=2, warmup_minutes=5, cooldown_minutes=5)
        steps = w["workoutSegments"][0]["workoutSteps"]
        assert len(steps) == 3
        assert steps[0]["stepType"]["stepTypeKey"] == "warmup"
        assert steps[0]["endConditionValue"] == 300.0
        assert steps[1]["stepType"]["stepTypeKey"] == "interval"
        assert steps[1]["zoneNumber"] == 2
        assert steps[2]["stepType"]["stepTypeKey"] == "cooldown"
        assert steps[2]["endConditionValue"] == 300.0

    def test_easy_run_step_order(self):
        w = easy_run("Test", 20, warmup_minutes=5, cooldown_minutes=5)
        steps = w["workoutSegments"][0]["workoutSteps"]
        assert steps[0]["stepOrder"] == 1
        assert steps[1]["stepOrder"] == 2
        assert steps[2]["stepOrder"] == 3

    def test_easy_run_no_warmup(self):
        w = easy_run("Test", 30, warmup_minutes=0)
        steps = w["workoutSegments"][0]["workoutSteps"]
        assert len(steps) == 1
        assert steps[0]["stepType"]["stepTypeKey"] == "interval"


class TestRunWalk:
    def test_basic_run_walk(self):
        w = run_walk("RW 5x3/1", 5, 3, 1)
        steps = w["workoutSegments"][0]["workoutSteps"]
        assert len(steps) == 1  # Just the repeat group
        repeat = steps[0]
        assert repeat["type"] == "RepeatGroupDTO"
        assert repeat["numberOfIterations"] == 5
        inner = repeat["workoutSteps"]
        assert len(inner) == 2
        assert inner[0]["endConditionValue"] == 180.0  # 3 min
        assert inner[0]["description"] == "Run"
        assert inner[1]["endConditionValue"] == 60.0  # 1 min
        assert inner[1]["description"] == "Walk"

    def test_run_walk_with_warmup_cooldown(self):
        w = run_walk("RW", 3, 2, 1, warmup_minutes=5, cooldown_minutes=3)
        steps = w["workoutSegments"][0]["workoutSteps"]
        assert len(steps) == 3
        assert steps[0]["stepType"]["stepTypeKey"] == "warmup"
        assert steps[1]["type"] == "RepeatGroupDTO"
        assert steps[2]["stepType"]["stepTypeKey"] == "cooldown"

    def test_run_walk_hr_zone(self):
        w = run_walk("RW", 4, 3, 1, hr_zone=2)
        repeat = w["workoutSegments"][0]["workoutSteps"][0]
        run_step = repeat["workoutSteps"][0]
        assert run_step["zoneNumber"] == 2
        # Walk step should not have HR zone
        walk_step = repeat["workoutSteps"][1]
        assert walk_step["targetType"]["workoutTargetTypeKey"] == "no.target"

    def test_run_walk_description(self):
        w = run_walk("Test", 5, 3, 1)
        assert "5x" in w["description"]
        assert "3min run" in w["description"]
        assert "1min walk" in w["description"]


class TestTempoRun:
    def test_basic_tempo(self):
        w = tempo_run("Tempo 20", 10, 20, 10)
        steps = w["workoutSegments"][0]["workoutSteps"]
        assert len(steps) == 3
        assert steps[0]["stepType"]["stepTypeKey"] == "warmup"
        assert steps[0]["endConditionValue"] == 600.0
        assert steps[1]["stepType"]["stepTypeKey"] == "interval"
        assert steps[1]["endConditionValue"] == 1200.0
        assert steps[1]["zoneNumber"] == 3  # default tempo zone
        assert steps[2]["stepType"]["stepTypeKey"] == "cooldown"

    def test_tempo_custom_zone(self):
        w = tempo_run("Tempo", 10, 15, 10, tempo_hr_zone=4)
        steps = w["workoutSegments"][0]["workoutSteps"]
        assert steps[1]["zoneNumber"] == 4


class TestIntervalRepeats:
    def test_basic_intervals(self):
        w = interval_repeats("400m x 8", 10, 8, 400, 2, 10)
        steps = w["workoutSegments"][0]["workoutSteps"]
        assert len(steps) == 3
        assert steps[0]["stepType"]["stepTypeKey"] == "warmup"

        repeat = steps[1]
        assert repeat["type"] == "RepeatGroupDTO"
        assert repeat["numberOfIterations"] == 8
        inner = repeat["workoutSteps"]
        assert len(inner) == 2
        # Hard interval is distance-based
        assert inner[0]["endCondition"]["conditionTypeKey"] == "distance"
        assert inner[0]["endConditionValue"] == 400
        assert inner[0]["zoneNumber"] == 4
        # Recovery is time-based
        assert inner[1]["endCondition"]["conditionTypeKey"] == "time"
        assert inner[1]["endConditionValue"] == 120.0

        assert steps[2]["stepType"]["stepTypeKey"] == "cooldown"

    def test_intervals_custom_zone(self):
        w = interval_repeats("Test", 10, 4, 800, 3, 10, hr_zone=5)
        repeat = w["workoutSegments"][0]["workoutSteps"][1]
        assert repeat["workoutSteps"][0]["zoneNumber"] == 5


class TestStrides:
    def test_basic_strides(self):
        w = strides("Easy + Strides", 25, 6)
        steps = w["workoutSegments"][0]["workoutSteps"]
        assert len(steps) == 2  # easy run + stride repeat group
        assert steps[0]["stepType"]["stepTypeKey"] == "interval"
        assert steps[0]["endConditionValue"] == 1500.0  # 25 min

        repeat = steps[1]
        assert repeat["type"] == "RepeatGroupDTO"
        assert repeat["numberOfIterations"] == 6
        inner = repeat["workoutSteps"]
        assert len(inner) == 2
        assert inner[0]["endConditionValue"] == 20  # 20s stride default
        assert inner[1]["endConditionValue"] == 60  # 60s recovery default

    def test_strides_custom_durations(self):
        w = strides("Test", 20, 4, stride_seconds=15, recovery_seconds=45)
        repeat = w["workoutSegments"][0]["workoutSteps"][1]
        assert repeat["workoutSteps"][0]["endConditionValue"] == 15
        assert repeat["workoutSteps"][1]["endConditionValue"] == 45

    def test_strides_with_warmup_cooldown(self):
        w = strides("Test", 20, 4, warmup_minutes=5, cooldown_minutes=3)
        steps = w["workoutSegments"][0]["workoutSteps"]
        assert len(steps) == 4
        assert steps[0]["stepType"]["stepTypeKey"] == "warmup"
        assert steps[1]["stepType"]["stepTypeKey"] == "interval"  # easy run
        assert steps[2]["type"] == "RepeatGroupDTO"  # strides
        assert steps[3]["stepType"]["stepTypeKey"] == "cooldown"

    def test_strides_description(self):
        w = strides("Test", 20, 6, stride_seconds=20)
        assert "6 strides" in w["description"]


class TestCustomWorkout:
    def test_custom_passes_through(self):
        raw_steps = [{"type": "ExecutableStepDTO", "stepOrder": 1}]
        w = custom_workout("Custom", raw_steps, description="My custom workout")
        assert w["workoutName"] == "Custom"
        assert w["workoutSegments"][0]["workoutSteps"] == raw_steps
        assert w["description"] == "My custom workout"


class TestWorkoutTypes:
    def test_all_types_registered(self):
        expected = {"easy_run", "run_walk", "tempo", "intervals", "strides", "custom"}
        assert set(WORKOUT_TYPES.keys()) == expected

    def test_each_type_has_required_fields(self):
        for name, info in WORKOUT_TYPES.items():
            assert "builder" in info, f"{name} missing builder"
            assert "description" in info, f"{name} missing description"
            assert "parameters" in info, f"{name} missing parameters"


class TestWorkoutStructure:
    """Tests common to all workout types — ensure consistent structure."""

    @pytest.mark.parametrize(
        "builder,kwargs",
        [
            (easy_run, {"name": "T", "duration_minutes": 30}),
            (run_walk, {"name": "T", "intervals": 3, "run_minutes": 2, "walk_minutes": 1}),
            (tempo_run, {"name": "T", "warmup_minutes": 10, "tempo_minutes": 20, "cooldown_minutes": 10}),
            (
                interval_repeats,
                {
                    "name": "T",
                    "warmup_minutes": 10,
                    "repeats": 4,
                    "distance_meters": 400,
                    "recovery_minutes": 2,
                    "cooldown_minutes": 10,
                },
            ),
            (strides, {"name": "T", "easy_minutes": 20, "stride_count": 4}),
        ],
    )
    def test_workout_has_required_fields(self, builder, kwargs):
        w = builder(**kwargs)
        assert w["workoutId"] is None
        assert w["workoutName"] == "T"
        assert w["sportType"]["sportTypeKey"] == "running"
        assert len(w["workoutSegments"]) == 1
        assert w["workoutSegments"][0]["segmentOrder"] == 1
        assert len(w["workoutSegments"][0]["workoutSteps"]) >= 1
