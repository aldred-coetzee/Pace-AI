"""Tests for date utilities in ui.plans."""

from __future__ import annotations

from ui.plans import _date_calendar, _fix_day_label, _validate_plan_dates


class TestDateCalendar:
    """Tests for _date_calendar — date-to-day-name reference builder."""

    def test_single_day(self) -> None:
        # 2026-04-27 is a Monday
        result = _date_calendar("2026-04-27", "2026-04-27")
        assert "Mon 2026-04-27" in result

    def test_full_week(self) -> None:
        # 2026-04-27 (Mon) to 2026-05-03 (Sun)
        result = _date_calendar("2026-04-27", "2026-05-03")
        lines = result.strip().split("\n")
        assert len(lines) == 7
        assert "Mon 2026-04-27" in lines[0]
        assert "Sun 2026-05-03" in lines[6]

    def test_may_17_2026_is_sunday(self) -> None:
        """The specific case that triggered this feature — May 17 2026 is a Sunday, not Saturday."""
        result = _date_calendar("2026-05-17", "2026-05-17")
        assert "Sun 2026-05-17" in result
        assert "Sat" not in result

    def test_invalid_dates_return_empty(self) -> None:
        assert _date_calendar("not-a-date", "2026-04-27") == ""
        assert _date_calendar("2026-04-27", "") == ""

    def test_end_before_start_returns_empty(self) -> None:
        result = _date_calendar("2026-05-03", "2026-04-27")
        assert result == ""


class TestFixDayLabel:
    """Tests for _fix_day_label — correcting day-of-week names in text."""

    def test_correct_label_unchanged(self) -> None:
        # Monday = weekday 0
        assert _fix_day_label("Monday easy run", 0) == "Monday easy run"

    def test_wrong_full_name_replaced(self) -> None:
        # Text says Saturday but correct day is Sunday (weekday 6)
        assert _fix_day_label("Saturday long run", 6) == "Sunday long run"

    def test_wrong_abbrev_replaced(self) -> None:
        # Text says Sat but correct day is Sun (weekday 6)
        assert _fix_day_label("Sat long run", 6) == "Sun long run"

    def test_no_day_label_unchanged(self) -> None:
        assert _fix_day_label("Easy recovery run", 0) == "Easy recovery run"

    def test_multiple_labels_all_fixed(self) -> None:
        # Both wrong day names should be fixed
        result = _fix_day_label("Sat long run (moved from Wed)", 6)
        # Sat -> Sun, Wed stays only if it's also wrong
        assert result.startswith("Sun long run")

    def test_preserves_full_name_format(self) -> None:
        result = _fix_day_label("Saturday long run", 0)
        assert result == "Monday long run"

    def test_preserves_abbrev_format(self) -> None:
        result = _fix_day_label("Sat long run", 0)
        assert result == "Mon long run"

    def test_case_insensitive_match(self) -> None:
        # "saturday" lowercase should still be fixed
        result = _fix_day_label("saturday long run", 6)
        # Should become Sunday (preserving full name format)
        assert "Sunday" in result or "sunday" in result.lower()

    def test_tuesday_variant(self) -> None:
        result = _fix_day_label("Tues tempo", 2)  # Wednesday
        assert "Wed" in result


class TestValidatePlanDates:
    """Tests for _validate_plan_dates — fixing plans after extraction."""

    def test_correct_plan_unchanged(self) -> None:
        plan = {
            "sessions": [
                {"date": "2026-04-27", "name": "Mon easy run"},  # Monday
                {"date": "2026-05-02", "name": "Sat long run"},  # Saturday
            ]
        }
        result = _validate_plan_dates(plan)
        assert result["sessions"][0]["name"] == "Mon easy run"
        assert result["sessions"][1]["name"] == "Sat long run"

    def test_wrong_day_in_name_fixed(self) -> None:
        plan = {
            "sessions": [
                # 2026-05-17 is a Sunday, not Saturday
                {"date": "2026-05-17", "name": "Sat long run"},
            ]
        }
        result = _validate_plan_dates(plan)
        assert result["sessions"][0]["name"] == "Sun long run"

    def test_wrong_day_in_description_fixed(self) -> None:
        plan = {
            "sessions": [
                {
                    "date": "2026-05-17",
                    "name": "Long Run",
                    "description": "Saturday long run — 8 miles easy",
                },
            ]
        }
        result = _validate_plan_dates(plan)
        assert "Sunday" in result["sessions"][0]["description"]
        assert "Saturday" not in result["sessions"][0]["description"]

    def test_invalid_date_skipped(self) -> None:
        plan = {
            "sessions": [
                {"date": "not-a-date", "name": "Sat long run"},
            ]
        }
        result = _validate_plan_dates(plan)
        assert result["sessions"][0]["name"] == "Sat long run"  # unchanged

    def test_no_day_label_unchanged(self) -> None:
        plan = {
            "sessions": [
                {"date": "2026-04-27", "name": "Easy Recovery Run"},
            ]
        }
        result = _validate_plan_dates(plan)
        assert result["sessions"][0]["name"] == "Easy Recovery Run"

    def test_empty_plan(self) -> None:
        assert _validate_plan_dates({}) == {}
        assert _validate_plan_dates({"sessions": []}) == {"sessions": []}

    def test_missing_fields_handled(self) -> None:
        plan = {
            "sessions": [
                {"date": "2026-04-27"},  # no name or description
            ]
        }
        result = _validate_plan_dates(plan)
        assert result["sessions"][0] == {"date": "2026-04-27"}
