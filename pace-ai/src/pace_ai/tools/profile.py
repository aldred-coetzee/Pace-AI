"""Athlete profile tools — auto-derive and manage athlete profile."""

from __future__ import annotations

import json
import statistics
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pace_ai.database import HistoryDB

# Fields that can only be set manually, not overwritten by auto-derivation
_MANUAL_FIELDS = {
    "date_of_birth",
    "gender",
    "experience_level",
    "injury_history",
    "preferred_long_run_day",
    "available_days_per_week",
    "notes",
}

# Fields computed automatically from history data
_AUTO_FIELDS = {
    "estimated_vdot",
    "vdot_peak",
    "vdot_peak_date",
    "vdot_current",
    "typical_weekly_km",
    "typical_long_run_km",
    "typical_easy_pace_min_per_km",
    "max_weekly_km_ever",
    "current_weekly_km",
    "training_age_years",
    "weight_kg_current",
    "weight_kg_trend",
    "resting_hr_baseline",
    "hrv_baseline",
}


def generate_athlete_profile(db: HistoryDB) -> dict[str, Any]:
    """Compute auto-derived fields from all history tables and upsert the profile.

    Reads from activities, race_results, wellness_snapshots, and body_measurements
    to compute:
    - estimated_vdot: from best race result in last 12 months
    - typical_weekly_km: median weekly total over last 12 weeks (running)
    - typical_long_run_km: median longest run per week over last 12 weeks
    - typical_easy_pace_min_per_km: median pace of bottom 30% effort runs
    - max_weekly_km_ever: max weekly total across all history
    - current_weekly_km: last 4 week average
    - training_age_years: years since first activity
    - weight_kg_current: most recent measurement
    - weight_kg_trend: compare last 4 weeks vs prior 4 weeks
    - resting_hr_baseline: 30-day median from wellness
    - hrv_baseline: 30-day median from wellness

    Returns:
        The complete athlete profile dict.
    """
    fields: dict[str, Any] = {}

    # ── VDOT from best recent race ────────────────────────────────────
    with db._connect() as conn:
        race = conn.execute(
            """SELECT vdot FROM race_results
               WHERE vdot IS NOT NULL AND date >= date('now', '-12 months')
               ORDER BY vdot DESC LIMIT 1
            """,
        ).fetchone()
    fields["estimated_vdot"] = race["vdot"] if race else None

    # ── VDOT peak (all-time best) ─────────────────────────────────────
    with db._connect() as conn:
        peak = conn.execute(
            """SELECT vdot, date, event_name FROM race_results
               WHERE vdot IS NOT NULL
               ORDER BY vdot DESC LIMIT 1
            """,
        ).fetchone()
    fields["vdot_peak"] = peak["vdot"] if peak else None
    fields["vdot_peak_date"] = peak["date"] if peak else None

    # ── VDOT current (most recent race/time-trial in last 3 months) ───
    # Only populated from actual race performances, not training pace estimates.
    # 3-month window ensures stale race data doesn't misrepresent current fitness.
    with db._connect() as conn:
        recent_race = conn.execute(
            """SELECT vdot FROM race_results
               WHERE vdot IS NOT NULL AND date >= date('now', '-3 months')
               ORDER BY date DESC LIMIT 1
            """,
        ).fetchone()
    fields["vdot_current"] = recent_race["vdot"] if recent_race else None

    # ── Weekly distances (running) ────────────────────────────────────
    with db._connect() as conn:
        weeks = conn.execute(
            """SELECT strftime('%Y-W%W', date) AS week,
                      SUM(distance_m) / 1000.0 AS km
               FROM activities
               WHERE LOWER(sport_type) LIKE '%run%'
               GROUP BY week
               ORDER BY week ASC
            """,
        ).fetchall()

    weekly_kms = [w["km"] for w in weeks if w["km"]]
    if weekly_kms:
        fields["max_weekly_km_ever"] = round(max(weekly_kms), 1)
        recent_12 = weekly_kms[-12:] if len(weekly_kms) >= 12 else weekly_kms
        fields["typical_weekly_km"] = round(statistics.median(recent_12), 1)
        recent_4 = weekly_kms[-4:] if len(weekly_kms) >= 4 else weekly_kms
        fields["current_weekly_km"] = round(statistics.mean(recent_4), 1)
    else:
        fields["max_weekly_km_ever"] = None
        fields["typical_weekly_km"] = None
        fields["current_weekly_km"] = None

    # ── Longest run per week (last 12 weeks) ──────────────────────────
    with db._connect() as conn:
        long_runs = conn.execute(
            """SELECT strftime('%Y-W%W', date) AS week,
                      MAX(distance_m) / 1000.0 AS longest_km
               FROM activities
               WHERE LOWER(sport_type) LIKE '%run%'
                 AND date >= date('now', '-84 days')
               GROUP BY week
               ORDER BY week ASC
            """,
        ).fetchall()
    long_run_kms = [r["longest_km"] for r in long_runs if r["longest_km"]]
    fields["typical_long_run_km"] = round(statistics.median(long_run_kms), 1) if long_run_kms else None

    # ── Easy pace (bottom 30% by average speed) ───────────────────────
    with db._connect() as conn:
        paced_runs = conn.execute(
            """SELECT average_speed_ms FROM activities
               WHERE LOWER(sport_type) LIKE '%run%'
                 AND average_speed_ms > 0
                 AND date >= date('now', '-84 days')
               ORDER BY average_speed_ms ASC
            """,
        ).fetchall()
    if paced_runs:
        n_easy = max(1, len(paced_runs) * 30 // 100)
        easy_speeds = [r["average_speed_ms"] for r in paced_runs[:n_easy]]
        median_speed = statistics.median(easy_speeds)
        if median_speed > 0:
            pace_min_per_km = (1000.0 / median_speed) / 60.0
            fields["typical_easy_pace_min_per_km"] = round(pace_min_per_km, 2)
        else:
            fields["typical_easy_pace_min_per_km"] = None
    else:
        fields["typical_easy_pace_min_per_km"] = None

    # ── Training age (from earliest race or activity, whichever is older) ─
    with db._connect() as conn:
        first_activity = conn.execute("SELECT MIN(date) AS d FROM activities").fetchone()
        first_race = conn.execute("SELECT MIN(date) AS d FROM race_results").fetchone()
    candidates = [r["d"] for r in [first_activity, first_race] if r and r["d"]]
    if candidates:
        from datetime import date, datetime

        earliest = min(candidates)
        first_date = datetime.strptime(earliest[:10], "%Y-%m-%d").date()
        delta = date.today() - first_date
        fields["training_age_years"] = round(delta.days / 365.25, 1)
    else:
        fields["training_age_years"] = None

    # ── Weight ────────────────────────────────────────────────────────
    with db._connect() as conn:
        latest_weight = conn.execute(
            "SELECT weight_kg FROM body_measurements WHERE weight_kg IS NOT NULL ORDER BY date DESC LIMIT 1",
        ).fetchone()
    fields["weight_kg_current"] = latest_weight["weight_kg"] if latest_weight else None

    # Weight trend: compare last 4 weeks vs prior 4 weeks
    with db._connect() as conn:
        recent_weights = conn.execute(
            """SELECT weight_kg FROM body_measurements
               WHERE weight_kg IS NOT NULL AND date >= date('now', '-28 days')
               ORDER BY date DESC
            """,
        ).fetchall()
        prior_weights = conn.execute(
            """SELECT weight_kg FROM body_measurements
               WHERE weight_kg IS NOT NULL AND date >= date('now', '-56 days') AND date < date('now', '-28 days')
               ORDER BY date DESC
            """,
        ).fetchall()

    if recent_weights and prior_weights:
        recent_avg = statistics.mean(r["weight_kg"] for r in recent_weights)
        prior_avg = statistics.mean(r["weight_kg"] for r in prior_weights)
        diff = recent_avg - prior_avg
        if abs(diff) < 0.5:
            fields["weight_kg_trend"] = "stable"
        elif diff > 0:
            fields["weight_kg_trend"] = "increasing"
        else:
            fields["weight_kg_trend"] = "decreasing"
    else:
        fields["weight_kg_trend"] = None

    # ── Resting HR baseline (30-day median) ───────────────────────────
    with db._connect() as conn:
        hr_rows = conn.execute(
            """SELECT resting_hr FROM wellness_snapshots
               WHERE resting_hr IS NOT NULL AND date >= date('now', '-30 days')
            """,
        ).fetchall()
    if hr_rows:
        fields["resting_hr_baseline"] = round(statistics.median(r["resting_hr"] for r in hr_rows), 1)
    else:
        fields["resting_hr_baseline"] = None

    # ── HRV baseline (30-day median) ──────────────────────────────────
    with db._connect() as conn:
        hrv_rows = conn.execute(
            """SELECT hrv_value FROM wellness_snapshots
               WHERE hrv_value IS NOT NULL AND date >= date('now', '-30 days')
            """,
        ).fetchall()
    if hrv_rows:
        fields["hrv_baseline"] = round(statistics.median(r["hrv_value"] for r in hrv_rows), 1)
    else:
        fields["hrv_baseline"] = None

    return db.upsert_athlete_profile(fields)


def get_athlete_profile(db: HistoryDB) -> dict[str, Any] | None:
    """Return the current athlete profile, or None if not yet generated."""
    return db.get_athlete_profile()


def update_athlete_profile_manual(db: HistoryDB, fields: dict[str, Any]) -> dict[str, Any]:
    """Update manually-entered fields only.

    Cannot overwrite auto-derived fields. Allowed fields:
    date_of_birth, gender, experience_level, injury_history,
    preferred_long_run_day, available_days_per_week, notes.

    Args:
        db: HistoryDB instance.
        fields: Dict of field names to values (only manual fields accepted).

    Returns:
        Updated profile dict.

    Raises:
        ValueError: If any field is not a valid manual field.
    """
    invalid = set(fields.keys()) - _MANUAL_FIELDS
    if invalid:
        msg = f"Cannot manually set auto-derived fields: {invalid}. Allowed: {_MANUAL_FIELDS}"
        raise ValueError(msg)

    # Serialize injury_history to JSON if it's a list/dict
    if "injury_history" in fields and not isinstance(fields["injury_history"], str):
        fields["injury_history"] = json.dumps(fields["injury_history"])

    return db.upsert_athlete_profile(fields)
