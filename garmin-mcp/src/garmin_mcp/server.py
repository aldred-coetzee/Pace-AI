"""FastMCP server for Garmin Connect workout management."""

from __future__ import annotations

import json
from typing import Any

from mcp.server.fastmcp import FastMCP

from garmin_mcp.client import GarminAPIError, GarminClient
from garmin_mcp.config import Settings
from garmin_mcp.workout_builder import (
    WORKOUT_TYPES,
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
        workout_type: One of: easy_run, run_walk, tempo, intervals, strides, custom.
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
async def list_calendar(year: int, month: int) -> dict:
    """List scheduled items on the Garmin Connect calendar for a month.

    Args:
        year: Calendar year (e.g. 2026).
        month: Calendar month (1-12).
    """
    try:
        return garmin.get_calendar(year, month)
    except GarminAPIError as e:
        return e.to_dict()


# ── Resources ──────────────────────────────────────────────────────────


@mcp.resource("garmin://workout-types")
async def workout_types_resource() -> str:
    """Available workout types and their parameters for create_workout."""
    return json.dumps(WORKOUT_TYPES, indent=2)


# ── Helpers ────────────────────────────────────────────────────────────


def _build_workout(workout_type: str, name: str, params: dict[str, Any]) -> dict[str, Any]:
    """Dispatch to the correct workout builder function."""
    if workout_type == "easy_run":
        return easy_run(name, **params)
    if workout_type == "run_walk":
        return run_walk(name, **params)
    if workout_type == "tempo":
        return tempo_run(name, **params)
    if workout_type == "intervals":
        return interval_repeats(name, **params)
    if workout_type == "strides":
        return strides(name, **params)
    if workout_type == "custom":
        return custom_workout(name, **params)
    msg = f"Unknown workout type: {workout_type}"
    raise ValueError(msg)


# ── Entry Point ────────────────────────────────────────────────────────


def main() -> None:
    """Entry point for the garmin-mcp server."""
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
