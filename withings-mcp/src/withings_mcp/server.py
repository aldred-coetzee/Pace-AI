"""FastMCP server for Withings body composition and health metrics."""

from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone
from typing import Any

from mcp.server.fastmcp import FastMCP

from withings_mcp.client import WithingsAPIError, WithingsClient
from withings_mcp.config import Settings

settings = Settings.from_env()
withings = WithingsClient(settings)

mcp = FastMCP(
    "withings-mcp",
    instructions="MCP server for Withings body composition and health metrics — weight, body fat, blood pressure",
    host=settings.host,
    port=settings.port,
)


# ── Tools ──────────────────────────────────────────────────────────────


@mcp.tool()
async def authenticate() -> dict:
    """Check Withings connection by initializing the account.

    The withings-sync library handles OAuth automatically. If tokens exist
    in ~/.withings_user.json they will be refreshed. If not, the library
    will prompt for authentication.
    """
    try:
        withings._ensure_account()
        return {"authenticated": True}
    except WithingsAPIError as e:
        return e.to_dict()


@mcp.tool()
async def get_measurements(from_date: str, to_date: str) -> dict:
    """Get body composition measurements between two dates.

    Returns weight, body fat %, muscle mass, bone mass, and body water for each
    measurement session in the date range.

    Args:
        from_date: Start date in YYYY-MM-DD format.
        to_date: End date in YYYY-MM-DD format.
    """
    try:
        startdate = _date_to_timestamp(from_date)
        enddate = _date_to_timestamp(to_date, end_of_day=True)
        measurements = withings.get_measurements(startdate, enddate)
        return {
            "from_date": from_date,
            "to_date": to_date,
            "count": len(measurements),
            "measurements": measurements,
        }
    except WithingsAPIError as e:
        return e.to_dict()


@mcp.tool()
async def get_latest_weight() -> dict:
    """Get the most recent weight measurement.

    Returns the latest weight, body fat %, and related metrics.
    """
    try:
        now = int(time.time())
        # Look back 90 days for the most recent measurement
        startdate = now - (90 * 86400)
        measurements = withings.get_measurements(startdate, now)

        weight_entries = [m for m in measurements if "weight_kg" in m]
        if not weight_entries:
            return {"message": "No weight measurements found in the last 90 days."}

        # Sort by date descending — most recent first
        weight_entries.sort(key=lambda m: m.get("date", 0), reverse=True)
        latest = weight_entries[0]
        latest["date_str"] = _timestamp_to_date(latest.get("date", 0))
        return latest
    except WithingsAPIError as e:
        return e.to_dict()


@mcp.tool()
async def get_blood_pressure(from_date: str, to_date: str) -> dict:
    """Get blood pressure readings between two dates.

    Returns systolic, diastolic, and heart rate (if available) for each reading.

    Args:
        from_date: Start date in YYYY-MM-DD format.
        to_date: End date in YYYY-MM-DD format.
    """
    try:
        startdate = _date_to_timestamp(from_date)
        enddate = _date_to_timestamp(to_date, end_of_day=True)
        measurements = withings.get_measurements(startdate, enddate)

        # Filter to only entries that have BP data
        bp_entries = [m for m in measurements if "systolic_mmhg" in m or "diastolic_mmhg" in m]
        for entry in bp_entries:
            entry["date_str"] = _timestamp_to_date(entry.get("date", 0))

        return {
            "from_date": from_date,
            "to_date": to_date,
            "count": len(bp_entries),
            "readings": bp_entries,
        }
    except WithingsAPIError as e:
        return e.to_dict()


@mcp.tool()
async def get_body_composition_trend(weeks: int = 8) -> dict:
    """Get weekly averages for weight and body fat over time.

    Useful for tracking body composition trends alongside training load.

    Args:
        weeks: Number of weeks to look back (default 8).
    """
    try:
        now = int(time.time())
        startdate = now - (weeks * 7 * 86400)
        measurements = withings.get_measurements(startdate, now)

        weight_entries = [m for m in measurements if "weight_kg" in m]
        if not weight_entries:
            return {"message": f"No weight measurements found in the last {weeks} weeks.", "weeks": []}

        # Group by ISO week
        weekly: dict[str, list[dict[str, Any]]] = {}
        for entry in weight_entries:
            ts = entry.get("date", 0)
            dt = datetime.fromtimestamp(ts, tz=timezone.utc)
            week_key = dt.strftime("%G-W%V")
            weekly.setdefault(week_key, []).append(entry)

        trend = []
        for week_key in sorted(weekly.keys()):
            entries = weekly[week_key]
            avg_weight = round(sum(e.get("weight_kg", 0) for e in entries) / len(entries), 2)
            fat_entries = [e for e in entries if "fat_ratio_pct" in e]
            avg_fat = round(sum(e["fat_ratio_pct"] for e in fat_entries) / len(fat_entries), 1) if fat_entries else None
            trend.append(
                {
                    "week": week_key,
                    "avg_weight_kg": avg_weight,
                    "avg_fat_ratio_pct": avg_fat,
                    "measurement_count": len(entries),
                }
            )

        return {"weeks_requested": weeks, "trend": trend}
    except WithingsAPIError as e:
        return e.to_dict()


# ── Resources ──────────────────────────────────────────────────────────


@mcp.resource("withings://measure-types")
async def measure_types_resource() -> str:
    """Available Withings measurement fields returned by get_measurements."""
    import json

    fields = {
        "weight_kg": "Body weight in kilograms",
        "fat_ratio_pct": "Body fat percentage",
        "fat_mass_kg": "Fat mass in kilograms",
        "fat_free_mass_kg": "Fat-free mass in kilograms",
        "muscle_mass_kg": "Muscle mass in kilograms",
        "bone_mass_kg": "Bone mass in kilograms",
        "hydration_kg": "Body water in kilograms",
        "systolic_mmhg": "Systolic blood pressure (mmHg)",
        "diastolic_mmhg": "Diastolic blood pressure (mmHg)",
        "heart_pulse_bpm": "Heart rate (bpm)",
    }
    return json.dumps(fields, indent=2)


# ── Helpers ────────────────────────────────────────────────────────────


def _date_to_timestamp(date_str: str, *, end_of_day: bool = False) -> int:
    """Convert YYYY-MM-DD string to Unix timestamp."""
    dt = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    if end_of_day:
        dt = dt + timedelta(days=1) - timedelta(seconds=1)
    return int(dt.timestamp())


def _timestamp_to_date(ts: int) -> str:
    """Convert Unix timestamp to YYYY-MM-DD string."""
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")


# ── Entry Point ────────────────────────────────────────────────────────


def main() -> None:
    """Entry point for the withings-mcp server."""
    import os

    mcp.run(transport=os.environ.get("MCP_TRANSPORT", "streamable-http"))


if __name__ == "__main__":
    main()
