"""Unit tests for methodology resources."""

from __future__ import annotations

from pace_ai.resources.methodology import METHODOLOGY, ZONES_EXPLAINED


class TestMethodology:
    def test_not_empty(self):
        assert len(METHODOLOGY) > 1000

    def test_contains_core_principles(self):
        assert "Progressive Overload" in METHODOLOGY
        assert "Specificity" in METHODOLOGY
        assert "Recovery" in METHODOLOGY
        assert "Individualisation" in METHODOLOGY

    def test_contains_zone_table(self):
        assert "Easy (E)" in METHODOLOGY
        assert "Threshold (T)" in METHODOLOGY
        assert "Interval (I)" in METHODOLOGY
        assert "Repetition (R)" in METHODOLOGY

    def test_contains_race_prediction(self):
        assert "VDOT" in METHODOLOGY
        assert "Riegel" in METHODOLOGY

    def test_contains_periodisation(self):
        assert "Base phase" in METHODOLOGY
        assert "Taper" in METHODOLOGY

    def test_contains_red_flags(self):
        assert "10%" in METHODOLOGY
        assert "ACWR" in METHODOLOGY


class TestZonesExplained:
    def test_not_empty(self):
        assert len(ZONES_EXPLAINED) > 500

    def test_all_zones_covered(self):
        assert "Zone 1: Easy" in ZONES_EXPLAINED
        assert "Zone 2: Marathon" in ZONES_EXPLAINED
        assert "Zone 3: Threshold" in ZONES_EXPLAINED
        assert "Zone 4: Interval" in ZONES_EXPLAINED
        assert "Zone 5: Repetition" in ZONES_EXPLAINED

    def test_contains_session_examples(self):
        assert "Recovery runs" in ZONES_EXPLAINED or "recovery" in ZONES_EXPLAINED.lower()
        assert "Tempo" in ZONES_EXPLAINED or "tempo" in ZONES_EXPLAINED.lower()
