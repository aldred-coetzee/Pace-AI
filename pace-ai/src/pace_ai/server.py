"""FastMCP server for running coaching intelligence."""

from __future__ import annotations

import json
from typing import Any

from mcp.server.fastmcp import FastMCP

from pace_ai.config import Settings
from pace_ai.database import GoalDB, HistoryDB
from pace_ai.prompts.coaching import (
    injury_risk_prompt,
    race_readiness_prompt,
    run_analysis_prompt,
    weekly_plan_prompt,
)
from pace_ai.resources.claim_store import query_claims
from pace_ai.resources.methodology import FIELD_TEST_PROTOCOLS, METHODOLOGY, ZONES_EXPLAINED
from pace_ai.tools import analysis as analysis_mod
from pace_ai.tools import environment as env_mod
from pace_ai.tools import goals as goals_mod
from pace_ai.tools import history as history_mod
from pace_ai.tools import memory as memory_mod
from pace_ai.tools import profile as profile_mod
from pace_ai.tools import run_analysis as run_mod
from pace_ai.tools import sync as sync_mod

settings = Settings.from_env()
goal_db = GoalDB(settings.db_path)
history_db = HistoryDB(settings.db_path)


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


# ── Evidence Tools ─────────────────────────────────────────────────────


@mcp.tool()
async def get_coaching_claims(
    category: str,
    population: str,
    limit: int = 20,
) -> list[dict]:
    """Query evidence-backed coaching claims from the research database.

    Returns ranked claims from peer-reviewed research, scored by population
    relevance. Use specific category names matching research domains
    (e.g. "training_load_acwr", "polarized_training", "taper_science").

    Args:
        category: Research category to query (e.g. "training_load_acwr", "periodisation").
            Use comma-separated values to query multiple categories.
        population: Target population for relevance scoring (e.g. "recreational runners",
            "elite athletes"). Claims matching exactly score highest.
        limit: Maximum number of claims to return (default 20).
    """
    categories = [c.strip() for c in category.split(",")]
    return query_claims(categories, population, limit)


# ── Sync Tools ─────────────────────────────────────────────────────────


@mcp.tool()
async def sync_strava(activities_json: str) -> dict:
    """Sync Strava activities into the central history store.

    Accepts a JSON array of raw activities from strava-mcp get_recent_activities.
    Upserts into activities table, auto-detects races, calculates VDOT, marks PBs.

    Args:
        activities_json: JSON array of Strava activity objects.
    """
    activities = _parse_json(activities_json, "activities_json")
    if isinstance(activities, dict) and activities.get("error") == "invalid_json":
        return activities
    return sync_mod.sync_strava(history_db, activities)


@mcp.tool()
async def sync_garmin_wellness(wellness_json: str) -> dict:
    """Sync Garmin wellness snapshots into the central history store.

    Args:
        wellness_json: JSON array of daily wellness snapshot objects from garmin-mcp.
    """
    data = _parse_json(wellness_json, "wellness_json")
    if isinstance(data, dict) and data.get("error") == "invalid_json":
        return data
    return sync_mod.sync_garmin_wellness(history_db, data)


@mcp.tool()
async def sync_withings(measurements_json: str) -> dict:
    """Sync Withings body measurements into the central history store.

    Args:
        measurements_json: JSON array of measurement objects from withings-mcp.
    """
    data = _parse_json(measurements_json, "measurements_json")
    if isinstance(data, dict) and data.get("error") == "invalid_json":
        return data
    return sync_mod.sync_withings(history_db, data)


@mcp.tool()
async def sync_notion(entries_json: str) -> dict:
    """Sync Notion diary entries into the central history store.

    Args:
        entries_json: JSON array of diary entry objects from notion-mcp.
    """
    data = _parse_json(entries_json, "entries_json")
    if isinstance(data, dict) and data.get("error") == "invalid_json":
        return data
    return sync_mod.sync_notion(history_db, data)


@mcp.tool()
async def sync_garmin_workouts(workouts_json: str) -> dict:
    """Sync Garmin scheduled workouts into the central history store.

    Matches completed workouts against activities by date and sport type.

    Args:
        workouts_json: JSON array of scheduled workout objects from garmin-mcp.
    """
    data = _parse_json(workouts_json, "workouts_json")
    if isinstance(data, dict) and data.get("error") == "invalid_json":
        return data
    return sync_mod.sync_garmin_workouts(history_db, data)


@mcp.tool()
async def get_sync_status() -> list[dict]:
    """Get sync status summary — last sync time and record counts per source."""
    return sync_mod.get_sync_status(history_db)


@mcp.tool()
async def sync_all() -> dict:
    """Incremental sync from all data sources (Strava, Garmin, Withings, Notion).

    Fetches only data newer than the last successful sync per source.
    Continues if any single source fails. Call at the start of each coaching session
    to ensure the history store is up to date.
    """
    return await sync_mod.sync_all(history_db)


# ── Coaching Memory Tools ─────────────────────────────────────────────


@mcp.tool()
async def append_coaching_log(entry_json: str) -> dict:
    """Record what happened in a coaching session.

    Append-only log. Call at the end of every coaching session.

    Args:
        entry_json: JSON object with required 'summary' and optional:
            prescriptions (list of strings), workout_ids (list), acwr, weekly_km,
            body_battery, stress_level, notion_stress, notion_niggles, follow_up.
    """
    entry = _parse_json(entry_json, "entry_json")
    if isinstance(entry, dict) and entry.get("error") == "invalid_json":
        return entry
    return memory_mod.append_coaching_log(history_db, entry)


@mcp.tool()
async def get_coaching_context() -> dict | None:
    """Get the current coaching context — active situation, concerns, and plan.

    Returns None if no context has been set yet. In that case, generate initial
    context from recent coaching log entries and athlete profile.
    """
    return memory_mod.get_coaching_context(history_db)


@mcp.tool()
async def update_coaching_context(content: str) -> dict:
    """Rewrite the coaching context with current situation and active plan.

    Call at the end of every coaching session. Hard limit: 2000 words.

    Args:
        content: Rich text summarising the current coaching situation.
    """
    try:
        return memory_mod.update_coaching_context(history_db, content)
    except ValueError as e:
        return {"error": "word_limit_exceeded", "message": str(e)}


@mcp.tool()
async def search_coaching_log(query: str, limit: int = 10) -> list[dict]:
    """Search past coaching sessions by keyword.

    Use when recalling specific past discussions, protocols, or decisions.
    Searches across summary and prescriptions fields.

    Args:
        query: Search term (e.g. "eccentric heel drops", "achilles", "long run").
        limit: Max results (default 10).
    """
    return memory_mod.search_coaching_log(history_db, query, limit)


@mcp.tool()
async def get_recent_coaching_log(limit: int = 5) -> list[dict]:
    """Get the most recent coaching session logs.

    Call at the start of each session to review recent history.

    Args:
        limit: Number of entries to return (default 5).
    """
    return memory_mod.get_recent_coaching_log(history_db, limit)


@mcp.tool()
async def add_athlete_fact(category: str, fact: str, source_log_id: int | None = None) -> dict:
    """Record a permanent fact about the athlete.

    Use for insights that should persist indefinitely — injury patterns,
    training responses, goals, preferences.

    Args:
        category: One of 'injury', 'training_response', 'goal', 'preference', 'nutrition', 'other'.
        fact: Plain text description.
        source_log_id: Optional coaching_log id this fact came from.
    """
    try:
        return memory_mod.add_athlete_fact(history_db, category, fact, source_log_id)
    except ValueError as e:
        return {"error": "invalid_category", "message": str(e)}


@mcp.tool()
async def get_athlete_facts(category: str | None = None) -> list[dict]:
    """Get all active athlete facts, optionally filtered by category.

    Call at session start for permanent context about the athlete.

    Args:
        category: Optional filter — 'injury', 'training_response', 'goal', 'preference', 'nutrition', 'other'.
    """
    try:
        return memory_mod.get_athlete_facts(history_db, category)
    except ValueError as e:
        return {"error": "invalid_category", "message": str(e)}


@mcp.tool()
async def update_athlete_fact(fact_id: int, fact: str) -> dict:
    """Update an existing athlete fact.

    Use when a fact changes (e.g. "Achilles tendinopathy — unresolved" → "Achilles — resolving").

    Args:
        fact_id: ID of the fact to update.
        fact: New text for the fact.
    """
    result = memory_mod.update_athlete_fact(history_db, fact_id, fact)
    if result is None:
        return {"error": "not_found", "message": f"No athlete fact with id {fact_id}"}
    return result


# ── History Query Tools ────────────────────────────────────────────────


@mcp.tool()
async def get_weekly_distances(weeks: int = 12, sport_type: str = "run") -> list[dict]:
    """Get weekly distance totals from the local history store.

    Used by ACWR calculation — replaces Claude having to pass weekly arrays.

    Args:
        weeks: Number of weeks to look back (default 12).
        sport_type: Sport type filter (default "run").
    """
    return history_mod.get_weekly_distances(history_db, weeks=weeks, sport_type=sport_type)


@mcp.tool()
async def get_recent_activities_local(days: int = 28, sport_type: str | None = None) -> list[dict]:
    """Get recent activities from the local history store.

    Much faster than calling strava-mcp. Requires prior sync_strava call.

    Args:
        days: Number of days to look back (default 28).
        sport_type: Optional filter (e.g. "run", "ride").
    """
    return history_mod.get_recent_activities(history_db, days=days, sport_type=sport_type)


@mcp.tool()
async def get_recent_wellness(days: int = 14) -> list[dict]:
    """Get recent Garmin wellness snapshots from the local store.

    Args:
        days: Number of days to look back (default 14).
    """
    return history_mod.get_recent_wellness(history_db, days=days)


@mcp.tool()
async def get_recent_diary(days: int = 28) -> list[dict]:
    """Get recent diary entries from the local store.

    Args:
        days: Number of days to look back (default 28).
    """
    return history_mod.get_recent_diary(history_db, days=days)


@mcp.tool()
async def get_race_history(limit: int = 10) -> list[dict]:
    """Get race results ordered by date, most recent first.

    Args:
        limit: Max number of results (default 10).
    """
    return history_mod.get_race_history(history_db, limit=limit)


@mcp.tool()
async def get_pbs() -> list[dict]:
    """Get personal bests — fastest time per distance label."""
    return history_mod.get_pbs(history_db)


# ── Profile Tools ──────────────────────────────────────────────────────


@mcp.tool()
async def generate_athlete_profile() -> dict:
    """Auto-generate athlete profile from all synced history data.

    Computes VDOT, weekly volume, easy pace, training age, weight trends,
    resting HR baseline, and HRV baseline. Call after syncing data sources.
    """
    return profile_mod.generate_athlete_profile(history_db)


@mcp.tool()
async def get_athlete_profile() -> dict | None:
    """Get the current athlete profile, or null if not yet generated."""
    return profile_mod.get_athlete_profile(history_db)


@mcp.tool()
async def update_athlete_profile_manual(fields_json: str) -> dict:
    """Update manually-entered athlete profile fields.

    Cannot overwrite auto-derived fields. Allowed: date_of_birth, gender,
    experience_level, injury_history, preferred_long_run_day,
    available_days_per_week, notes.

    Args:
        fields_json: JSON object of field names to values.
    """
    fields = _parse_json(fields_json, "fields_json")
    if isinstance(fields, dict) and fields.get("error") == "invalid_json":
        return fields
    return profile_mod.update_athlete_profile_manual(history_db, fields)


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
    import os

    mcp.run(transport=os.environ.get("MCP_TRANSPORT", "streamable-http"))


if __name__ == "__main__":
    main()
