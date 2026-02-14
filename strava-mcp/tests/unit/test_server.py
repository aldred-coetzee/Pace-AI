"""Unit tests for server helpers."""

from __future__ import annotations

from strava_mcp.server import _speed_to_pace


class TestSpeedToPace:
    def test_normal_pace(self):
        # 3.33 m/s ≈ 5:00/km
        result = _speed_to_pace(3.33)
        assert result == "5:00"

    def test_fast_pace(self):
        # 5.0 m/s ≈ 3:20/km
        result = _speed_to_pace(5.0)
        assert result == "3:20"

    def test_slow_pace(self):
        # 2.0 m/s ≈ 8:20/km
        result = _speed_to_pace(2.0)
        assert result == "8:20"

    def test_zero_speed(self):
        assert _speed_to_pace(0) is None

    def test_negative_speed(self):
        assert _speed_to_pace(-1) is None
