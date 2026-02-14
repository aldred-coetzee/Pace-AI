"""Unit tests for GoalDB database layer."""

from __future__ import annotations

from pace_ai.database import GoalDB


class TestGoalDB:
    def test_create_and_get(self, goal_db):
        goal = goal_db.create("5k", 1320, race_date="2025-03-01", notes="Park Run")
        assert goal["id"] is not None
        assert goal["race_type"] == "5k"
        assert goal["target_time_seconds"] == 1320
        assert goal["race_date"] == "2025-03-01"

        fetched = goal_db.get(goal["id"])
        assert fetched == goal

    def test_get_nonexistent(self, goal_db):
        assert goal_db.get(999) is None

    def test_list_all_empty(self, goal_db):
        assert goal_db.list_all() == []

    def test_list_all_multiple(self, goal_db):
        goal_db.create("5k", 1320)
        goal_db.create("10k", 2700)
        goals = goal_db.list_all()
        assert len(goals) == 2

    def test_update_single_field(self, goal_db):
        goal = goal_db.create("5k", 1320)
        updated = goal_db.update(goal["id"], race_type="10k")
        assert updated["race_type"] == "10k"
        assert updated["target_time_seconds"] == 1320  # unchanged

    def test_update_multiple_fields(self, goal_db):
        goal = goal_db.create("5k", 1320)
        updated = goal_db.update(goal["id"], race_type="10k", target_time_seconds=2700)
        assert updated["race_type"] == "10k"
        assert updated["target_time_seconds"] == 2700

    def test_update_nonexistent(self, goal_db):
        assert goal_db.update(999, race_type="10k") is None

    def test_update_ignores_unknown_fields(self, goal_db):
        goal = goal_db.create("5k", 1320)
        updated = goal_db.update(goal["id"], unknown_field="value")
        assert updated["race_type"] == "5k"  # unchanged

    def test_delete_existing(self, goal_db):
        goal = goal_db.create("5k", 1320)
        assert goal_db.delete(goal["id"]) is True
        assert goal_db.get(goal["id"]) is None

    def test_delete_nonexistent(self, goal_db):
        assert goal_db.delete(999) is False

    def test_timestamps_set(self, goal_db):
        goal = goal_db.create("5k", 1320)
        assert goal["created_at"] > 0
        assert goal["updated_at"] > 0

    def test_update_changes_updated_at(self, goal_db):
        goal = goal_db.create("5k", 1320)
        original_updated = goal["updated_at"]
        import time
        time.sleep(0.01)
        updated = goal_db.update(goal["id"], notes="new notes")
        assert updated["updated_at"] >= original_updated
