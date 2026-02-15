"""Coaching prompt templates for structured, repeatable advice.

Each prompt defines:
- description: What the prompt does (shown to the user)
- arguments: What Claude should provide (fetched from strava-mcp)
- template: The coaching framework that guides Claude's reasoning
"""

from __future__ import annotations


def weekly_plan_prompt(
    goals: list[dict],
    recent_activities: list[dict],
    athlete_stats: dict,
    training_zones: dict | None = None,
) -> str:
    """Generate a weekly training plan prompt.

    Args:
        goals: Current training goals from pace-ai.
        recent_activities: Last 4 weeks of activities from strava-mcp.
        athlete_stats: Athlete statistics from strava-mcp.
        training_zones: Optional zone definitions.
    """
    goals_text = _format_goals(goals) if goals else "No goals set."
    activities_text = _format_recent_activities(recent_activities)
    stats_text = _format_stats(athlete_stats)
    zones_text = _format_zones(training_zones) if training_zones else "No zone data available."

    return f"""You are a running coach designing next week's training plan.

## Current Goals
{goals_text}

## Recent Training (last 4 weeks)
{activities_text}

## Athlete Statistics
{stats_text}

## Training Zones
{zones_text}

## Coaching Framework
Apply these principles:
1. **Progressive overload**: Increase weekly volume by no more than 10% from the recent average.
2. **80/20 polarised training**: ~80% of volume at easy pace, ~20% at moderate-to-hard effort.
3. **Recovery**: At least 1 full rest day per week. Easy days after hard days.
4. **Specificity**: Align key sessions with the primary goal race distance.

## Output Format
Provide a day-by-day plan for the upcoming week:

For each day:
- **Session type** (easy run, tempo, intervals, long run, rest, cross-train)
- **Distance** (km)
- **Target pace/effort** (zone or pace range)
- **Purpose** (why this session, what it develops)

End with:
- **Weekly total** (km)
- **Intensity distribution** (% easy / % moderate / % hard)
- **Key session of the week** and why it matters
"""


def run_analysis_prompt(
    activity: dict,
    streams: dict | None = None,
    goals: list[dict] | None = None,
) -> str:
    """Generate a run analysis prompt.

    Args:
        activity: Full activity detail from strava-mcp.
        streams: Optional time-series data (HR, pace, etc.).
        goals: Optional current goals for context.
    """
    activity_text = _format_activity_detail(activity)
    streams_text = _format_streams(streams) if streams else "No stream data available."
    goals_text = _format_goals(goals) if goals else "No goals set."

    return f"""You are a running coach analyzing a specific run.

## Run Data
{activity_text}

## Time-Series Data
{streams_text}

## Current Goals
{goals_text}

## Analysis Framework
Evaluate the run on:
1. **Pace consistency**: Look at split-to-split variation. A coefficient of variation (CV) under 5% is good.
2. **Heart rate drift**: Compare first-half vs second-half average HR at similar pace. >5% drift suggests fatigue.
3. **Effort distribution**: Was the effort appropriate for the session type?
4. **Cadence**: Optimal running cadence is typically 170-185 spm. Note any significant deviation.

## Output Format
Provide:
- **Summary**: One-sentence assessment of the run.
- **What went well**: 2-3 specific positives with data support.
- **What to improve**: 1-2 specific areas with actionable suggestions.
- **Training context**: How this run fits the current training block and goals.
"""


def race_readiness_prompt(
    goals: list[dict],
    recent_activities: list[dict],
    athlete_stats: dict,
    training_load: dict | None = None,
) -> str:
    """Generate a race readiness assessment prompt.

    Args:
        goals: Current goals (especially the target race).
        recent_activities: Recent training data from strava-mcp.
        athlete_stats: Athlete statistics from strava-mcp.
        training_load: Optional ACWR analysis.
    """
    goals_text = _format_goals(goals) if goals else "No goals set."
    activities_text = _format_recent_activities(recent_activities)
    stats_text = _format_stats(athlete_stats)
    load_text = _format_training_load(training_load) if training_load else "No load analysis available."

    return f"""You are a running coach assessing race readiness.

## Target Race
{goals_text}

## Recent Training
{activities_text}

## Athlete Statistics
{stats_text}

## Training Load Analysis
{load_text}

## Assessment Framework
Evaluate readiness based on:
1. **Volume adequacy**: Has weekly mileage been sufficient for the goal distance?
   (Peak week: 2-3x race distance for half marathon, 1.5-2x for marathon.)
2. **Key workouts**: Has the athlete completed race-specific workouts at or near goal pace?
3. **Consistency**: How many weeks of consistent training in the last 8 weeks?
4. **Taper**: Is the current training load appropriate for the time until race day?
5. **VDOT/Riegel check**: Based on recent performances, is the goal time realistic?

## Output Format
Provide:
- **Readiness score**: 1-10 with brief justification.
- **Strengths**: What's working in the preparation.
- **Risks**: What concerns you.
- **Recommendations**: Specific adjustments for the remaining time before the race.
"""


def injury_risk_prompt(
    weekly_distances: list[float],
    training_load: dict,
    recent_activities: list[dict] | None = None,
) -> str:
    """Generate an injury risk assessment prompt.

    Args:
        weekly_distances: Weekly mileage for the last 8+ weeks.
        training_load: ACWR analysis from analyze_training_load.
        recent_activities: Optional recent activity details.
    """
    distances_text = "\n".join(f"  Week {i + 1}: {d:.1f} km" for i, d in enumerate(weekly_distances))
    load_text = _format_training_load(training_load)
    activities_text = (
        _format_recent_activities(recent_activities) if recent_activities else "No detailed activity data."
    )

    return f"""You are a running coach assessing injury risk from training load patterns.

## Weekly Mileage (oldest to newest)
{distances_text}

## Training Load Analysis
{load_text}

## Recent Activities
{activities_text}

## Risk Assessment Framework
Evaluate based on:
1. **10% rule**: Weekly mileage increases should not exceed 10%. Flag any weeks that exceeded this.
2. **ACWR**: Acute:chronic workload ratio (uncoupled method). Optimal: 0.8-1.3. Elevated risk: >1.3. High risk: >1.5.
3. **Load variability**: Week-to-week consistency of the chronic period (coefficient of variation).
   Low CV (<0.1) = very consistent. High CV (>0.3) = erratic loading pattern worth investigating.
4. **Pattern recognition**: Look for back-to-back high weeks, sudden drops, or erratic patterns.

## Output Format
Provide:
- **Risk level**: Low / Moderate / Elevated / High — with specific data supporting the assessment.
- **Specific concerns**: Cite the exact weeks or patterns that are problematic.
- **Recommendations**: Concrete adjustments (e.g., "reduce next week to X km", "add a recovery week").
"""


# ── Formatting helpers ───────────────────────────────────────────────


def _format_goals(goals: list[dict]) -> str:
    if not goals:
        return "No goals set."
    lines = []
    for g in goals:
        time_str = g.get("target_time_formatted", str(g.get("target_time_seconds", "?")))
        line = f"- **{g['race_type']}** in {time_str}"
        if g.get("race_date"):
            line += f" (race date: {g['race_date']})"
        if g.get("notes"):
            line += f" — {g['notes']}"
        lines.append(line)
    return "\n".join(lines)


def _format_recent_activities(activities: list[dict]) -> str:
    if not activities:
        return "No recent activities."
    lines = []
    for a in activities:
        dist = a.get("distance_km", a.get("distance", 0) / 1000 if a.get("distance") else 0)
        pace = a.get("pace_min_per_km", "N/A")
        hr = a.get("average_heartrate", "N/A")
        lines.append(
            f"- {a.get('start_date', 'unknown date')}: {a.get('name', 'Untitled')}"
            f" -- {dist:.1f} km, pace {pace}/km, HR {hr}"
        )
    return "\n".join(lines)


def _format_activity_detail(activity: dict) -> str:
    lines = [
        f"**{activity.get('name', 'Untitled')}** — {activity.get('type', 'Run')}",
        f"Date: {activity.get('start_date', 'unknown')}",
        f"Distance: {activity.get('distance', 0) / 1000:.2f} km",
        f"Moving time: {activity.get('moving_time', 0) // 60}:{activity.get('moving_time', 0) % 60:02d}",
        f"Elapsed time: {activity.get('elapsed_time', 0) // 60}:{activity.get('elapsed_time', 0) % 60:02d}",
        f"Elevation gain: {activity.get('total_elevation_gain', 0)} m",
        f"Average HR: {activity.get('average_heartrate', 'N/A')} bpm",
        f"Max HR: {activity.get('max_heartrate', 'N/A')} bpm",
        f"Average cadence: {activity.get('average_cadence', 'N/A')} spm",
    ]

    splits = activity.get("splits_metric", [])
    if splits:
        lines.append("\n**Splits (per km):**")
        for s in splits:
            split_pace_s = s.get("moving_time", s.get("elapsed_time", 0))
            m, sec = divmod(split_pace_s, 60)
            hr = s.get("average_heartrate", "N/A")
            lines.append(f"  km {s.get('split', '?')}: {m}:{sec:02d} — HR {hr}")

    return "\n".join(lines)


def _format_streams(streams: dict) -> str:
    if not streams:
        return "No stream data."
    lines = []
    for key, data in streams.items():
        n = len(data) if isinstance(data, list) else 0
        lines.append(f"- **{key}**: {n} data points")
    return "\n".join(lines)


def _format_stats(stats: dict) -> str:
    lines = []
    for period in ["recent_run_totals", "ytd_run_totals", "all_run_totals"]:
        if period in stats:
            s = stats[period]
            label = period.replace("_", " ").title()
            dist_km = s.get("distance", 0) / 1000
            lines.append(
                f"- **{label}**: {s.get('count', 0)} runs, {dist_km:.0f} km,"
                f" {s.get('elevation_gain', 0):.0f} m elevation"
            )
    return "\n".join(lines) if lines else "No statistics available."


def _format_training_load(load: dict) -> str:
    return (
        f"- ACWR: {load.get('acwr', 'N/A')}\n"
        f"- Risk level: {load.get('risk_level', 'N/A')}\n"
        f"- Acute load: {load.get('acute_load', 'N/A')} km\n"
        f"- Chronic load: {load.get('chronic_load', 'N/A')} km\n"
        f"- Load variability (CV): {load.get('load_variability_cv', 'N/A')}\n"
        f"- Interpretation: {load.get('interpretation', '')}"
    )


def _format_zones(zones: dict) -> str:
    if not zones or "zones" not in zones:
        return "No zone data."
    lines = []
    for name, data in zones["zones"].items():
        pace = data.get("pace_range_per_km", "N/A")
        hr = data.get("hr_range_bpm", "N/A")
        lines.append(f"- **{name}**: pace {pace}/km, HR {hr}")
    return "\n".join(lines)
