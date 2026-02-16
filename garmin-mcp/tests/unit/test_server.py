"""Unit tests for server module."""

from __future__ import annotations

from garmin_mcp.server import _build_workout


class TestBuildWorkout:
    def test_build_easy_run(self):
        w = _build_workout("easy_run", "Easy 30", {"duration_minutes": 30})
        assert w["workoutName"] == "Easy 30"
        assert w["sportType"]["sportTypeKey"] == "running"

    def test_build_run_walk(self):
        w = _build_workout("run_walk", "RW", {"intervals": 5, "run_minutes": 3, "walk_minutes": 1})
        assert w["workoutName"] == "RW"

    def test_build_tempo(self):
        w = _build_workout("tempo", "Tempo", {"warmup_minutes": 10, "tempo_minutes": 20, "cooldown_minutes": 10})
        assert w["workoutName"] == "Tempo"

    def test_build_intervals(self):
        w = _build_workout(
            "intervals",
            "400s",
            {"warmup_minutes": 10, "repeats": 8, "distance_meters": 400, "recovery_minutes": 2, "cooldown_minutes": 10},
        )
        assert w["workoutName"] == "400s"

    def test_build_strides(self):
        w = _build_workout("strides", "Strides", {"easy_minutes": 25, "stride_count": 6})
        assert w["workoutName"] == "Strides"

    def test_build_custom(self):
        w = _build_workout("custom", "Custom", {"steps_json": [{"type": "ExecutableStepDTO"}]})
        assert w["workoutName"] == "Custom"

    def test_build_unknown_type_raises(self):
        import pytest

        with pytest.raises(ValueError, match="Unknown workout type"):
            _build_workout("unknown", "Test", {})


class TestMainSignature:
    def test_main_is_callable(self):
        from garmin_mcp.server import main

        assert callable(main)
