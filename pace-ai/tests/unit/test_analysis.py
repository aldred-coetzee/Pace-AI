"""Unit tests for training analysis tools."""

from __future__ import annotations

import pytest

from pace_ai.tools.analysis import calculate_acwr, calculate_training_zones, predict_race_time


class TestCalculateACWR:
    def test_optimal_range(self):
        result = calculate_acwr([30, 35, 32, 35])
        assert 0.8 <= result["acwr"] <= 1.3
        assert result["risk_level"] == "optimal"

    def test_undertraining(self):
        result = calculate_acwr([40, 40, 40, 20])
        assert result["acwr"] < 0.8
        assert result["risk_level"] == "undertraining"

    def test_elevated_risk(self):
        result = calculate_acwr([25, 25, 25, 38])
        assert result["risk_level"] == "elevated"

    def test_high_risk(self):
        result = calculate_acwr([20, 20, 20, 40])
        assert result["acwr"] > 1.5
        assert result["risk_level"] == "high"

    def test_zero_chronic(self):
        result = calculate_acwr([0, 0, 0, 0])
        assert result["risk_level"] == "insufficient_data"

    def test_too_few_weeks_raises(self):
        with pytest.raises(ValueError, match="at least 4 weeks"):
            calculate_acwr([30, 35, 32])

    def test_monotony_and_strain(self):
        result = calculate_acwr([30, 30, 30, 30])
        assert "monotony" in result
        assert "strain" in result

    def test_week_over_week_change(self):
        result = calculate_acwr([30, 35, 32, 40])
        assert result["week_over_week_change_pct"] is not None
        assert result["week_over_week_change_pct"] == pytest.approx(25.0, abs=0.1)

    def test_more_than_4_weeks(self):
        # Only last 4 weeks should be used for chronic
        result = calculate_acwr([10, 10, 30, 35, 32, 35])
        assert result["chronic_load"] == pytest.approx(33.0, abs=0.1)


class TestPredictRaceTime:
    def test_5k_to_marathon(self):
        result = predict_race_time("5k", "20:00", "marathon")
        assert result["vdot"] > 0
        assert result["predicted_seconds"] > 0
        assert "predicted_time" in result
        assert "riegel_predicted_time" in result

    def test_5k_to_half(self):
        result = predict_race_time("5k", "22:00", "half marathon")
        # VDOT ~44-45, half ~1:40-1:42
        assert 5800 < result["predicted_seconds"] < 6200

    def test_10k_to_5k(self):
        # Shorter prediction — should be faster
        result = predict_race_time("10k", "45:00", "5k")
        assert result["predicted_seconds"] < 2700  # faster than 45:00

    def test_unknown_source_distance(self):
        with pytest.raises(ValueError, match="Unknown distance"):
            predict_race_time("100m", "10:00", "5k")

    def test_unknown_target_distance(self):
        with pytest.raises(ValueError, match="Unknown distance"):
            predict_race_time("5k", "20:00", "100m")

    def test_equivalent_performances(self):
        result = predict_race_time("5k", "20:00", "10k")
        assert "equivalent_performances" in result
        assert "5k" in result["equivalent_performances"]
        assert "marathon" in result["equivalent_performances"]

    def test_vdot_reasonable_range(self):
        # 20 min 5K is roughly VDOT 48
        result = predict_race_time("5k", "20:00", "10k")
        assert 45 < result["vdot"] < 52


class TestCalculateTrainingZones:
    def test_from_pace(self):
        result = calculate_training_zones(threshold_pace_per_km="4:30")
        zones = result["zones"]
        assert "easy" in zones
        assert "threshold" in zones
        assert "interval" in zones
        assert "repetition" in zones
        # Easy should be slower than threshold
        assert zones["easy"]["pace_seconds_per_km"][1] > zones["threshold"]["pace_seconds_per_km"][1]

    def test_from_hr(self):
        result = calculate_training_zones(threshold_hr=175)
        zones = result["zones"]
        assert "easy" in zones
        assert "hr_range_bpm" in zones["easy"]
        # Easy HR should be lower than threshold HR
        assert zones["easy"]["hr_range_bpm"][1] < zones["threshold"]["hr_range_bpm"][0]

    def test_from_both(self):
        result = calculate_training_zones(threshold_pace_per_km="4:30", threshold_hr=175)
        zones = result["zones"]
        assert "pace_range_per_km" in zones["easy"]
        assert "hr_range_bpm" in zones["easy"]

    def test_no_input_raises(self):
        with pytest.raises(ValueError, match="Provide at least one"):
            calculate_training_zones()

    def test_zone_descriptions(self):
        result = calculate_training_zones(threshold_pace_per_km="4:30")
        assert "description" in result
        assert "easy" in result["description"]

    def test_zone_ordering(self):
        # Repetition should be fastest, easy should be slowest
        result = calculate_training_zones(threshold_pace_per_km="5:00")
        zones = result["zones"]
        rep_fast = zones["repetition"]["pace_seconds_per_km"][0]
        easy_slow = zones["easy"]["pace_seconds_per_km"][1]
        assert rep_fast < easy_slow
