"""History query tools — read from the central history store."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pace_ai.database import HistoryDB


def get_weekly_distances(
    db: HistoryDB,
    weeks: int = 12,
    sport_type: str = "run",
) -> list[dict[str, Any]]:
    """Return weekly distance totals from the local activities table.

    Can be used directly by ACWR calculation, replacing the need for Claude
    to pass weekly arrays from strava-mcp.

    Args:
        db: HistoryDB instance.
        weeks: Number of weeks to look back (default 12).
        sport_type: Sport type filter (default "run").

    Returns:
        List of dicts with week, week_start, distance_km, activity_count.
    """
    return db.get_weekly_distances(weeks=weeks, sport_type=sport_type)


def get_recent_activities(
    db: HistoryDB,
    days: int = 28,
    sport_type: str | None = None,
) -> list[dict[str, Any]]:
    """Return activities from the local store.

    Much faster than a live API call to strava-mcp.

    Args:
        db: HistoryDB instance.
        days: Number of days to look back (default 28).
        sport_type: Optional sport type filter (e.g. "run", "ride").

    Returns:
        List of activity dicts, most recent first.
    """
    return db.get_activities(days=days, sport_type=sport_type)


def get_recent_wellness(db: HistoryDB, days: int = 14) -> list[dict[str, Any]]:
    """Return wellness snapshots from the local store.

    Args:
        db: HistoryDB instance.
        days: Number of days to look back (default 14).

    Returns:
        List of wellness snapshot dicts, most recent first.
    """
    return db.get_wellness(days=days)


def get_recent_diary(db: HistoryDB, days: int = 28) -> list[dict[str, Any]]:
    """Return diary entries from the local store.

    Args:
        db: HistoryDB instance.
        days: Number of days to look back (default 28).

    Returns:
        List of diary entry dicts, most recent first.
    """
    return db.get_diary_entries(days=days)


def get_race_history(db: HistoryDB, limit: int = 10) -> list[dict[str, Any]]:
    """Return race results ordered by date desc.

    Args:
        db: HistoryDB instance.
        limit: Max number of results (default 10).

    Returns:
        List of race result dicts.
    """
    return db.get_race_results(limit=limit)


def get_pbs(db: HistoryDB) -> list[dict[str, Any]]:
    """Return personal bests — fastest time per distance label.

    Args:
        db: HistoryDB instance.

    Returns:
        List of PB dicts with distance_label, best_time_s, date, event_name, vdot.
    """
    return db.get_pbs()
