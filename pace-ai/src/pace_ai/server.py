"""FastMCP server for running coaching intelligence."""

from __future__ import annotations

import json
from typing import Any

from mcp.server.fastmcp import FastMCP

from pace_ai.config import Settings
from pace_ai.database import GoalDB
from pace_ai.prompts.coaching import (
    injury_risk_prompt,
    race_readiness_prompt,
    run_analysis_prompt,
    weekly_plan_prompt,
)
from pace_ai.resources.methodology import FIELD_TEST_PROTOCOLS, METHODOLOGY, ZONES_EXPLAINED
from pace_ai.tools import analysis as analysis_mod
from pace_ai.tools import environment as env_mod
from pace_ai.tools import goals as goals_mod
from pace_ai.tools import run_analysis as run_mod

settings = Settings.from_env()
goal_db = GoalDB(settings.db_path)


def _parse_json(raw: str, name: str = "input") -> Any:
    """Parse a JSON string with a clear error message on failure."""
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        return {"error": "invalid_json", "parameter": name, "message": f"Failed to parse {name}: {e}"}


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
    """Compute ACWR and load variability from weekly distance data.

    Uses the uncoupled method: chronic load excludes the acute week.

    Args:
        weekly_distances: Weekly distances in km (most recent last), minimum 5 weeks.
    """
    return analysis_mod.calculate_acwr(weekly_distances)


@mcp.tool()
async def predict_race_time(
    recent_race_distance: str,
    recent_race_time: str,
    target_distance: str,
    temperature_c: float | None = None,
    altitude_m: float | None = None,
) -> dict:
    """Predict race time using VDOT, Riegel, and Cameron models.

    Returns predictions from three models plus caveats about accuracy.
    Optionally adjusts predictions for heat and/or altitude conditions.

    Args:
        recent_race_distance: Distance of a recent race (e.g. "5k", "10k", "half marathon").
        recent_race_time: Finish time of that race (H:MM:SS or M:SS).
        target_distance: Target distance to predict (e.g. "marathon", "half marathon").
        temperature_c: Race-day temperature in Celsius (optional, applies heat slowdown).
        altitude_m: Race-day altitude in meters (optional, applies altitude slowdown).
    """
    return analysis_mod.predict_race_time(
        recent_race_distance,
        recent_race_time,
        target_distance,
        temperature_c=temperature_c,
        altitude_m=altitude_m,
    )


@mcp.tool()
async def calculate_training_zones(
    threshold_pace_per_km: str | None = None,
    threshold_hr: int | None = None,
    vdot: float | None = None,
) -> dict:
    """Calculate Daniels' training zones from threshold pace, heart rate, and/or VDOT.

    Args:
        threshold_pace_per_km: Threshold pace as M:SS per km (e.g. "4:30").
        threshold_hr: Threshold heart rate in bpm.
        vdot: VDOT value (computes zones using Daniels' %VO2max curve).
    """
    return analysis_mod.calculate_training_zones(
        threshold_pace_per_km=threshold_pace_per_km,
        threshold_hr=threshold_hr,
        vdot=vdot,
    )


@mcp.tool()
async def calculate_hr_zones_karvonen(max_hr: int, resting_hr: int) -> dict:
    """Calculate HR training zones using the Karvonen (Heart Rate Reserve) method.

    More accurate than %MaxHR for recreational runners because it accounts for
    individual resting heart rate. Use with field-tested max HR and morning resting HR.

    Args:
        max_hr: Maximum heart rate in bpm (from field test or 220-age estimate).
        resting_hr: Resting heart rate in bpm (measured upon waking).
    """
    return analysis_mod.calculate_hr_zones_karvonen(max_hr, resting_hr)


@mcp.tool()
async def analyze_training_load_daily(daily_distances: list[float]) -> dict:
    """Compute ACWR using EWMA from daily distance data with spike detection.

    More accurate than weekly ACWR — uses exponentially weighted moving averages
    and detects single-session spikes and consecutive hard days.

    Args:
        daily_distances: Daily distances in km (most recent last), minimum 28 days.
    """
    return analysis_mod.calculate_acwr_daily(daily_distances)


@mcp.tool()
async def calculate_cardiac_decoupling(
    hr_stream_json: str,
    velocity_stream_json: str,
    time_stream_json: str = "null",
) -> dict:
    """Calculate cardiac decoupling (pace:HR drift) between run halves.

    Compares the pace-to-HR ratio in the first and second halves of a run.
    <5% = excellent aerobic fitness, 5-10% = adequate, >10% = aerobic deficiency.
    Best used on steady easy/marathon-pace runs of 45+ minutes.

    Args:
        hr_stream_json: JSON array of HR data points (bpm) from get_activity_streams.
        velocity_stream_json: JSON array of velocity data points (m/s) from get_activity_streams.
        time_stream_json: JSON array of timestamps (optional, improves accuracy).
    """
    hr = _parse_json(hr_stream_json, "hr_stream_json")
    if isinstance(hr, dict) and hr.get("error") == "invalid_json":
        return hr
    vel = _parse_json(velocity_stream_json, "velocity_stream_json")
    if isinstance(vel, dict) and vel.get("error") == "invalid_json":
        return vel
    time_s = _parse_json(time_stream_json, "time_stream_json") if time_stream_json != "null" else None
    if isinstance(time_s, dict) and time_s.get("error") == "invalid_json":
        return time_s
    return run_mod.calculate_cardiac_decoupling(hr, vel, time_s)


# ── Run Analysis Tools ────────────────────────────────────────────────


@mcp.tool()
async def analyze_run(
    activity_json: str,
    streams_json: str = "null",
    athlete_zones_json: str = "null",
) -> dict:
    """Compute structured analysis of a single run.

    Returns HR drift, pace variability, time-in-zone, cadence assessment, and coaching flags.
    Pre-computes the numbers so Claude can focus on interpretation.

    Args:
        activity_json: JSON object of full activity detail from strava-mcp.
        streams_json: JSON object of activity streams (optional, enables HR analysis).
        athlete_zones_json: JSON object of athlete zones (optional, enables zone distribution).
    """
    activity = _parse_json(activity_json, "activity_json")
    if isinstance(activity, dict) and activity.get("error") == "invalid_json":
        return activity
    streams = _parse_json(streams_json, "streams_json") if streams_json != "null" else None
    if isinstance(streams, dict) and streams.get("error") == "invalid_json":
        return streams
    zones = _parse_json(athlete_zones_json, "athlete_zones_json") if athlete_zones_json != "null" else None
    if isinstance(zones, dict) and zones.get("error") == "invalid_json":
        return zones
    return run_mod.analyze_run(activity, streams, zones)


@mcp.tool()
async def detect_workout_type(activity_json: str, streams_json: str = "null") -> dict:
    """Auto-classify workout type from laps, pace, and HR patterns.

    Detects: easy_run, long_run, tempo, intervals, race, recovery, progression.
    More accurate than Strava's workout_type field (which is usually left as default).

    Args:
        activity_json: JSON object of full activity detail from strava-mcp.
        streams_json: JSON object of activity streams (optional).
    """
    activity = _parse_json(activity_json, "activity_json")
    if isinstance(activity, dict) and activity.get("error") == "invalid_json":
        return activity
    streams = _parse_json(streams_json, "streams_json") if streams_json != "null" else None
    if isinstance(streams, dict) and streams.get("error") == "invalid_json":
        return streams
    return run_mod.detect_workout_type(activity, streams)


@mcp.tool()
async def get_training_distribution(
    activities_json: str,
    athlete_zones_json: str = "null",
) -> dict:
    """Classify runs by intensity and assess training polarization.

    Answers: "Am I doing 80/20? Am I running my easy runs easy enough?"
    Uses HR data when available, falls back to suffer_score or pace heuristics.

    Args:
        activities_json: JSON array of recent activities from strava-mcp.
        athlete_zones_json: JSON object of athlete HR zones (optional).
    """
    activities = _parse_json(activities_json, "activities_json")
    if isinstance(activities, dict) and activities.get("error") == "invalid_json":
        return activities
    zones = _parse_json(athlete_zones_json, "athlete_zones_json") if athlete_zones_json != "null" else None
    if isinstance(zones, dict) and zones.get("error") == "invalid_json":
        return zones
    return run_mod.get_training_distribution(activities, zones)


@mcp.tool()
async def assess_fitness_trend(
    best_efforts_json: str,
    weekly_summaries_json: str,
) -> dict:
    """Assess fitness trend from best efforts and weekly training data.

    Computes VDOT from best efforts, volume trends, and consistency metrics.
    Answers: "Am I actually getting faster? Am I training consistently?"

    Args:
        best_efforts_json: JSON array from strava-mcp get_best_efforts.
        weekly_summaries_json: JSON array from strava-mcp get_weekly_summary.
    """
    best_efforts = _parse_json(best_efforts_json, "best_efforts_json")
    if isinstance(best_efforts, dict) and best_efforts.get("error") == "invalid_json":
        return best_efforts
    weekly_summaries = _parse_json(weekly_summaries_json, "weekly_summaries_json")
    if isinstance(weekly_summaries, dict) and weekly_summaries.get("error") == "invalid_json":
        return weekly_summaries
    return run_mod.assess_fitness_trend(best_efforts=best_efforts, weekly_summaries=weekly_summaries)


@mcp.tool()
async def assess_race_readiness_tool(
    goals_json: str,
    best_efforts_json: str,
    weekly_summaries_json: str,
    training_load_json: str = "null",
) -> dict:
    """Compute structured race readiness scores.

    Evaluates VDOT alignment with goal, volume adequacy, long run readiness,
    consistency, and training load. Returns per-goal scores with specific strengths/risks.

    Args:
        goals_json: JSON array of goals from pace-ai get_goals.
        best_efforts_json: JSON array from strava-mcp get_best_efforts.
        weekly_summaries_json: JSON array from strava-mcp get_weekly_summary.
        training_load_json: JSON object of ACWR analysis (optional).
    """
    goals = _parse_json(goals_json, "goals_json")
    if isinstance(goals, dict) and goals.get("error") == "invalid_json":
        return goals
    best_efforts = _parse_json(best_efforts_json, "best_efforts_json")
    if isinstance(best_efforts, dict) and best_efforts.get("error") == "invalid_json":
        return best_efforts
    weekly_summaries = _parse_json(weekly_summaries_json, "weekly_summaries_json")
    if isinstance(weekly_summaries, dict) and weekly_summaries.get("error") == "invalid_json":
        return weekly_summaries
    training_load = _parse_json(training_load_json, "training_load_json") if training_load_json != "null" else None
    if isinstance(training_load, dict) and training_load.get("error") == "invalid_json":
        return training_load
    return run_mod.assess_race_readiness(
        goals=goals,
        best_efforts=best_efforts,
        weekly_summaries=weekly_summaries,
        training_load=training_load,
    )


@mcp.tool()
async def detect_anomalies(
    activity_json: str,
    streams_json: str = "null",
) -> dict:
    """Detect data quality issues in an activity.

    Flags GPS glitches, HR sensor failures, pace outliers, and missing data.
    Returns a quality score (0-10) and whether the data is usable for coaching.

    Args:
        activity_json: JSON object of full activity detail from strava-mcp.
        streams_json: JSON object of activity streams (optional, improves HR checks).
    """
    activity = _parse_json(activity_json, "activity_json")
    if isinstance(activity, dict) and activity.get("error") == "invalid_json":
        return activity
    streams = _parse_json(streams_json, "streams_json") if streams_json != "null" else None
    if isinstance(streams, dict) and streams.get("error") == "invalid_json":
        return streams
    return run_mod.detect_anomalies(activity, streams)


# ── Environment Tools ─────────────────────────────────────────────────


@mcp.tool()
async def calculate_heat_adjustment(
    temperature_f: float | None = None,
    temperature_c: float | None = None,
    dew_point_f: float | None = None,
    dew_point_c: float | None = None,
) -> dict:
    """Calculate pace adjustment for heat and humidity.

    Answers: "How much should I slow down in the heat?"
    Returns slowdown percentage, adjusted effort guidance, and risk level.

    Args:
        temperature_f: Temperature in Fahrenheit.
        temperature_c: Temperature in Celsius.
        dew_point_f: Dew point in Fahrenheit (improves accuracy).
        dew_point_c: Dew point in Celsius (improves accuracy).
    """
    return env_mod.calculate_heat_adjustment(
        temperature_f=temperature_f,
        temperature_c=temperature_c,
        dew_point_f=dew_point_f,
        dew_point_c=dew_point_c,
    )


@mcp.tool()
async def calculate_altitude_adjustment(
    altitude_ft: float | None = None,
    altitude_m: float | None = None,
) -> dict:
    """Calculate pace adjustment for altitude.

    Answers: "How much slower should I run at altitude?"
    Returns slowdown percentage, VO2max reduction, and acclimatization guidance.

    Args:
        altitude_ft: Altitude in feet.
        altitude_m: Altitude in meters.
    """
    return env_mod.calculate_altitude_adjustment(altitude_ft=altitude_ft, altitude_m=altitude_m)


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


@mcp.resource("coaching://field-test-protocols")
async def field_test_protocols_resource() -> str:
    """LTHR, MaxHR, and Resting HR field test protocols for establishing accurate training zones."""
    return FIELD_TEST_PROTOCOLS


# ── Entry Point ────────────────────────────────────────────────────────


def main() -> None:
    """Entry point for the pace-ai server."""
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
