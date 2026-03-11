"""Unit tests for workout_builder module."""

from __future__ import annotations

import pytest

from garmin_mcp.workout_builder import (
    WORKOUT_TYPES,
    build_cardio_workout,
    build_hiit_workout,
    build_mobility_workout,
    build_strength_workout,
    build_walking_workout,
    build_yoga_workout,
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


class TestStrengthWorkout:
    def test_basic_strength(self):
        exercises = [
            {"name": "Eccentric heel drops", "sets": 3, "reps": 15, "rest_s": 60},
            {"name": "Glute bridges", "sets": 3, "reps": 20, "rest_s": 45},
        ]
        w = build_strength_workout("Rehab Strength", exercises)
        assert w["sportType"]["sportTypeId"] == 5
        assert w["sportType"]["sportTypeKey"] == "strength_training"
        assert w["workoutSegments"][0]["sportType"]["sportTypeId"] == 5

        steps = w["workoutSegments"][0]["workoutSteps"]
        # warmup + (3 sets * 2 exercises) + (rest between each except last) + cooldown
        # warmup(1) + set1+rest + set2+rest + set3+rest + set1+rest + set2+rest + set3 + cooldown
        assert steps[0]["stepType"]["stepTypeKey"] == "warmup"
        assert steps[0]["endCondition"]["conditionTypeKey"] == "lap.button"
        assert steps[-1]["stepType"]["stepTypeKey"] == "cooldown"

    def test_strength_lap_button_for_reps(self):
        exercises = [{"name": "Squats", "sets": 2, "reps": 10, "rest_s": 60}]
        w = build_strength_workout("Test", exercises)
        steps = w["workoutSegments"][0]["workoutSteps"]
        # warmup + set1 + rest + set2 + cooldown = 5 steps
        assert len(steps) == 5
        # Set steps use lap button (reps-based)
        assert steps[1]["endCondition"]["conditionTypeKey"] == "lap.button"
        assert "set 1/2" in steps[1]["description"]
        # Rest step is timed
        assert steps[2]["endCondition"]["conditionTypeKey"] == "time"
        assert steps[2]["endConditionValue"] == 60

    def test_strength_timed_exercises(self):
        exercises = [{"name": "Plank", "sets": 3, "duration_s": 45, "rest_s": 30}]
        w = build_strength_workout("Core", exercises)
        steps = w["workoutSegments"][0]["workoutSteps"]
        # warmup + set1 + rest + set2 + rest + set3 + cooldown = 7 steps (no rest after last set)
        assert len(steps) == 7
        # Timed exercises use time condition
        assert steps[1]["endCondition"]["conditionTypeKey"] == "time"
        assert steps[1]["endConditionValue"] == 45

    def test_strength_with_notes(self):
        exercises = [{"name": "Heel drops", "sets": 1, "reps": 15, "rest_s": 60, "notes": "3s eccentric"}]
        w = build_strength_workout("Test", exercises)
        steps = w["workoutSegments"][0]["workoutSteps"]
        assert "3s eccentric" in steps[1]["description"]

    def test_strength_description(self):
        exercises = [
            {"name": "Squats", "sets": 1, "reps": 10, "rest_s": 60},
            {"name": "Lunges", "sets": 1, "reps": 10, "rest_s": 60},
        ]
        w = build_strength_workout("Leg Day", exercises)
        assert "Squats" in w["description"]
        assert "Lunges" in w["description"]

    def test_strength_multiple_exercises_rest_between(self):
        exercises = [
            {"name": "A", "sets": 1, "reps": 10, "rest_s": 60},
            {"name": "B", "sets": 1, "reps": 10, "rest_s": 60},
        ]
        w = build_strength_workout("Test", exercises)
        steps = w["workoutSegments"][0]["workoutSteps"]
        # warmup + A_set1 + rest + B_set1 + cooldown = 5
        assert len(steps) == 5
        assert steps[2]["stepType"]["stepTypeKey"] == "rest"


class TestMobilityWorkout:
    def test_basic_mobility(self):
        exercises = [
            {"name": "Hip flexor stretch", "sets": 2, "duration_s": 30, "rest_s": 10},
            {"name": "Hamstring stretch", "sets": 2, "duration_s": 45, "rest_s": 10},
        ]
        w = build_mobility_workout("Morning Mobility", exercises)
        assert w["sportType"]["sportTypeId"] == 11
        assert w["sportType"]["sportTypeKey"] == "mobility"

        steps = w["workoutSegments"][0]["workoutSteps"]
        assert steps[0]["stepType"]["stepTypeKey"] == "warmup"
        assert steps[-1]["stepType"]["stepTypeKey"] == "cooldown"

    def test_mobility_timed_steps(self):
        exercises = [{"name": "Stretch", "sets": 1, "duration_s": 60, "rest_s": 15}]
        w = build_mobility_workout("Test", exercises)
        steps = w["workoutSegments"][0]["workoutSteps"]
        # warmup + stretch + cooldown = 3 (no rest after last set of last exercise)
        assert len(steps) == 3
        assert steps[1]["endCondition"]["conditionTypeKey"] == "time"
        assert steps[1]["endConditionValue"] == 60

    def test_mobility_description(self):
        exercises = [{"name": "A", "sets": 1, "duration_s": 30, "rest_s": 10}]
        w = build_mobility_workout("Test", exercises)
        assert "1 exercises" in w["description"]


class TestYogaWorkout:
    def test_basic_yoga(self):
        w = build_yoga_workout("Morning Yoga", 30)
        assert w["sportType"]["sportTypeId"] == 7
        assert w["sportType"]["sportTypeKey"] == "yoga"

        steps = w["workoutSegments"][0]["workoutSteps"]
        assert len(steps) == 1
        assert steps[0]["endConditionValue"] == 1800.0

    def test_yoga_with_style(self):
        w = build_yoga_workout("Yin Session", 60, style="Yin")
        assert "Yin yoga" in w["description"]
        steps = w["workoutSegments"][0]["workoutSteps"]
        assert "Yin yoga" in steps[0]["description"]

    def test_yoga_no_style(self):
        w = build_yoga_workout("Yoga", 45)
        assert "Yoga" in w["description"]


class TestCardioWorkout:
    def test_basic_cardio(self):
        w = build_cardio_workout("Bike Ride", 30, "moderate")
        assert w["sportType"]["sportTypeId"] == 6
        assert w["sportType"]["sportTypeKey"] == "cardio"

        steps = w["workoutSegments"][0]["workoutSteps"]
        assert len(steps) == 3
        assert steps[0]["stepType"]["stepTypeKey"] == "warmup"
        assert steps[1]["stepType"]["stepTypeKey"] == "interval"
        assert steps[1]["zoneNumber"] == 2
        assert steps[2]["stepType"]["stepTypeKey"] == "cooldown"

    def test_cardio_easy(self):
        w = build_cardio_workout("Easy Cardio", 25, "easy")
        steps = w["workoutSegments"][0]["workoutSteps"]
        assert steps[1]["zoneNumber"] == 1

    def test_cardio_hard(self):
        w = build_cardio_workout("Hard Cardio", 40, "hard")
        steps = w["workoutSegments"][0]["workoutSteps"]
        assert steps[1]["zoneNumber"] == 3

    def test_cardio_invalid_intensity(self):
        with pytest.raises(ValueError, match="Invalid intensity"):
            build_cardio_workout("Test", 30, "extreme")

    def test_cardio_warmup_cooldown_5min(self):
        w = build_cardio_workout("Test", 30, "moderate")
        steps = w["workoutSegments"][0]["workoutSteps"]
        assert steps[0]["endConditionValue"] == 300  # 5 min warmup
        assert steps[2]["endConditionValue"] == 300  # 5 min cooldown
        assert steps[1]["endConditionValue"] == 1200  # 20 min main (30 - 10)


class TestHiitWorkout:
    def test_basic_hiit(self):
        w = build_hiit_workout("Tabata", 4, 20, 10, ["Burpees", "Squats"])
        assert w["sportType"]["sportTypeId"] == 9
        assert w["sportType"]["sportTypeKey"] == "hiit"

        steps = w["workoutSegments"][0]["workoutSteps"]
        assert len(steps) == 3  # warmup + repeat group + cooldown
        assert steps[0]["stepType"]["stepTypeKey"] == "warmup"
        assert steps[2]["stepType"]["stepTypeKey"] == "cooldown"

        repeat = steps[1]
        assert repeat["type"] == "RepeatGroupDTO"
        assert repeat["numberOfIterations"] == 4

    def test_hiit_inner_steps(self):
        w = build_hiit_workout("HIIT", 3, 30, 15, ["Push-ups", "Jump squats"])
        repeat = w["workoutSegments"][0]["workoutSteps"][1]
        inner = repeat["workoutSteps"]
        # 2 exercises * 2 (work + rest) = 4 inner steps
        assert len(inner) == 4
        assert inner[0]["description"] == "Push-ups"
        assert inner[0]["endConditionValue"] == 30
        assert inner[1]["description"] == "Rest"
        assert inner[1]["endConditionValue"] == 15
        assert inner[2]["description"] == "Jump squats"
        assert inner[2]["endConditionValue"] == 30
        assert inner[3]["description"] == "Rest"
        assert inner[3]["endConditionValue"] == 15

    def test_hiit_description(self):
        w = build_hiit_workout("Test", 5, 40, 20, ["A", "B", "C"])
        assert "5 rounds" in w["description"]
        assert "40s work" in w["description"]
        assert "20s rest" in w["description"]
        assert "3 exercises" in w["description"]


class TestWalkingWorkout:
    def test_basic_walking(self):
        w = build_walking_workout("Morning Walk", 45)
        assert w["sportType"]["sportTypeId"] == 12
        assert w["sportType"]["sportTypeKey"] == "walking"

        steps = w["workoutSegments"][0]["workoutSteps"]
        assert len(steps) == 1
        assert steps[0]["endConditionValue"] == 2700.0  # 45 min
        assert steps[0]["zoneNumber"] == 1

    def test_walking_custom_zone(self):
        w = build_walking_workout("Brisk Walk", 30, hr_zone=2)
        steps = w["workoutSegments"][0]["workoutSteps"]
        assert steps[0]["zoneNumber"] == 2

    def test_walking_description(self):
        w = build_walking_workout("Test", 60)
        assert "60 min" in w["description"]


class TestWorkoutTypes:
    def test_all_types_registered(self):
        expected = {
            "easy_run",
            "run_walk",
            "tempo",
            "intervals",
            "strides",
            "strength",
            "mobility",
            "yoga",
            "cardio",
            "hiit",
            "walking",
            "custom",
        }
        assert set(WORKOUT_TYPES.keys()) == expected

    def test_each_type_has_required_fields(self):
        for name, info in WORKOUT_TYPES.items():
            assert "builder" in info, f"{name} missing builder"
            assert "description" in info, f"{name} missing description"
            assert "parameters" in info, f"{name} missing parameters"


class TestWorkoutStructure:
    """Tests common to all workout types — ensure consistent structure."""

    @pytest.mark.parametrize(
        "builder,kwargs,expected_sport",
        [
            (easy_run, {"name": "T", "duration_minutes": 30}, "running"),
            (run_walk, {"name": "T", "intervals": 3, "run_minutes": 2, "walk_minutes": 1}, "running"),
            (tempo_run, {"name": "T", "warmup_minutes": 10, "tempo_minutes": 20, "cooldown_minutes": 10}, "running"),
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
                "running",
            ),
            (strides, {"name": "T", "easy_minutes": 20, "stride_count": 4}, "running"),
            (
                build_strength_workout,
                {"name": "T", "exercises": [{"name": "Squats", "sets": 1, "reps": 10, "rest_s": 60}]},
                "strength_training",
            ),
            (
                build_mobility_workout,
                {"name": "T", "exercises": [{"name": "Stretch", "sets": 1, "duration_s": 30, "rest_s": 10}]},
                "mobility",
            ),
            (build_yoga_workout, {"name": "T", "duration_minutes": 30}, "yoga"),
            (build_cardio_workout, {"name": "T", "duration_minutes": 30, "intensity": "moderate"}, "cardio"),
            (
                build_hiit_workout,
                {"name": "T", "rounds": 3, "work_s": 30, "rest_s": 15, "exercises": ["Burpees"]},
                "hiit",
            ),
            (build_walking_workout, {"name": "T", "duration_minutes": 30}, "walking"),
        ],
    )
    def test_workout_has_required_fields(self, builder, kwargs, expected_sport):
        w = builder(**kwargs)
        assert w["workoutId"] is None
        assert w["workoutName"] == "T"
        assert w["sportType"]["sportTypeKey"] == expected_sport
        assert len(w["workoutSegments"]) == 1
        assert w["workoutSegments"][0]["segmentOrder"] == 1
        assert w["workoutSegments"][0]["sportType"]["sportTypeKey"] == expected_sport
        assert len(w["workoutSegments"][0]["workoutSteps"]) >= 1
