"""Unit tests for server module helpers."""

from __future__ import annotations

import pytest

from withings_mcp.server import _date_to_timestamp, _timestamp_to_date


class TestDateToTimestamp:
    def test_start_of_day(self):
        ts = _date_to_timestamp("2026-01-15")
        # 2026-01-15 00:00:00 UTC
        assert ts == 1768435200

    def test_end_of_day(self):
        ts = _date_to_timestamp("2026-01-15", end_of_day=True)
        # 2026-01-15 23:59:59 UTC
        assert ts == 1768521599

    def test_invalid_date_raises(self):
        with pytest.raises(ValueError):
            _date_to_timestamp("not-a-date")


class TestTimestampToDate:
    def test_converts_correctly(self):
        assert _timestamp_to_date(1768435200) == "2026-01-15"


class TestMainSignature:
    def test_main_is_callable(self):
        from withings_mcp.server import main

        assert callable(main)
