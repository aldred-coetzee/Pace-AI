"""Sync tools — ingest data from external MCP servers into the central history store."""

from __future__ import annotations

import logging
import re
import time
from datetime import date, datetime, timedelta
from typing import TYPE_CHECKING, Any

from pace_ai.tools.analysis import _vdot_from_time

if TYPE_CHECKING:
    from pace_ai.database import HistoryDB

log = logging.getLogger(__name__)

# Patterns for detecting races from activity names
_RACE_PATTERNS = re.compile(
    r"\b(race|parkrun|park run|5k race|10k race|half marathon|marathon|time trial)\b",
    re.IGNORECASE,
)

# Map common distance labels to meters
_DISTANCE_LABEL_MAP = {
    "1500m": 1500,
    "mile": 1609.34,
    "3k": 3000,
    "5k": 5000,
    "8k": 8000,
    "10k": 10000,
    "15k": 15000,
    "half marathon": 21097.5,
    "marathon": 42195,
}


def _detect_distance_label(distance_m: float) -> str | None:
    """Match a distance in meters to a standard race label (within 5% tolerance)."""
    for label, target_m in _DISTANCE_LABEL_MAP.items():
        if abs(distance_m - target_m) / target_m < 0.05:
            return label
    return None


def _is_likely_race(activity: dict[str, Any]) -> bool:
    """Detect if a Strava activity is likely a race."""
    if activity.get("workout_type") == 1:
        return True
    name = activity.get("name", "")
    return bool(_RACE_PATTERNS.search(name))


def sync_strava(db: HistoryDB, activities: list[dict[str, Any]]) -> dict[str, Any]:
    """Sync Strava activities into the history store.

    Accepts raw activity list from strava-mcp. Upserts into activities table,
    detects race results, calculates VDOT, and marks PBs.

    Returns:
        Summary with counts of synced activities and detected races.
    """
    # Map Strava fields to our schema
    mapped = []
    dates = []
    for a in activities:
        date = a.get("start_date_local", a.get("start_date", ""))[:10]
        if date:
            dates.append(date)
        mapped.append(
            {
                "strava_id": str(a.get("id", "")),
                "date": date,
                "sport_type": a.get("sport_type", a.get("type", "unknown")),
                "name": a.get("name"),
                "distance_m": a.get("distance"),
                "moving_time_s": a.get("moving_time"),
                "elapsed_time_s": a.get("elapsed_time"),
                "elevation_gain_m": a.get("total_elevation_gain"),
                "average_hr": a.get("average_heartrate"),
                "max_hr": a.get("max_heartrate"),
                "average_cadence": a.get("average_cadence"),
                "average_speed_ms": a.get("average_speed"),
                "description": a.get("description"),
                "private_note": a.get("private_note"),
                "perceived_effort": a.get("perceived_exertion"),
                "raw": a,
            }
        )

    activity_count = db.upsert_activities(mapped)

    # Detect races and create race results
    race_count = 0
    for a in activities:
        if _is_likely_race(a) and a.get("distance") and a.get("moving_time"):
            distance_m = a["distance"]
            time_s = a["moving_time"]
            distance_label = _detect_distance_label(distance_m)
            vdot = round(_vdot_from_time(distance_m, time_s), 1)
            date = a.get("start_date_local", a.get("start_date", ""))[:10]
            result = {
                "date": date,
                "distance_m": distance_m,
                "distance_label": distance_label,
                "time_s": time_s,
                "event_name": a.get("name"),
                "course_type": "road",
                "vdot": vdot,
                "source": str(a.get("id", "")),
            }
            db.upsert_race_result(result)
            race_count += 1

    # Recalculate PBs
    if race_count > 0:
        db.mark_pbs()

    earliest = min(dates) if dates else None
    latest = max(dates) if dates else None
    db.log_sync("strava", activity_count, "success", earliest_date=earliest, latest_date=latest)

    return {
        "source": "strava",
        "activities_synced": activity_count,
        "races_detected": race_count,
    }


def sync_garmin_wellness(db: HistoryDB, wellness_data: list[dict[str, Any]]) -> dict[str, Any]:
    """Sync Garmin wellness snapshots into the history store.

    Returns:
        Summary with count of synced records.
    """
    mapped = []
    dates = []
    for w in wellness_data:
        date = w.get("date", "")
        if date:
            dates.append(date)
        mapped.append(
            {
                "date": date,
                "body_battery_max": w.get("body_battery_max"),
                "body_battery_min": w.get("body_battery_min"),
                "hrv_status": w.get("hrv_status"),
                "hrv_value": w.get("hrv_value"),
                "sleep_score": w.get("sleep_score"),
                "sleep_duration_s": w.get("sleep_duration_s"),
                "sleep_deep_s": w.get("sleep_deep_s"),
                "sleep_rem_s": w.get("sleep_rem_s"),
                "stress_avg": w.get("stress_avg"),
                "stress_max": w.get("stress_max"),
                "training_readiness": w.get("training_readiness"),
                "resting_hr": w.get("resting_hr"),
                "respiration_avg": w.get("respiration_avg"),
                "raw": w,
            }
        )

    count = db.upsert_wellness(mapped)
    earliest = min(dates) if dates else None
    latest = max(dates) if dates else None
    db.log_sync("garmin_wellness", count, "success", earliest_date=earliest, latest_date=latest)

    return {"source": "garmin_wellness", "records_synced": count}


def sync_withings(db: HistoryDB, measurements: list[dict[str, Any]]) -> dict[str, Any]:
    """Sync Withings body measurements into the history store.

    Returns:
        Summary with count of synced records.
    """
    mapped = []
    dates = []
    for m in measurements:
        date = m.get("date", "")
        if date:
            dates.append(date)
        mapped.append(
            {
                "date": date,
                "weight_kg": m.get("weight_kg"),
                "bmi": m.get("bmi"),
                "body_fat_pct": m.get("body_fat_pct"),
                "muscle_mass_kg": m.get("muscle_mass_kg"),
                "bone_mass_kg": m.get("bone_mass_kg"),
                "water_pct": m.get("water_pct"),
                "systolic_bp": m.get("systolic_bp") or m.get("systolic_mmhg"),
                "diastolic_bp": m.get("diastolic_bp") or m.get("diastolic_mmhg"),
                "raw": m,
            }
        )

    count = db.upsert_body_measurements(mapped)
    earliest = min(dates) if dates else None
    latest = max(dates) if dates else None
    db.log_sync("withings", count, "success", earliest_date=earliest, latest_date=latest)

    return {"source": "withings", "records_synced": count}


def sync_notion(db: HistoryDB, entries: list[dict[str, Any]]) -> dict[str, Any]:
    """Sync Notion diary entries into the history store.

    Returns:
        Summary with count of synced records.
    """
    mapped = []
    dates = []
    for e in entries:
        date = e.get("date", "")
        if date:
            dates.append(date)
        mapped.append(
            {
                "date": date,
                "stress_1_5": e.get("stress_1_5"),
                "niggles": e.get("niggles"),
                "notes": e.get("notes"),
            }
        )

    count = db.upsert_diary_entries(mapped)
    earliest = min(dates) if dates else None
    latest = max(dates) if dates else None
    db.log_sync("notion", count, "success", earliest_date=earliest, latest_date=latest)

    return {"source": "notion", "records_synced": count}


def sync_garmin_workouts(db: HistoryDB, workouts: list[dict[str, Any]]) -> dict[str, Any]:
    """Sync Garmin scheduled workouts into the history store.

    Attempts to match completed workouts against activities by date and sport type.

    Returns:
        Summary with count of synced records.
    """
    mapped = []
    dates = []
    for w in workouts:
        date = w.get("scheduled_date", "")
        if date:
            dates.append(date)
        mapped.append(
            {
                "garmin_workout_id": str(w.get("garmin_workout_id", w.get("id", ""))),
                "sport_type": w.get("sport_type", "running"),
                "scheduled_date": date,
                "workout_name": w.get("workout_name", w.get("name")),
                "workout_detail": w.get("workout_detail"),
                "created_at": w.get("created_at"),
                "completed": w.get("completed", 0),
                "strava_activity_id": w.get("strava_activity_id"),
                "skipped_reason": w.get("skipped_reason"),
            }
        )

    count = db.upsert_scheduled_workouts(mapped)

    # Try to match unmatched workouts to activities by date + sport_type
    with db._connect() as conn:
        unmatched = conn.execute(
            "SELECT id, scheduled_date, sport_type FROM scheduled_workouts"
            " WHERE completed = 0 AND scheduled_date IS NOT NULL",
        ).fetchall()
        for row in unmatched:
            # Match "running" to "Run", "cycling" to "Ride", etc.
            sport = row["sport_type"].lower()
            sport_match = sport[:3]  # "run" from "running", "rid" from "ride"
            activity = conn.execute(
                "SELECT strava_id FROM activities WHERE date = ? AND LOWER(sport_type) LIKE ? LIMIT 1",
                (row["scheduled_date"], f"%{sport_match}%"),
            ).fetchone()
            if activity:
                conn.execute(
                    "UPDATE scheduled_workouts SET completed = 1, strava_activity_id = ? WHERE id = ?",
                    (activity["strava_id"], row["id"]),
                )

    earliest = min(dates) if dates else None
    latest = max(dates) if dates else None
    db.log_sync("garmin_workouts", count, "success", earliest_date=earliest, latest_date=latest)

    return {"source": "garmin_workouts", "records_synced": count}


def get_sync_status(db: HistoryDB) -> list[dict[str, Any]]:
    """Return sync status summary per source."""
    return db.get_sync_status()


def _last_sync_time(db: HistoryDB, source: str) -> str | None:
    """Return the synced_at timestamp from the most recent successful sync for a source."""
    with db._connect() as conn:
        row = conn.execute(
            "SELECT synced_at FROM sync_log WHERE source = ? AND status = 'success' ORDER BY id DESC LIMIT 1",
            (source,),
        ).fetchone()
    return row["synced_at"] if row else None


def _to_timestamp(d: str) -> int:
    """Convert a date/datetime string or Unix timestamp string to Unix timestamp.

    Accepts: YYYY-MM-DD, YYYY-MM-DDTHH:MM:SSZ (synced_at), or raw epoch strings.
    """
    if d.isdigit():
        return int(d)
    if "T" in d:
        return int(datetime.strptime(d, "%Y-%m-%dT%H:%M:%SZ").timestamp())
    return int(datetime.strptime(d[:10], "%Y-%m-%d").timestamp())


async def _enrich_private_notes(db: HistoryDB, strava_client: Any, days: int = 28) -> int:
    """Fetch detail for recent activities missing private_note and backfill them.

    Only fetches detail for activities where private_note is NULL, to minimise
    API calls. Returns count of activities enriched.
    """
    with db._connect() as conn:
        rows = conn.execute(
            """SELECT strava_id FROM activities
               WHERE private_note IS NULL AND date >= date('now', ?)
               ORDER BY date DESC""",
            (f"-{days} days",),
        ).fetchall()

    enriched = 0
    for row in rows:
        strava_id = row["strava_id"]
        try:
            detail = await strava_client.get_activity(int(strava_id))
        except Exception:
            log.warning("Failed to fetch detail for activity %s", strava_id)
            continue
        note = detail.get("private_note")
        if note:
            with db._connect() as conn:
                conn.execute(
                    "UPDATE activities SET private_note = ? WHERE strava_id = ?",
                    (note, strava_id),
                )
            enriched += 1
    return enriched


async def sync_all(db: HistoryDB) -> dict[str, Any]:
    """Incremental sync from all 5 external sources.

    Fetches only data newer than the last successful sync per source.
    Continues if any single source fails. Calls external client libraries directly.

    Returns:
        Summary dict with per-source results and any errors.
    """
    results: dict[str, Any] = {}
    errors: dict[str, str] = {}

    # ── 1. Strava ────────────────────────────────────────────────────
    try:
        from strava_mcp.auth import TokenStore
        from strava_mcp.client import StravaClient
        from strava_mcp.config import Settings as StravaSettings

        strava_settings = StravaSettings.from_env()
        token_store = TokenStore(strava_settings.db_path)
        strava_client = StravaClient(strava_settings, token_store)

        last = _last_sync_time(db, "strava")
        after_ts = _to_timestamp(last) if last else None
        activities = await strava_client.get_all_activities(after=after_ts)
        results["strava"] = sync_strava(db, activities)

        # Enrich recent activities with private_note (only available from detail endpoint)
        enriched = await _enrich_private_notes(db, strava_client, days=28)
        if enriched:
            results["strava"]["private_notes_enriched"] = enriched
    except Exception as exc:
        log.exception("sync_all: strava failed")
        errors["strava"] = str(exc)
        db.log_sync("strava", 0, "error", error=str(exc))

    # ── 2. Garmin Wellness ───────────────────────────────────────────
    try:
        from garmin_mcp.client import GarminClient
        from garmin_mcp.config import Settings as GarminSettings

        garmin_settings = GarminSettings.from_env()
        garmin_client = GarminClient(garmin_settings)

        last = _last_sync_time(db, "garmin_wellness")
        # Garmin wellness is per-day, so sync from the day of last sync (to catch same-day updates)
        # Always re-sync yesterday (sleep/resting HR may not have been available at previous sync)
        if last:
            sync_date = datetime.strptime(last, "%Y-%m-%dT%H:%M:%SZ").date()
            start_date = min(sync_date, date.today() - timedelta(days=1))
        else:
            start_date = date.today() - timedelta(days=14)
        end_date = date.today()

        wellness_records: list[dict[str, Any]] = []
        current = start_date
        while current <= end_date:
            d = current.isoformat()
            record: dict[str, Any] = {"date": d}
            for metric, fetch in [
                ("body_battery", garmin_client.get_body_battery),
                ("sleep", garmin_client.get_sleep),
                ("stress", garmin_client.get_stress),
                ("resting_hr", garmin_client.get_resting_hr),
            ]:
                try:
                    data = fetch(d)
                    if metric == "body_battery" and data:
                        levels = None
                        if isinstance(data, list):
                            levels = data
                        elif isinstance(data, dict):
                            levels = data.get("bodyBatteryValuesArray") or data.get("bodyBatteryStatList")
                        if levels:
                            vals = [v[-1] if isinstance(v, list) else v.get("batteryLevel", 0) for v in levels if v]
                            vals = [v for v in vals if v and v > 0]
                            record["body_battery_max"] = max(vals) if vals else None
                            record["body_battery_min"] = min(vals) if vals else None
                        else:
                            charged = data.get("charged") if isinstance(data, dict) else None
                            drained = data.get("drained") if isinstance(data, dict) else None
                            if charged or drained:
                                record["body_battery_max"] = charged
                                record["body_battery_min"] = drained
                    elif metric == "sleep" and data:
                        if isinstance(data, dict):
                            record["sleep_duration_s"] = data.get("sleepTimeSeconds")
                            record["sleep_deep_s"] = data.get("deepSleepSeconds")
                            record["sleep_rem_s"] = data.get("remSleepSeconds")
                    elif metric == "stress" and data:
                        if isinstance(data, dict):
                            record["stress_avg"] = data.get("overallStressLevel") or data.get("avgStressLevel")
                            record["stress_max"] = data.get("maxStressLevel")
                    elif metric == "resting_hr" and data:
                        if isinstance(data, dict):
                            # Navigate nested Garmin resting HR response
                            metrics_map = data.get("allMetrics", {}).get("metricsMap", {})
                            rhr_list = metrics_map.get("WELLNESS_RESTING_HEART_RATE", [])
                            if rhr_list and isinstance(rhr_list[0], dict):
                                val = rhr_list[0].get("value")
                                if val and 30 <= val <= 120:
                                    record["resting_hr"] = int(val)
                            elif data.get("restingHeartRate"):
                                record["resting_hr"] = data["restingHeartRate"]
                except Exception:
                    pass  # Individual metric failure — continue
            wellness_records.append(record)
            current += timedelta(days=1)

        if wellness_records:
            results["garmin_wellness"] = sync_garmin_wellness(db, wellness_records)
        else:
            results["garmin_wellness"] = {"source": "garmin_wellness", "records_synced": 0, "message": "up to date"}
    except Exception as exc:
        log.exception("sync_all: garmin_wellness failed")
        errors["garmin_wellness"] = str(exc)
        db.log_sync("garmin_wellness", 0, "error", error=str(exc))

    # ── 3. Garmin Workouts ───────────────────────────────────────────
    try:
        # Reuse garmin_client from above if available, otherwise create new
        if "garmin_client" not in dir():
            from garmin_mcp.client import GarminClient
            from garmin_mcp.config import Settings as GarminSettings

            garmin_settings = GarminSettings.from_env()
            garmin_client = GarminClient(garmin_settings)

        last_workout_sync = _last_sync_time(db, "garmin_workouts")
        last_workout_ts = _to_timestamp(last_workout_sync) if last_workout_sync else 0

        raw_workouts = garmin_client.get_workouts(start=0, limit=100)
        if raw_workouts:
            # Filter to workouts created/updated since last sync
            new_workouts = []
            for w in raw_workouts:
                updated = w.get("updatedDate") or w.get("createdDate") or ""
                if updated and last_workout_ts:
                    # Garmin dates: "2026-03-08T10:00:00.0" or epoch millis
                    try:
                        w_ts = _to_timestamp(updated[:19].replace(".0", "").replace(" ", "T") + "Z")
                    except (ValueError, IndexError):
                        w_ts = 0
                    if w_ts <= last_workout_ts:
                        continue
                new_workouts.append(w)

            if new_workouts:
                workout_mapped = []
                for w in new_workouts:
                    sport = w.get("sportType", {})
                    workout_mapped.append(
                        {
                            "garmin_workout_id": str(w.get("workoutId", "")),
                            "sport_type": (
                                sport.get("sportTypeKey", "running") if isinstance(sport, dict) else "running"
                            ),
                            "scheduled_date": w.get("createdDate", "")[:10] if w.get("createdDate") else "",
                            "workout_name": w.get("workoutName"),
                        }
                    )
                results["garmin_workouts"] = sync_garmin_workouts(db, workout_mapped)
            else:
                results["garmin_workouts"] = {
                    "source": "garmin_workouts",
                    "records_synced": 0,
                    "message": "up to date",
                }
        else:
            results["garmin_workouts"] = {"source": "garmin_workouts", "records_synced": 0}
    except Exception as exc:
        log.exception("sync_all: garmin_workouts failed")
        errors["garmin_workouts"] = str(exc)
        db.log_sync("garmin_workouts", 0, "error", error=str(exc))

    # ── 4. Withings ──────────────────────────────────────────────────
    try:
        from withings_mcp.client import WithingsClient
        from withings_mcp.config import Settings as WithingsSettings

        withings_settings = WithingsSettings.from_env()
        withings_client = WithingsClient(withings_settings)

        last = _last_sync_time(db, "withings")
        start_ts = _to_timestamp(last) if last else int(time.time()) - 14 * 86400
        end_ts = int(time.time())
        measurements = withings_client.get_measurements(startdate=start_ts, enddate=end_ts)

        # Convert timestamps to YYYY-MM-DD in datetime field
        for m in measurements:
            if "datetime" in m and isinstance(m["datetime"], str):
                m["date"] = m["datetime"][:10]
            elif "date" in m and isinstance(m["date"], (int, float)):
                m["date"] = datetime.fromtimestamp(m["date"]).strftime("%Y-%m-%d")

        results["withings"] = sync_withings(db, measurements)
    except Exception as exc:
        log.exception("sync_all: withings failed")
        errors["withings"] = str(exc)
        db.log_sync("withings", 0, "error", error=str(exc))

    # ── 5. Notion ────────────────────────────────────────────────────
    try:
        from notion_mcp.client import NotionClient, parse_diary_entry
        from notion_mcp.config import Settings as NotionSettings

        last_notion_sync = _last_sync_time(db, "notion")
        last_notion_ts = _to_timestamp(last_notion_sync) if last_notion_sync else 0

        notion_settings = NotionSettings.from_env()
        notion_client = NotionClient(notion_settings)

        raw_pages = await notion_client.fetch_all_entries()

        # Filter to pages edited since last sync
        new_pages = []
        for p in raw_pages:
            edited = p.get("last_edited_time", "")
            if edited and last_notion_ts:
                try:
                    p_ts = _to_timestamp(edited.rstrip("Z")[:19] + "Z")
                except (ValueError, IndexError):
                    p_ts = 0
                if p_ts <= last_notion_ts:
                    continue
            new_pages.append(p)

        entries = [parse_diary_entry(p) for p in new_pages]
        entries = [e for e in entries if e is not None]

        mapped_entries = []
        for e in entries:
            mapped_entries.append(
                {
                    "date": e.get("date", ""),
                    "stress_1_5": e.get("stress"),
                    "niggles": e.get("niggles"),
                    "notes": e.get("notes"),
                }
            )

        results["notion"] = sync_notion(db, mapped_entries)
    except Exception as exc:
        log.exception("sync_all: notion failed")
        errors["notion"] = str(exc)
        db.log_sync("notion", 0, "error", error=str(exc))

    summary: dict[str, Any] = {"results": results}
    if errors:
        summary["errors"] = errors
    summary["sources_synced"] = len(results)
    summary["sources_failed"] = len(errors)
    return summary
