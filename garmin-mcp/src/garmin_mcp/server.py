"""FastMCP server for Garmin Connect workout management."""

from __future__ import annotations

import json
from datetime import date, timedelta
from typing import Any

from mcp.server.fastmcp import FastMCP

from garmin_mcp.client import GarminAPIError, GarminClient
from garmin_mcp.config import Settings
from garmin_mcp.workout_builder import (
    WORKOUT_TYPES,
    build_cardio_workout,
    build_hiit_workout,
    build_mobility_workout,
    build_strength_workout,
    build_walking_workout,
    build_yoga_workout,
    custom_workout,
    easy_run,
    interval_repeats,
    run_walk,
    strides,
    tempo_run,
)

settings = Settings.from_env()
garmin = GarminClient(settings)

mcp = FastMCP(
    "garmin-mcp",
    instructions=(
        "MCP server for Garmin Connect workout management — create, schedule, and sync workouts to Garmin watches"
    ),
    host=settings.host,
    port=settings.port,
)


# ── Tools ──────────────────────────────────────────────────────────────


@mcp.tool()
async def authenticate() -> dict:
    """Check/resume Garmin Connect session. Returns auth status."""
    try:
        return garmin.check_auth()
    except GarminAPIError as e:
        return e.to_dict()


@mcp.tool()
async def create_workout(
    workout_type: str,
    name: str,
    params_json: str = "{}",
) -> dict:
    """Create a workout in Garmin Connect by type.

    Builds structured workout JSON and uploads it. The workout will appear in
    Garmin Connect and can be scheduled to a date (syncs to watch).

    Args:
        workout_type: easy_run|run_walk|tempo|intervals|strides|strength|mobility|yoga|cardio|hiit|walking|custom.
        name: Workout name (shown on watch).
        params_json: JSON object of type-specific parameters. See garmin://workout-types resource.
    """
    if workout_type not in WORKOUT_TYPES:
        return {
            "error": "invalid_workout_type",
            "message": f"Unknown workout type: {workout_type}",
            "valid_types": list(WORKOUT_TYPES.keys()),
        }

    try:
        params = json.loads(params_json)
    except json.JSONDecodeError as e:
        return {"error": "invalid_json", "message": f"Failed to parse params_json: {e}"}

    try:
        workout_json = _build_workout(workout_type, name, params)
    except (TypeError, ValueError) as e:
        return {"error": "invalid_params", "message": str(e)}

    try:
        result = garmin.create_workout(workout_json)
        workout_id = result.get("workoutId") if isinstance(result, dict) else None
        return {
            "created": True,
            "workout_id": workout_id,
            "workout_name": name,
            "workout_type": workout_type,
        }
    except GarminAPIError as e:
        return e.to_dict()


@mcp.tool()
async def list_workouts(start: int = 0, limit: int = 50) -> dict:
    """List workouts in Garmin Connect.

    Args:
        start: Offset for pagination (default 0).
        limit: Max results to return (default 50).
    """
    try:
        workouts = garmin.get_workouts(start, limit)
        if isinstance(workouts, list):
            return {
                "count": len(workouts),
                "workouts": [
                    {
                        "workout_id": w.get("workoutId"),
                        "name": w.get("workoutName"),
                        "sport_type": w.get("sportType", {}).get("sportTypeKey"),
                        "created_date": w.get("createdDate"),
                        "updated_date": w.get("updatedDate"),
                    }
                    for w in workouts
                ],
            }
        return {"count": 0, "workouts": [], "raw": workouts}
    except GarminAPIError as e:
        return e.to_dict()


@mcp.tool()
async def get_workout(workout_id: int) -> dict:
    """Get workout details by ID.

    Args:
        workout_id: The Garmin workout ID.
    """
    try:
        return garmin.get_workout(workout_id)
    except GarminAPIError as e:
        return e.to_dict()


@mcp.tool()
async def delete_workout(workout_id: int) -> dict:
    """Delete a workout from Garmin Connect.

    Args:
        workout_id: The Garmin workout ID to delete.
    """
    try:
        return garmin.delete_workout(workout_id)
    except GarminAPIError as e:
        return e.to_dict()


@mcp.tool()
async def schedule_workout(workout_id: int, date: str) -> dict:
    """Schedule a workout to a specific calendar date.

    The workout will sync to the watch and appear on the scheduled date.

    Args:
        workout_id: The Garmin workout ID.
        date: Date in YYYY-MM-DD format.
    """
    try:
        return garmin.schedule_workout(workout_id, date)
    except GarminAPIError as e:
        return e.to_dict()


@mcp.tool()
async def list_calendar(start_date: str, end_date: str) -> dict:
    """List scheduled items on the Garmin Connect calendar for a date range.

    Returns workouts, activities, and other events scheduled in the range.

    Args:
        start_date: Start date in YYYY-MM-DD format.
        end_date: End date in YYYY-MM-DD format (inclusive).
    """
    try:
        start = date.fromisoformat(start_date)
        end = date.fromisoformat(end_date)
    except ValueError:
        return {"error": "invalid_date", "message": "Dates must be YYYY-MM-DD format."}

    if end < start:
        return {"error": "invalid_range", "message": "end_date must be >= start_date."}

    # Fetch calendar months that cover the date range (month is 0-indexed)
    all_items: list[dict[str, Any]] = []
    seen_months: set[tuple[int, int]] = set()
    current = start
    while current <= end:
        key = (current.year, current.month - 1)  # API uses 0-indexed months
        if key not in seen_months:
            seen_months.add(key)
            try:
                data = garmin.get_calendar(current.year, current.month - 1)
                items = data.get("calendarItems", []) if isinstance(data, dict) else []
                all_items.extend(items)
            except GarminAPIError:
                pass
        current += timedelta(days=1)

    # Filter to items within the requested date range
    filtered = [
        item for item in all_items
        if item.get("date") and start_date <= item["date"] <= end_date
    ]

    events = [
        {
            "id": item.get("id"),
            "title": item.get("title"),
            "date": item.get("date"),
            "item_type": item.get("itemType"),
            "sport_type": item.get("sportTypeKey"),
            "duration": item.get("duration"),
            "distance": item.get("distance"),
        }
        for item in filtered
    ]

    return {"start_date": start_date, "end_date": end_date, "count": len(events), "events": events}


# ── Wellness Tools ────────────────────────────────────────────────────


@mcp.tool()
async def get_body_battery(date: str) -> dict:
    """Get daily body battery data from Garmin.

    Args:
        date: Date in YYYY-MM-DD format.
    """
    try:
        return {"date": date, "data": garmin.get_body_battery(date)}
    except GarminAPIError as e:
        return e.to_dict()


@mcp.tool()
async def get_sleep(date: str) -> dict:
    """Get sleep score and summary from Garmin.

    Args:
        date: Date in YYYY-MM-DD format.
    """
    try:
        return garmin.get_sleep(date)
    except GarminAPIError as e:
        return e.to_dict()


@mcp.tool()
async def get_hrv(date: str) -> dict:
    """Get HRV (heart rate variability) status from Garmin.

    Args:
        date: Date in YYYY-MM-DD format.
    """
    try:
        data = garmin.get_hrv(date)
        if data is None:
            return {"date": date, "hrv": None, "message": "No HRV data available for this date."}
        return data
    except GarminAPIError as e:
        return e.to_dict()


@mcp.tool()
async def get_training_readiness(date: str) -> dict:
    """Get training readiness score from Garmin.

    Args:
        date: Date in YYYY-MM-DD format.
    """
    try:
        return garmin.get_training_readiness(date)
    except GarminAPIError as e:
        return e.to_dict()


@mcp.tool()
async def get_stress(date: str) -> dict:
    """Get daily stress data from Garmin.

    Args:
        date: Date in YYYY-MM-DD format.
    """
    try:
        return garmin.get_stress(date)
    except GarminAPIError as e:
        return e.to_dict()


@mcp.tool()
async def get_resting_hr(date: str) -> dict:
    """Get resting heart rate from Garmin.

    Args:
        date: Date in YYYY-MM-DD format.
    """
    try:
        data = garmin.get_resting_hr(date)
        if data is None:
            return {"date": date, "resting_hr": None, "message": "No resting HR data available for this date."}
        return data
    except GarminAPIError as e:
        return e.to_dict()


@mcp.tool()
async def get_wellness_snapshot(days: int = 7) -> dict:
    """Get a combined wellness summary for today and the past N days.

    Fetches body battery, sleep, HRV, resting HR, training readiness, and stress
    for each day and returns a combined summary useful for coaching context.

    Args:
        days: Number of past days to include (default 7).
    """
    today = date.today()
    dates = [(today - timedelta(days=i)).isoformat() for i in range(days)]

    snapshot: dict[str, Any] = {"dates": dates, "days": []}
    for d in dates:
        day_data: dict[str, Any] = {"date": d}
        for metric, fetch in [
            ("body_battery", garmin.get_body_battery),
            ("sleep", garmin.get_sleep),
            ("hrv", garmin.get_hrv),
            ("resting_hr", garmin.get_resting_hr),
            ("training_readiness", garmin.get_training_readiness),
            ("stress", garmin.get_stress),
        ]:
            try:
                day_data[metric] = fetch(d)
            except GarminAPIError:
                day_data[metric] = None
        snapshot["days"].append(day_data)

    return snapshot


# ── Resources ──────────────────────────────────────────────────────────


@mcp.resource("garmin://workout-types")
async def workout_types_resource() -> str:
    """Available workout types and their parameters for create_workout."""
    return json.dumps(WORKOUT_TYPES, indent=2)


# ── Helpers ────────────────────────────────────────────────────────────


_BUILDERS = {
    "easy_run": easy_run,
    "run_walk": run_walk,
    "tempo": tempo_run,
    "intervals": interval_repeats,
    "strides": strides,
    "strength": build_strength_workout,
    "mobility": build_mobility_workout,
    "yoga": build_yoga_workout,
    "cardio": build_cardio_workout,
    "hiit": build_hiit_workout,
    "walking": build_walking_workout,
    "custom": custom_workout,
}


def _build_workout(workout_type: str, name: str, params: dict[str, Any]) -> dict[str, Any]:
    """Dispatch to the correct workout builder function."""
    builder = _BUILDERS.get(workout_type)
    if builder is None:
        msg = f"Unknown workout type: {workout_type}"
        raise ValueError(msg)
    return builder(name, **params)


# ── Entry Point ────────────────────────────────────────────────────────


def main() -> None:
    """Entry point for the garmin-mcp server."""
    import os

    mcp.run(transport=os.environ.get("MCP_TRANSPORT", "streamable-http"))


if __name__ == "__main__":
    main()
