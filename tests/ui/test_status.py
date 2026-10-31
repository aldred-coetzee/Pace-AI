"""Regression tests for the rule-based status assessments."""

from __future__ import annotations

from ui.status import assess_recent_runs, assess_training_load


def _week(key: str, miles: float) -> dict:
    return {"week": key, "week_start": "", "distance_miles": miles, "activity_count": 3}


def test_training_load_uses_latest_week_when_given_oldest_first() -> None:
    # HistoryDB returns weeks oldest-first. Four steady weeks then a spike:
    # ACWR = 30 / 15 = 2.0, which must read as a concern, not as OK.
    weeks = [_week(f"2026-W{n:02d}", 15) for n in range(38, 42)] + [_week("2026-W42", 30)]
    status, html = assess_training_load(weeks)
    assert status == "concern"
    assert "2.00" in html


def test_training_load_is_order_independent() -> None:
    weeks = [_week(f"2026-W{n:02d}", 15) for n in range(38, 42)] + [_week("2026-W42", 30)]
    assert assess_training_load(weeks) == assess_training_load(list(reversed(weeks)))


def test_recent_runs_accepts_formatted_pace() -> None:
    # get_recent_activities formats pace as "m:ss"; int() on it used to crash /status.
    run = {
        "date": "2026-10-30",
        "sport_type": "Run",
        "name": "Easy",
        "distance_miles": 4.0,
        "pace_min_per_mile": "9:30",
    }
    _status, html = assess_recent_runs([run], [])
    assert "9:30/mi" in html
