"""Unit tests for environment adjustment tools."""

from __future__ import annotations

import pytest

from pace_ai.tools.environment import calculate_altitude_adjustment, calculate_heat_adjustment


class TestCalculateHeatAdjustment:
    def test_cool_weather_no_adjustment(self):
        result = calculate_heat_adjustment(temperature_f=50)
        assert result["slowdown_pct"] == 0.0
        assert result["risk_level"] == "minimal"

    def test_warm_weather_moderate(self):
        result = calculate_heat_adjustment(temperature_f=80, dew_point_f=60)
        # combined = 140, expect 1-3% slowdown
        assert 1.0 <= result["slowdown_pct"] <= 3.0
        assert result["risk_level"] in ("moderate", "high")

    def test_hot_and_humid(self):
        result = calculate_heat_adjustment(temperature_f=90, dew_point_f=75)
        # combined = 165, expect 6%+ slowdown
        assert result["slowdown_pct"] >= 6.0
        assert result["risk_level"] == "extreme"

    def test_celsius_input(self):
        result = calculate_heat_adjustment(temperature_c=30, dew_point_c=20)
        assert result["temperature_f"] > 80
        assert result["slowdown_pct"] > 0

    def test_no_dew_point_defaults(self):
        result = calculate_heat_adjustment(temperature_f=85)
        # Should use temp - 20 as dew point estimate
        assert result["dew_point_f"] == 65

    def test_no_temperature_raises(self):
        with pytest.raises(ValueError, match="Provide temperature"):
            calculate_heat_adjustment()

    def test_adjustment_factor(self):
        result = calculate_heat_adjustment(temperature_f=80, dew_point_f=65)
        assert result["adjustment_factor"] > 1.0
        assert result["adjustment_factor"] == pytest.approx(1 + result["slowdown_pct"] / 100, abs=0.01)

    def test_fahrenheit_takes_precedence(self):
        result = calculate_heat_adjustment(temperature_f=70, temperature_c=40)
        # Should use F value (70) not C value (40C = 104F)
        assert result["temperature_f"] == 70


class TestCalculateAltitudeAdjustment:
    def test_sea_level_no_adjustment(self):
        result = calculate_altitude_adjustment(altitude_ft=0)
        assert result["slowdown_pct"] == 0.0
        assert result["adjustment_factor"] == 1.0
        assert result["acclimatization_days"] == 0

    def test_below_3000ft_no_adjustment(self):
        result = calculate_altitude_adjustment(altitude_ft=2500)
        assert result["slowdown_pct"] == 0.0

    def test_moderate_altitude(self):
        result = calculate_altitude_adjustment(altitude_ft=5000)
        # 2000 ft above 3000 = ~4% slowdown
        assert result["slowdown_pct"] == pytest.approx(4.0, abs=0.5)

    def test_high_altitude(self):
        result = calculate_altitude_adjustment(altitude_ft=8000)
        # 5000 ft above 3000 = ~10% slowdown
        assert result["slowdown_pct"] == pytest.approx(10.0, abs=0.5)
        assert result["vo2max_reduction_pct"] > 0

    def test_meters_input(self):
        result = calculate_altitude_adjustment(altitude_m=2000)
        # ~6560 ft
        assert result["altitude_ft"] > 6000
        assert result["slowdown_pct"] > 0

    def test_no_input_raises(self):
        with pytest.raises(ValueError, match="Provide altitude"):
            calculate_altitude_adjustment()

    def test_acclimatization_increases_with_altitude(self):
        low = calculate_altitude_adjustment(altitude_ft=4000)
        high = calculate_altitude_adjustment(altitude_ft=9000)
        assert high["acclimatization_days"] > low["acclimatization_days"]
