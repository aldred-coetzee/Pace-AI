"""Goal management tools — CRUD operations for training goals."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pace_ai.database import GoalDB


def format_time(seconds: int) -> str:
    """Format seconds as H:MM:SS or M:SS."""
    h, remainder = divmod(seconds, 3600)
    m, s = divmod(remainder, 60)
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def parse_time(time_str: str) -> int:
    """Parse H:MM:SS or M:SS or MM:SS to seconds."""
    parts = time_str.strip().split(":")
    if len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    if len(parts) == 2:
        return int(parts[0]) * 60 + int(parts[1])
    msg = f"Invalid time format: {time_str!r}. Use H:MM:SS or M:SS."
    raise ValueError(msg)


def set_goal(
    db: GoalDB,
    race_type: str,
    target_time: str,
    race_date: str | None = None,
    notes: str | None = None,
) -> dict:
    """Create a new training goal.

    Args:
        db: Goal database instance.
        race_type: Race distance/type (e.g. "5k", "10k", "half marathon", "marathon").
        target_time: Target finish time (H:MM:SS or M:SS format).
        race_date: Optional race date (YYYY-MM-DD).
        notes: Optional notes about the goal.

    Returns:
        The created goal with formatted time.
    """
    target_seconds = parse_time(target_time)
    goal = db.create(race_type, target_seconds, race_date, notes)
    goal["target_time_formatted"] = format_time(goal["target_time_seconds"])
    return goal


def get_goals(db: GoalDB) -> list[dict]:
    """List all training goals."""
    goals = db.list_all()
    for g in goals:
        g["target_time_formatted"] = format_time(g["target_time_seconds"])
    return goals


def update_goal(
    db: GoalDB,
    goal_id: int,
    race_type: str | None = None,
    target_time: str | None = None,
    race_date: str | None = None,
    notes: str | None = None,
) -> dict | None:
    """Update an existing goal.

    Returns:
        Updated goal, or None if goal not found.
    """
    fields: dict = {}
    if race_type is not None:
        fields["race_type"] = race_type
    if target_time is not None:
        fields["target_time_seconds"] = parse_time(target_time)
    if race_date is not None:
        fields["race_date"] = race_date
    if notes is not None:
        fields["notes"] = notes

    goal = db.update(goal_id, **fields)
    if goal is not None:
        goal["target_time_formatted"] = format_time(goal["target_time_seconds"])
    return goal


def delete_goal(db: GoalDB, goal_id: int) -> str:
    """Delete a goal by ID. Returns confirmation message."""
    if db.delete(goal_id):
        return f"Goal {goal_id} deleted."
    return f"Goal {goal_id} not found."
