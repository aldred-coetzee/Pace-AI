"""FastMCP server for running coaching intelligence."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from pace_ai.config import Settings
from pace_ai.database import GoalDB
from pace_ai.prompts.coaching import (
    injury_risk_prompt,
    race_readiness_prompt,
    run_analysis_prompt,
    weekly_plan_prompt,
)
from pace_ai.resources.methodology import METHODOLOGY, ZONES_EXPLAINED
from pace_ai.tools import analysis as analysis_mod
from pace_ai.tools import goals as goals_mod

settings = Settings.from_env()
goal_db = GoalDB(settings.db_path)

mcp = FastMCP(
    "pace-ai",
    instructions="Running coach intelligence layer — coaching prompts, methodology, goals, and training analysis",
    host=settings.host,
    port=settings.port,
)


# ── Goal Tools ─────────────────────────────────────────────────────────


@mcp.tool()
async def set_goal(race_type: str, target_time: str, race_date: str | None = None, notes: str | None = None) -> dict:
    """Store a new training goal.

    Args:
        race_type: Race distance/type (e.g. "5k", "10k", "half marathon", "marathon").
        target_time: Target finish time in H:MM:SS or M:SS format.
        race_date: Optional race date (YYYY-MM-DD).
        notes: Optional notes about the goal.
    """
    return goals_mod.set_goal(goal_db, race_type, target_time, race_date, notes)


@mcp.tool()
async def get_goals() -> list[dict]:
    """List all current training goals."""
    return goals_mod.get_goals(goal_db)


@mcp.tool()
async def update_goal(
    goal_id: int,
    race_type: str | None = None,
    target_time: str | None = None,
    race_date: str | None = None,
    notes: str | None = None,
) -> dict | str:
    """Update an existing goal.

    Args:
        goal_id: The goal ID to update.
        race_type: New race type (optional).
        target_time: New target time in H:MM:SS or M:SS format (optional).
        race_date: New race date (optional).
        notes: New notes (optional).
    """
    result = goals_mod.update_goal(goal_db, goal_id, race_type, target_time, race_date, notes)
    if result is None:
        return f"Goal {goal_id} not found."
    return result


@mcp.tool()
async def delete_goal(goal_id: int) -> str:
    """Delete a training goal.

    Args:
        goal_id: The goal ID to delete.
    """
    return goals_mod.delete_goal(goal_db, goal_id)


# ── Analysis Tools ─────────────────────────────────────────────────────


@mcp.tool()
async def analyze_training_load(weekly_distances: list[float]) -> dict:
    """Compute ACWR, monotony, and strain from weekly distance data.

    Args:
        weekly_distances: Weekly distances in km (most recent last), minimum 4 weeks.
    """
    return analysis_mod.calculate_acwr(weekly_distances)


@mcp.tool()
async def predict_race_time(recent_race_distance: str, recent_race_time: str, target_distance: str) -> dict:
    """Predict race time using VDOT model and Riegel formula.

    Args:
        recent_race_distance: Distance of a recent race (e.g. "5k", "10k", "half marathon").
        recent_race_time: Finish time of that race (H:MM:SS or M:SS).
        target_distance: Target distance to predict (e.g. "marathon", "half marathon").
    """
    return analysis_mod.predict_race_time(recent_race_distance, recent_race_time, target_distance)


@mcp.tool()
async def calculate_training_zones(
    threshold_pace_per_km: str | None = None,
    threshold_hr: int | None = None,
) -> dict:
    """Calculate Daniels' training zones from threshold pace and/or heart rate.

    Args:
        threshold_pace_per_km: Threshold pace as M:SS per km (e.g. "4:30").
        threshold_hr: Threshold heart rate in bpm.
    """
    return analysis_mod.calculate_training_zones(
        threshold_pace_per_km=threshold_pace_per_km,
        threshold_hr=threshold_hr,
    )


# ── Prompts ────────────────────────────────────────────────────────────


@mcp.prompt()
async def weekly_plan(
    goals_json: str = "[]",
    activities_json: str = "[]",
    stats_json: str = "{}",
    zones_json: str = "null",
) -> str:
    """Generate a structured weekly training plan.

    Pass JSON-serialized data from strava-mcp tools and pace-ai goals.

    Args:
        goals_json: JSON array of goals from get_goals().
        activities_json: JSON array of recent activities from strava-mcp.
        stats_json: JSON object of athlete stats from strava-mcp.
        zones_json: JSON object of training zones (optional).
    """
    import json

    return weekly_plan_prompt(
        goals=json.loads(goals_json),
        recent_activities=json.loads(activities_json),
        athlete_stats=json.loads(stats_json),
        training_zones=json.loads(zones_json) if zones_json != "null" else None,
    )


@mcp.prompt()
async def run_analysis(
    activity_json: str = "{}",
    streams_json: str = "null",
    goals_json: str = "null",
) -> str:
    """Analyze a specific run with coaching insights.

    Args:
        activity_json: JSON object of full activity detail from strava-mcp.
        streams_json: JSON object of activity streams (optional).
        goals_json: JSON array of goals (optional).
    """
    import json

    return run_analysis_prompt(
        activity=json.loads(activity_json),
        streams=json.loads(streams_json) if streams_json != "null" else None,
        goals=json.loads(goals_json) if goals_json != "null" else None,
    )


@mcp.prompt()
async def race_readiness(
    goals_json: str = "[]",
    activities_json: str = "[]",
    stats_json: str = "{}",
    training_load_json: str = "null",
) -> str:
    """Assess readiness for an upcoming race.

    Args:
        goals_json: JSON array of goals.
        activities_json: JSON array of recent activities.
        stats_json: JSON object of athlete stats.
        training_load_json: JSON object of ACWR analysis (optional).
    """
    import json

    return race_readiness_prompt(
        goals=json.loads(goals_json),
        recent_activities=json.loads(activities_json),
        athlete_stats=json.loads(stats_json),
        training_load=json.loads(training_load_json) if training_load_json != "null" else None,
    )


@mcp.prompt()
async def injury_risk(
    weekly_distances_json: str = "[]",
    training_load_json: str = "{}",
    activities_json: str = "null",
) -> str:
    """Assess injury risk from training load patterns.

    Args:
        weekly_distances_json: JSON array of weekly distances (km).
        training_load_json: JSON object of ACWR analysis.
        activities_json: JSON array of recent activities (optional).
    """
    import json

    return injury_risk_prompt(
        weekly_distances=json.loads(weekly_distances_json),
        training_load=json.loads(training_load_json),
        recent_activities=json.loads(activities_json) if activities_json != "null" else None,
    )


# ── Resources ──────────────────────────────────────────────────────────


@mcp.resource("coaching://methodology")
async def methodology_resource() -> str:
    """Complete running coaching methodology — principles, zones, periodisation."""
    return METHODOLOGY


@mcp.resource("coaching://zones-explained")
async def zones_explained_resource() -> str:
    """Detailed explanation of each training zone with purpose and session formats."""
    return ZONES_EXPLAINED


# ── Entry Point ────────────────────────────────────────────────────────


def main() -> None:
    """Entry point for the pace-ai server."""
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
