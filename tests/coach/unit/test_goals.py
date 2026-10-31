"""Unit tests for goal management tools."""

from __future__ import annotations

import pytest

from pace_ai.tools.goals import delete_goal, format_time, get_goals, parse_time, set_goal, update_goal


class TestParseTime:
    def test_hms(self):
        assert parse_time("1:30:00") == 5400

    def test_ms(self):
        assert parse_time("22:00") == 1320

    def test_single_digit_seconds(self):
        assert parse_time("4:05") == 245

    def test_invalid_format(self):
        with pytest.raises(ValueError, match="Invalid time format"):
            parse_time("bad")

    def test_leading_whitespace(self):
        assert parse_time("  22:00  ") == 1320


class TestFormatTime:
    def test_with_hours(self):
        assert format_time(5400) == "1:30:00"

    def test_without_hours(self):
        assert format_time(1320) == "22:00"

    def test_zero(self):
        assert format_time(0) == "0:00"

    def test_single_digit_seconds(self):
        assert format_time(245) == "4:05"

    def test_roundtrip_hms(self):
        assert format_time(parse_time("1:45:30")) == "1:45:30"

    def test_roundtrip_ms(self):
        assert format_time(parse_time("5:00")) == "5:00"


class TestSetGoal:
    def test_creates_goal(self, goal_db):
        result = set_goal(goal_db, "5k", "22:00", race_date="2025-03-01", notes="Park Run PB")
        assert result["race_type"] == "5k"
        assert result["target_time_seconds"] == 1320
        assert result["target_time_formatted"] == "22:00"
        assert result["race_date"] == "2025-03-01"
        assert result["id"] is not None

    def test_creates_goal_without_optional_fields(self, goal_db):
        result = set_goal(goal_db, "marathon", "3:30:00")
        assert result["race_type"] == "marathon"
        assert result["race_date"] is None
        assert result["notes"] is None

    def test_invalid_time_raises(self, goal_db):
        with pytest.raises(ValueError):
            set_goal(goal_db, "5k", "bad_time")


class TestGetGoals:
    def test_empty(self, goal_db):
        assert get_goals(goal_db) == []

    def test_returns_all_goals(self, goal_db):
        set_goal(goal_db, "5k", "22:00")
        set_goal(goal_db, "10k", "45:00")
        goals = get_goals(goal_db)
        assert len(goals) == 2
        assert all("target_time_formatted" in g for g in goals)

    def test_ordered_by_newest_first(self, goal_db):
        set_goal(goal_db, "5k", "22:00")
        set_goal(goal_db, "10k", "45:00")
        goals = get_goals(goal_db)
        assert goals[0]["race_type"] == "10k"


class TestUpdateGoal:
    def test_update_race_type(self, goal_db):
        goal = set_goal(goal_db, "5k", "22:00")
        updated = update_goal(goal_db, goal["id"], race_type="10k")
        assert updated["race_type"] == "10k"
        assert updated["target_time_seconds"] == 1320  # unchanged

    def test_update_target_time(self, goal_db):
        goal = set_goal(goal_db, "5k", "22:00")
        updated = update_goal(goal_db, goal["id"], target_time="21:30")
        assert updated["target_time_seconds"] == 1290

    def test_update_nonexistent(self, goal_db):
        assert update_goal(goal_db, 999) is None

    def test_update_no_fields(self, goal_db):
        goal = set_goal(goal_db, "5k", "22:00")
        result = update_goal(goal_db, goal["id"])
        assert result["target_time_seconds"] == 1320


class TestDeleteGoal:
    def test_delete_existing(self, goal_db):
        goal = set_goal(goal_db, "5k", "22:00")
        result = delete_goal(goal_db, goal["id"])
        assert "deleted" in result
        assert get_goals(goal_db) == []

    def test_delete_nonexistent(self, goal_db):
        result = delete_goal(goal_db, 999)
        assert "not found" in result
