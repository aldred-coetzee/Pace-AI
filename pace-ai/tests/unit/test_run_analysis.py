"""Unit tests for run analysis tools."""

from __future__ import annotations

import pytest

from pace_ai.tools.run_analysis import (
    analyze_run,
    assess_fitness_trend,
    assess_race_readiness,
    detect_anomalies,
    detect_workout_type,
    get_training_distribution,
)

from ..conftest import sample_activity_detail

# ── analyze_run ───────────────────────────────────────────────────────


class TestAnalyzeRun:
    def test_basic_split_analysis(self):
        activity = sample_activity_detail()
        result = analyze_run(activity)
        assert "pacing" in result
        assert result["pacing"]["split_count"] == 8
        assert "pace_cv_pct" in result["pacing"]

    def test_even_pacing_grade(self):
        activity = sample_activity_detail()
        result = analyze_run(activity)
        # All splits are 270s — very even
        assert result["pacing"]["pacing_grade"] in ("excellent", "good")

    def test_hr_drift_from_streams(self):
        activity = sample_activity_detail()
        # Simulate HR drift: lower in first half, higher in second
        streams = {
            "heartrate": [140] * 50 + [160] * 50,
            "time": list(range(100)),
        }
        result = analyze_run(activity, streams=streams)
        assert "hr_analysis" in result
        assert result["hr_analysis"]["cardiac_drift_pct"] > 0
        assert result["hr_analysis"]["first_half_avg_hr"] < result["hr_analysis"]["second_half_avg_hr"]

    def test_zone_distribution_with_athlete_zones(self):
        activity = sample_activity_detail()
        streams = {
            "heartrate": [130] * 30 + [155] * 30 + [175] * 40,
            "time": list(range(100)),
        }
        zones = {
            "heart_rate": {
                "zones": [
                    {"min": 0, "max": 120},
                    {"min": 120, "max": 150},
                    {"min": 150, "max": 170},
                    {"min": 170, "max": 190},
                    {"min": 190, "max": -1},
                ]
            }
        }
        result = analyze_run(activity, streams=streams, athlete_zones=zones)
        assert "zone_distribution" in result
        assert len(result["zone_distribution"]) == 5

    def test_cadence_from_activity(self):
        activity = sample_activity_detail()
        activity["average_cadence"] = 86  # Strava stores half-cycles
        result = analyze_run(activity)
        assert "cadence" in result
        assert result["cadence"]["average_spm"] == 172  # doubled

    def test_flags_for_hard_easy_run(self):
        activity = sample_activity_detail()
        activity["workout_type"] = 0  # Not tagged as race/workout
        streams = {
            "heartrate": [175] * 100,  # Very high HR throughout
            "time": list(range(100)),
        }
        zones = {
            "heart_rate": {
                "zones": [
                    {"min": 0, "max": 120},
                    {"min": 120, "max": 150},
                    {"min": 150, "max": 170},
                    {"min": 170, "max": 190},
                    {"min": 190, "max": -1},
                ]
            }
        }
        result = analyze_run(activity, streams=streams, athlete_zones=zones)
        # Should flag that too little time was in easy zones
        assert any("zones 1-2" in f for f in result["flags"])

    def test_zone_distribution_empty_zones(self):
        # Test edge case: empty zones list returns empty list
        from pace_ai.tools.run_analysis import _compute_time_in_zones

        hr_stream = [140, 150, 160]
        zones = []
        time_stream = [0, 1, 2]
        result = _compute_time_in_zones(hr_stream, zones, time_stream)
        assert result == []

    def test_zone_distribution_empty_hr_stream(self):
        # Test edge case: empty hr_stream returns empty list
        from pace_ai.tools.run_analysis import _compute_time_in_zones

        hr_stream = []
        zones = [{"min": 0, "max": 120}, {"min": 120, "max": 150}]
        time_stream = []
        result = _compute_time_in_zones(hr_stream, zones, time_stream)
        assert result == []

    def test_zone_distribution_short_time_stream(self):
        # Test edge case: time_stream shorter than hr_stream (guards against index error)
        from pace_ai.tools.run_analysis import _compute_time_in_zones

        hr_stream = [140, 150, 160, 170]
        zones = [{"min": 0, "max": 150}, {"min": 150, "max": 180}]
        time_stream = [0, 1]  # Shorter than hr_stream
        # Should not crash, uses default dt=1 for missing time data
        result = _compute_time_in_zones(hr_stream, zones, time_stream)
        assert len(result) == 2
        assert all("zone_index" in z for z in result)


# ── detect_workout_type ───────────────────────────────────────────────


class TestDetectWorkoutType:
    def test_race_tagged(self):
        activity = {"workout_type": 1, "distance": 5000, "moving_time": 1200}
        result = detect_workout_type(activity)
        assert result["detected_type"] == "race"

    def test_long_run_by_distance(self):
        activity = {"distance": 22000, "moving_time": 7200, "laps": [], "splits_metric": []}
        result = detect_workout_type(activity)
        assert result["detected_type"] == "long_run"

    def test_long_run_by_duration(self):
        activity = {"distance": 12000, "moving_time": 6000, "laps": [], "splits_metric": []}
        result = detect_workout_type(activity)
        assert result["detected_type"] == "long_run"

    def test_recovery_run(self):
        # Short, slow run
        activity = {"distance": 4000, "moving_time": 1800, "laps": [], "splits_metric": []}
        # 4km in 30 min = 2.22 m/s (very slow)
        result = detect_workout_type(activity)
        assert result["detected_type"] == "recovery"

    def test_interval_detection(self):
        # Create laps with alternating fast/slow speeds
        laps = []
        for i in range(8):
            speed = 5.0 if i % 2 == 0 else 2.0  # work vs rest
            laps.append({"distance": 400, "average_speed": speed, "moving_time": 80 if i % 2 == 0 else 200})
        activity = {"distance": 6000, "moving_time": 2400, "laps": laps, "splits_metric": []}
        result = detect_workout_type(activity)
        assert result["detected_type"] == "intervals"

    def test_easy_run_default(self):
        activity = {"distance": 8000, "moving_time": 2800, "laps": [], "splits_metric": []}
        result = detect_workout_type(activity)
        assert result["detected_type"] == "easy_run"

    def test_tempo_detection(self):
        # Even pacing with high HR
        splits = [{"split": i + 1, "distance": 1000, "moving_time": 250, "elapsed_time": 250} for i in range(6)]
        activity = {
            "distance": 6000,
            "moving_time": 1500,
            "laps": [],
            "splits_metric": splits,
            "average_heartrate": 170,
            "max_heartrate": 190,
        }
        result = detect_workout_type(activity)
        assert result["detected_type"] == "tempo"


# ── get_training_distribution ─────────────────────────────────────────


class TestGetTrainingDistribution:
    def test_basic_distribution(self):
        activities = [
            {"type": "Run", "moving_time_s": 3600, "average_heartrate": 140, "max_heartrate": 190, "id": 1},
            {"type": "Run", "moving_time_s": 2400, "average_heartrate": 165, "max_heartrate": 190, "id": 2},
            {"type": "Run", "moving_time_s": 1800, "average_heartrate": 175, "max_heartrate": 190, "id": 3},
        ]
        result = get_training_distribution(activities)
        assert result["run_count"] == 3
        assert "distribution" in result
        assert result["distribution"]["easy_pct"] > 0
        assert result["distribution"]["hard_pct"] > 0

    def test_80_20_assessment(self):
        # 4 easy runs, 1 hard
        activities = [
            {"type": "Run", "moving_time_s": 3600, "average_heartrate": 130, "max_heartrate": 190, "id": i}
            for i in range(4)
        ] + [{"type": "Run", "moving_time_s": 1800, "average_heartrate": 178, "max_heartrate": 190, "id": 5}]
        result = get_training_distribution(activities)
        assert result["polarization"] == "well_polarized"

    def test_no_runs(self):
        result = get_training_distribution([])
        assert result["run_count"] == 0

    def test_filters_non_running(self):
        activities = [
            {"type": "Ride", "moving_time_s": 3600, "average_heartrate": 140, "max_heartrate": 190, "id": 1},
            {"type": "Run", "moving_time_s": 2400, "average_heartrate": 140, "max_heartrate": 190, "id": 2},
        ]
        result = get_training_distribution(activities)
        assert result["run_count"] == 1

    def test_suffer_score_fallback(self):
        activities = [
            {"type": "Run", "moving_time_s": 3600, "suffer_score": 40, "id": 1},
            {"type": "Run", "moving_time_s": 1800, "suffer_score": 120, "id": 2},
        ]
        result = get_training_distribution(activities)
        assert result["run_count"] == 2
        total = (
            result["distribution"]["easy_pct"]
            + result["distribution"]["moderate_pct"]
            + result["distribution"]["hard_pct"]
        )
        assert total == pytest.approx(100, abs=0.5)


# ── assess_fitness_trend ──────────────────────────────────────────────


class TestAssessFitnessTrend:
    def test_vdot_from_best_efforts(self):
        best_efforts = [
            {"distance_name": "5k", "distance_m": 5000, "elapsed_time": 1200, "elapsed_time_formatted": "20:00"},
        ]
        weekly = [{"total_distance_km": 40, "longest_run_km": 15} for _ in range(4)]
        result = assess_fitness_trend(best_efforts, weekly)
        assert "current_vdot" in result
        assert result["current_vdot"] > 0

    def test_volume_trend_increasing(self):
        best_efforts = []
        weekly = [
            {"total_distance_km": 30},
            {"total_distance_km": 32},
            {"total_distance_km": 35},
            {"total_distance_km": 38},
        ]
        result = assess_fitness_trend(best_efforts, weekly)
        assert result["volume_trend"]["trend_direction"] == "increasing"

    def test_consistency_metric(self):
        best_efforts = []
        weekly = [
            {"total_distance_km": 30},
            {"total_distance_km": 0},
            {"total_distance_km": 30},
            {"total_distance_km": 30},
        ]
        result = assess_fitness_trend(best_efforts, weekly)
        assert result["consistency"]["active_weeks"] == 3
        assert result["consistency"]["consistency_pct"] == 75.0


# ── assess_race_readiness ────────────────────────────────────────────


class TestAssessRaceReadiness:
    def test_basic_assessment(self):
        goals = [{"race_type": "5k", "target_time_seconds": 1200, "target_time_formatted": "20:00"}]
        best_efforts = [
            {"distance_name": "5k", "distance_m": 5000, "elapsed_time": 1250},
        ]
        weekly = [
            {"total_distance_km": 35, "longest_run_km": 12},
            {"total_distance_km": 38, "longest_run_km": 14},
            {"total_distance_km": 40, "longest_run_km": 15},
            {"total_distance_km": 35, "longest_run_km": 12},
        ]
        result = assess_race_readiness(goals, best_efforts, weekly)
        assert "assessments" in result
        assert len(result["assessments"]) == 1
        assert result["assessments"][0]["overall_score"] > 0

    def test_no_goals_returns_error(self):
        result = assess_race_readiness([], [], [])
        assert "error" in result

    def test_includes_strengths_and_risks(self):
        goals = [{"race_type": "half marathon", "target_time_seconds": 5400, "target_time_formatted": "1:30:00"}]
        best_efforts = [
            {"distance_name": "5k", "distance_m": 5000, "elapsed_time": 1100},
        ]
        weekly = [
            {"total_distance_km": 50, "longest_run_km": 20},
        ] * 8
        result = assess_race_readiness(goals, best_efforts, weekly)
        assessment = result["assessments"][0]
        assert isinstance(assessment["strengths"], list)
        assert isinstance(assessment["risks"], list)

    def test_fallback_vdot_from_weekly_summary(self):
        # Test fallback VDOT estimation when best_efforts is empty
        goals = [{"race_type": "5k", "target_time_seconds": 1200, "target_time_formatted": "20:00"}]
        best_efforts = []  # No best efforts available
        weekly = [
            {"total_distance_km": 35, "total_time_s": 10500, "longest_run_km": 12},  # ~5:00/km avg pace
            {"total_distance_km": 40, "total_time_s": 12000, "longest_run_km": 15},  # ~5:00/km avg pace
            {"total_distance_km": 38, "total_time_s": 11400, "longest_run_km": 14},  # ~5:00/km avg pace
        ]
        result = assess_race_readiness(goals, best_efforts, weekly)
        assessment = result["assessments"][0]
        # Should estimate VDOT from weekly pace data
        assert assessment["current_vdot"] is not None
        assert assessment["current_vdot"] > 0


# ── detect_anomalies ────────────────────────────────────────────────


class TestDetectAnomalies:
    def test_clean_activity(self):
        activity = sample_activity_detail()
        result = detect_anomalies(activity)
        assert result["anomaly_count"] == 0
        assert result["data_quality_score"] >= 8
        assert result["usable_for_coaching"] is True

    def test_impossible_speed(self):
        activity = {"id": 1, "distance": 10000, "moving_time": 1000}  # 10 m/s = 1:40/km
        result = detect_anomalies(activity)
        assert any(a["type"] == "gps" for a in result["anomalies"])

    def test_zero_distance(self):
        activity = {"id": 1, "distance": 50, "moving_time": 600}
        result = detect_anomalies(activity)
        assert any(a["type"] == "gps" for a in result["anomalies"])

    def test_hr_too_high(self):
        activity = {"id": 1, "distance": 5000, "moving_time": 1500}
        streams = {"heartrate": [150] * 50 + [280] * 10}
        result = detect_anomalies(activity, streams)
        assert any(a["type"] == "hr" and a["severity"] == "high" for a in result["anomalies"])

    def test_hr_dropout(self):
        activity = {"id": 1, "distance": 5000, "moving_time": 1500}
        streams = {"heartrate": [0] * 30 + [150] * 70}
        result = detect_anomalies(activity, streams)
        assert any(a["type"] == "hr" for a in result["anomalies"])

    def test_hr_stuck(self):
        activity = {"id": 1, "distance": 5000, "moving_time": 1500}
        streams = {"heartrate": [155] * 50}
        result = detect_anomalies(activity, streams)
        assert any("stuck" in a["detail"] for a in result["anomalies"])

    def test_split_anomaly(self):
        activity = {
            "id": 1,
            "distance": 5000,
            "moving_time": 1500,
            "splits_metric": [
                {"split": 1, "distance": 1000, "moving_time": 300},
                {"split": 2, "distance": 1000, "moving_time": 300},
                {"split": 3, "distance": 1000, "moving_time": 600},  # 100% slower
                {"split": 4, "distance": 1000, "moving_time": 300},
            ],
        }
        result = detect_anomalies(activity)
        assert any(a["type"] == "pace" for a in result["anomalies"])

    def test_missing_data_flags(self):
        activity = {"id": 1, "distance": 5000, "moving_time": 1500}
        result = detect_anomalies(activity)
        assert "heart_rate" in result["missing_data"]
        assert "splits" in result["missing_data"]
        assert "cadence" in result["missing_data"]

    def test_quality_score_degrades(self):
        # Multiple high-severity anomalies should tank the score
        activity = {"id": 1, "distance": 50, "moving_time": 600}
        streams = {"heartrate": [155] * 50}
        result = detect_anomalies(activity, streams)
        assert result["data_quality_score"] < 5
        assert result["usable_for_coaching"] is False


# ── calculate_cardiac_decoupling ──────────────────────────────────────


class TestCalculateCardiacDecoupling:
    def test_steady_run_minimal_decoupling(self):
        from pace_ai.tools.run_analysis import calculate_cardiac_decoupling

        # Steady pace and HR throughout
        hr_stream = [150] * 50 + [152] * 50  # Very slight increase
        velocity_stream = [3.5] * 100  # Constant velocity
        result = calculate_cardiac_decoupling(hr_stream, velocity_stream)

        assert "decoupling_pct" in result
        assert result["decoupling_pct"] < 3
        assert result["assessment"] in ("excellent", "good")

    def test_declining_efficiency(self):
        from pace_ai.tools.run_analysis import calculate_cardiac_decoupling

        # Same pace, but HR climbs in second half (poor decoupling)
        hr_stream = [140] * 50 + [160] * 50
        velocity_stream = [3.5] * 100  # Same velocity throughout
        result = calculate_cardiac_decoupling(hr_stream, velocity_stream)

        assert result["decoupling_pct"] > 5
        assert result["assessment"] in ("adequate", "poor")

    def test_insufficient_data(self):
        from pace_ai.tools.run_analysis import calculate_cardiac_decoupling

        # Too few data points
        hr_stream = [150] * 10
        velocity_stream = [3.5] * 10
        result = calculate_cardiac_decoupling(hr_stream, velocity_stream)

        assert "error" in result
        assert "at least 20" in result["error"].lower()

    def test_filters_stops(self):
        from pace_ai.tools.run_analysis import calculate_cardiac_decoupling

        # Include some stops (zero velocity) that should be filtered
        hr_stream = [140] * 30 + [0] * 10 + [145] * 30 + [0] * 10 + [150] * 20
        velocity_stream = [3.5] * 30 + [0] * 10 + [3.5] * 30 + [0] * 10 + [3.5] * 20
        result = calculate_cardiac_decoupling(hr_stream, velocity_stream)

        # Should still work by filtering out zero-velocity points
        assert "decoupling_pct" in result

    def test_filters_low_hr(self):
        from pace_ai.tools.run_analysis import calculate_cardiac_decoupling

        # Include some invalid low HR readings
        hr_stream = [30] * 10 + [140] * 50 + [145] * 50
        velocity_stream = [3.5] * 110
        result = calculate_cardiac_decoupling(hr_stream, velocity_stream)

        # Should filter out HR < 60
        assert "decoupling_pct" in result

    def test_first_and_second_half_breakdown(self):
        from pace_ai.tools.run_analysis import calculate_cardiac_decoupling

        hr_stream = [140] * 50 + [150] * 50
        velocity_stream = [3.5] * 100
        result = calculate_cardiac_decoupling(hr_stream, velocity_stream)

        assert "first_half" in result
        assert "second_half" in result
        assert "avg_velocity_mps" in result["first_half"]
        assert "avg_hr_bpm" in result["first_half"]
        assert "efficiency_ratio" in result["first_half"]

    def test_assessment_ranges(self):
        from pace_ai.tools.run_analysis import calculate_cardiac_decoupling

        # Test different decoupling levels
        # Excellent: < 3%
        result_excellent = calculate_cardiac_decoupling([150] * 100, [3.5] * 100)
        assert result_excellent["assessment"] == "excellent"

        # Good: 3-5%
        hr_good = [140] * 50 + [145] * 50
        result_good = calculate_cardiac_decoupling(hr_good, [3.5] * 100)
        if result_good["decoupling_pct"] < 5:
            assert result_good["assessment"] in ("excellent", "good")


# ── HR reliability warnings ────────────────────────────────────────────


class TestHRReliabilityWarnings:
    def test_long_run_warning(self):
        # Run > 90 minutes
        activity = sample_activity_detail()
        activity["moving_time"] = 6000  # 100 minutes
        result = analyze_run(activity)

        assert "hr_reliability_warnings" in result
        assert any(w["condition"] == "long_run_cardiac_drift" for w in result["hr_reliability_warnings"])

    def test_heat_warning(self):
        activity = sample_activity_detail()
        activity["average_temp"] = 28  # Hot day
        result = analyze_run(activity)

        assert "hr_reliability_warnings" in result
        assert any(w["condition"] == "heat_elevated_hr" for w in result["hr_reliability_warnings"])

    def test_interval_hr_lag_warning(self):
        # Many short laps
        laps = [{"distance": 400, "moving_time": 90, "average_speed": 4.5} for _ in range(8)]
        activity = sample_activity_detail()
        activity["laps"] = laps
        result = analyze_run(activity)

        assert "hr_reliability_warnings" in result
        assert any(w["condition"] == "interval_hr_lag" for w in result["hr_reliability_warnings"])

    def test_optical_hr_lag_warning(self):
        activity = sample_activity_detail()
        # Simulate optical sensor warm-up lag: need longer stream
        # early = first 25% (60 points), later = next 25% (60-120)
        # For detection: (later - early) / later > 0.15
        # If early=100, later=160, then (160-100)/160 = 0.375 > 0.15
        streams = {
            "heartrate": [100] * 60 + [160] * 180,  # Low start, then jump
            "time": list(range(240)),
        }
        result = analyze_run(activity, streams=streams)

        assert "hr_reliability_warnings" in result
        assert any(w["condition"] == "optical_hr_lag" for w in result["hr_reliability_warnings"])

    def test_normal_activity_no_warnings(self):
        # Normal activity: moderate duration, moderate temp, no weird HR
        activity = sample_activity_detail()
        activity["moving_time"] = 2400  # 40 minutes
        activity["average_temp"] = 18  # Cool
        activity["laps"] = []
        streams = {
            "heartrate": [150] * 100,
            "time": list(range(100)),
        }
        result = analyze_run(activity, streams=streams)

        # Should have no warnings (or at least not the specific ones we flag)
        if "hr_reliability_warnings" in result:
            assert len(result["hr_reliability_warnings"]) == 0

    def test_analyze_run_includes_hr_warnings(self):
        # Integration: verify hr_reliability_warnings appears in analyze_run result
        activity = sample_activity_detail()
        activity["moving_time"] = 6000  # Long run
        result = analyze_run(activity)

        # Should have the key even if empty
        assert "hr_reliability_warnings" in result
        assert isinstance(result["hr_reliability_warnings"], list)
