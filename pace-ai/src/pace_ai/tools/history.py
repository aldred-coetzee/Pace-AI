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
    weeks_data = db.get_weekly_distances(weeks=weeks, sport_type=sport_type)
    for w in weeks_data:
        km = w.get("distance_km") or 0
        w["distance_miles"] = round(km / 1.60934, 2) if km else None
    return weeks_data


def get_recent_activities(
    db: HistoryDB,
    days: int = 28,
    sport_type: str | None = None,
) -> list[dict[str, Any]]:
    """Return activities from the local store with computed mile/pace fields.

    Much faster than a live API call to strava-mcp.

    Args:
        db: HistoryDB instance.
        days: Number of days to look back (default 28).
        sport_type: Optional sport type filter (e.g. "run", "ride").

    Returns:
        List of activity dicts, most recent first.
    """
    activities = db.get_activities(days=days, sport_type=sport_type)
    for a in activities:
        dist_m = a.get("distance_m") or 0
        speed = a.get("average_speed_ms") or 0
        a["distance_miles"] = round(dist_m / 1609.34, 2) if dist_m else None
        a["distance_km"] = round(dist_m / 1000, 2) if dist_m else None
        if speed > 0:
            pace_s_km = 1000 / speed
            pace_s_mi = 1609.34 / speed
            a["pace_min_per_km"] = f"{int(pace_s_km // 60)}:{int(pace_s_km % 60):02d}"
            a["pace_min_per_mile"] = f"{int(pace_s_mi // 60)}:{int(pace_s_mi % 60):02d}"
        else:
            a["pace_min_per_km"] = None
            a["pace_min_per_mile"] = None
    return activities


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
