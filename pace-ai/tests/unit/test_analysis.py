"""Unit tests for training analysis tools."""

from __future__ import annotations

import pytest

from pace_ai.tools.analysis import calculate_acwr, calculate_training_zones, predict_race_time

# ── ACWR Tests (Uncoupled Method) ────────────────────────────────────


class TestCalculateACWR:
    def test_optimal_range(self):
        result = calculate_acwr([30, 35, 32, 35, 34])
        assert 0.8 <= result["acwr"] <= 1.3
        assert result["risk_level"] == "optimal"

    def test_undertraining(self):
        result = calculate_acwr([40, 40, 40, 40, 20])
        assert result["acwr"] == 0.5
        assert result["risk_level"] == "undertraining"

    def test_elevated_risk(self):
        result = calculate_acwr([25, 25, 25, 25, 35])
        assert result["acwr"] == 1.4
        assert result["risk_level"] == "elevated"

    def test_high_risk(self):
        result = calculate_acwr([20, 20, 20, 20, 40])
        assert result["acwr"] == 2.0
        assert result["risk_level"] == "high"

    def test_zero_chronic(self):
        result = calculate_acwr([0, 0, 0, 0, 0])
        assert result["risk_level"] == "insufficient_data"

    def test_too_few_weeks_raises(self):
        with pytest.raises(ValueError, match="at least 5 weeks"):
            calculate_acwr([30, 35, 32, 34])

    def test_four_weeks_raises(self):
        """4 weeks was the old minimum — now we need 5 for uncoupled method."""
        with pytest.raises(ValueError, match="at least 5 weeks"):
            calculate_acwr([30, 35, 32, 35])

    def test_uncoupled_chronic_excludes_acute(self):
        """Verify the chronic load does NOT include the acute week (uncoupled method)."""
        # If coupled: chronic = mean([30, 30, 30, 60]) = 37.5
        # If uncoupled: chronic = mean([30, 30, 30, 30]) = 30.0
        result = calculate_acwr([30, 30, 30, 30, 60])
        assert result["chronic_load"] == 30.0
        assert result["acute_load"] == 60
        assert result["acwr"] == 2.0

    def test_load_variability_cv_identical_weeks(self):
        result = calculate_acwr([30, 30, 30, 30, 30])
        assert "load_variability_cv" in result
        assert result["load_variability_cv"] == 0  # identical weeks → zero variability

    def test_load_variability_cv_varied_weeks(self):
        # chronic weeks: [20, 30, 40, 50], mean=35, std=sqrt(125)≈11.18, cv=0.32
        result = calculate_acwr([20, 30, 40, 50, 35])
        assert result["load_variability_cv"] == pytest.approx(0.32, abs=0.01)

    def test_week_over_week_change(self):
        result = calculate_acwr([30, 35, 32, 32, 40])
        assert result["week_over_week_change_pct"] == pytest.approx(25.0, abs=0.1)

    def test_more_than_5_weeks_uses_last_5(self):
        # 6 weeks: [100, 30, 35, 32, 35, 34]
        # chronic = mean([30, 35, 32, 35]) = 33.0, acute = 34
        result = calculate_acwr([100, 30, 35, 32, 35, 34])
        assert result["chronic_load"] == pytest.approx(33.0, abs=0.1)


# ── VDOT Golden Value Tests ──────────────────────────────────────────


class TestPredictRaceTime:
    def test_vdot_20min_5k_golden(self):
        """20:00 5K ≈ VDOT 49.8 (published Daniels table: VDOT 50 for ~20:00)."""
        result = predict_race_time("5k", "20:00", "10k")
        assert result["vdot"] == pytest.approx(49.8, abs=0.5)

    def test_vdot_25min_5k(self):
        """25:00 5K ≈ VDOT 38.3 per Daniels formula."""
        result = predict_race_time("5k", "25:00", "10k")
        assert result["vdot"] == pytest.approx(38.3, abs=0.5)

    def test_vdot_17_10_5k(self):
        """17:10 5K ≈ VDOT 59.5 (published: VDOT 60 for ~17:10)."""
        result = predict_race_time("5k", "17:10", "10k")
        assert result["vdot"] == pytest.approx(59.5, abs=0.5)

    def test_vdot_30min_5k(self):
        """30:00 5K ≈ VDOT 30.8."""
        result = predict_race_time("5k", "30:00", "10k")
        assert result["vdot"] == pytest.approx(30.8, abs=0.5)

    def test_vdot_40min_10k(self):
        """40:00 10K ≈ VDOT 51.9."""
        result = predict_race_time("10k", "40:00", "5k")
        assert result["vdot"] == pytest.approx(51.9, abs=0.5)

    def test_vdot_90min_half(self):
        """1:30:00 half marathon ≈ VDOT 51.0."""
        result = predict_race_time("half marathon", "1:30:00", "marathon")
        assert result["vdot"] == pytest.approx(51.0, abs=0.5)

    def test_10k_prediction_from_20min_5k(self):
        """20:00 5K → 10K ≈ 41:28 (2488s) via VDOT."""
        result = predict_race_time("5k", "20:00", "10k")
        assert result["predicted_seconds"] == pytest.approx(2488, abs=30)

    def test_half_prediction_from_20min_5k(self):
        """20:00 5K → half marathon ≈ 1:31:50 (5510s) via VDOT."""
        result = predict_race_time("5k", "20:00", "half marathon")
        assert result["predicted_seconds"] == pytest.approx(5510, abs=30)

    def test_marathon_prediction_from_20min_5k(self):
        """20:00 5K → marathon ≈ 3:11:18 (11478s) via VDOT."""
        result = predict_race_time("5k", "20:00", "marathon")
        assert result["predicted_seconds"] == pytest.approx(11478, abs=60)

    # ── Riegel Reference Values ──────────────────────────────────────

    def test_riegel_5k_to_10k(self):
        """Riegel: 20:00 5K → 10K = 41:42 (2502s). Exponent = 1.06."""
        result = predict_race_time("5k", "20:00", "10k")
        assert result["riegel_predicted_seconds"] == 2502

    def test_riegel_5k_to_half(self):
        """Riegel: 20:00 5K → half marathon = 1:32:00 (5520s)."""
        result = predict_race_time("5k", "20:00", "half marathon")
        assert result["riegel_predicted_seconds"] == 5520

    def test_riegel_5k_to_marathon(self):
        """Riegel: 20:00 5K → marathon = 3:11:49 (11509s)."""
        result = predict_race_time("5k", "20:00", "marathon")
        assert result["riegel_predicted_seconds"] == 11509

    def test_riegel_always_slower_than_vdot_for_marathon(self):
        """Riegel is known to be more optimistic for longer distances from short races.
        With our VDOT 49.8 (not 50.0), the VDOT prediction is slightly slower."""
        result = predict_race_time("5k", "20:00", "marathon")
        # Both predictions should be within ~2% of each other
        assert abs(result["predicted_seconds"] - result["riegel_predicted_seconds"]) < 300

    # ── Existing Tests (tightened) ───────────────────────────────────

    def test_5k_to_half(self):
        result = predict_race_time("5k", "22:00", "half marathon")
        # VDOT ~44.3, half ~1:42-ish
        assert 5900 < result["predicted_seconds"] < 6200

    def test_10k_to_5k(self):
        result = predict_race_time("10k", "45:00", "5k")
        assert result["predicted_seconds"] < 2700

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


# ── Training Zones Tests ─────────────────────────────────────────────


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
        result = calculate_training_zones(threshold_pace_per_km="5:00")
        zones = result["zones"]
        rep_fast = zones["repetition"]["pace_seconds_per_km"][0]
        easy_slow = zones["easy"]["pace_seconds_per_km"][1]
        assert rep_fast < easy_slow

    # ── VDOT-based Zone Tests ────────────────────────────────────────

    def test_from_vdot(self):
        """VDOT 50 should produce valid pace zones for all five Daniels zones."""
        result = calculate_training_zones(vdot=50)
        zones = result["zones"]
        assert len(zones) == 5
        for zone_name in ["easy", "marathon", "threshold", "interval", "repetition"]:
            assert zone_name in zones
            assert "pace_range_per_km" in zones[zone_name]
            assert "pace_seconds_per_km" in zones[zone_name]

    def test_vdot50_threshold_pace(self):
        """VDOT 50 threshold pace should be ~4:15/km (255s) per published Daniels tables."""
        result = calculate_training_zones(vdot=50)
        t_fast, t_slow = result["zones"]["threshold"]["pace_seconds_per_km"]
        assert t_fast == 255  # 4:15 — fast end of threshold
        assert t_slow == 267  # 4:27 — slow end of threshold

    def test_vdot50_easy_pace(self):
        """VDOT 50 easy pace range: ~4:53 - 5:51 per Daniels %VO2max curves."""
        result = calculate_training_zones(vdot=50)
        e_fast, e_slow = result["zones"]["easy"]["pace_seconds_per_km"]
        assert e_fast == 293  # 4:53
        assert e_slow == 351  # 5:51

    def test_vdot50_zone_ordering(self):
        """Zones should be ordered: repetition (fastest) < interval < threshold < marathon < easy (slowest)."""
        result = calculate_training_zones(vdot=50)
        z = result["zones"]
        assert z["repetition"]["pace_seconds_per_km"][0] < z["interval"]["pace_seconds_per_km"][0]
        assert z["interval"]["pace_seconds_per_km"][0] < z["threshold"]["pace_seconds_per_km"][0]
        assert z["threshold"]["pace_seconds_per_km"][0] < z["marathon"]["pace_seconds_per_km"][0]
        assert z["marathon"]["pace_seconds_per_km"][0] < z["easy"]["pace_seconds_per_km"][0]

    def test_vdot_with_hr(self):
        """VDOT + HR should produce both pace and HR ranges."""
        result = calculate_training_zones(vdot=50, threshold_hr=175)
        zones = result["zones"]
        assert "pace_range_per_km" in zones["easy"]
        assert "hr_range_bpm" in zones["easy"]

    def test_vdot_takes_precedence_over_pace(self):
        """When both vdot and threshold_pace_per_km are provided, vdot is used for paces."""
        result = calculate_training_zones(vdot=50, threshold_pace_per_km="6:00")
        # If VDOT were ignored and 6:00 used, threshold fast end would be ~5:49
        # With VDOT 50, threshold fast end is 4:15 (255s)
        assert result["zones"]["threshold"]["pace_seconds_per_km"][0] == 255

    def test_reference_includes_vdot(self):
        result = calculate_training_zones(vdot=50)
        assert result["reference"]["vdot"] == 50
