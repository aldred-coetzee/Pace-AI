"""Coaching prompt templates for structured, repeatable advice.

Each prompt defines:
- description: What the prompt does (shown to the user)
- arguments: What Claude should provide (fetched from strava-mcp)
- template: The coaching framework that guides Claude's reasoning

The prompts inject the coaching methodology (from resources/methodology.py) as
reference material. This is a RAG-like pattern: the methodology is the knowledge
base, the prompt teaches the model how to apply it, and the model reasons about
the specific athlete. When research changes, update the methodology — not these
prompts.
"""

from __future__ import annotations

from pace_ai.resources.methodology import METHODOLOGY


def weekly_plan_prompt(
    goals: list[dict],
    recent_activities: list[dict],
    athlete_stats: dict,
    training_zones: dict | None = None,
    training_load: dict | None = None,
    athlete_context: dict | None = None,
) -> str:
    """Generate a weekly training plan prompt.

    Args:
        goals: Current training goals from pace-ai.
        recent_activities: Last 4 weeks of activities from strava-mcp.
        athlete_stats: Athlete statistics from strava-mcp.
        training_zones: Optional zone definitions.
        training_load: Optional ACWR analysis from analyze_training_load.
        athlete_context: Optional dict with age, gender, experience level, condition.
    """
    goals_text = _format_goals(goals) if goals else "No goals set."
    activities_text = _format_recent_activities(recent_activities)
    stats_text = _format_stats(athlete_stats)
    zones_text = _format_zones(training_zones) if training_zones else "No zone data available."
    load_text = _format_training_load(training_load) if training_load else "No load analysis available."
    context_text = _format_athlete_context(athlete_context) if athlete_context else ""

    context_section = (
        f"""
## Athlete Context
{context_text}
"""
        if context_text
        else ""
    )

    return f"""You are a running coach designing next week's training plan.
{context_section}
## Current Goals
{goals_text}

## Recent Training (last 4 weeks)
{activities_text}

## Athlete Statistics
{stats_text}

## Training Zones
{zones_text}

## Training Load Analysis
{load_text}

## Coaching Methodology Reference
{METHODOLOGY}

## Instructions
Apply the methodology above to this specific athlete. In particular:
1. Follow the **progressive overload**, **80/20**, and **recovery** principles.
2. Align key sessions with the **goal race distance** (specificity).
3. Apply the **population-specific guidelines** and **ACWR action thresholds** \
that match this athlete's age, experience, condition, and training load.
4. If the methodology flags concerns for this athlete's profile, address them \
in the safety notes.

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
- **Safety notes**: Any concerns about the athlete's current training load, condition, or recovery needs
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
    training_zones: dict | None = None,
    race_prediction: dict | None = None,
) -> str:
    """Generate a race readiness assessment prompt.

    Args:
        goals: Current goals (especially the target race).
        recent_activities: Recent training data from strava-mcp.
        athlete_stats: Athlete statistics from strava-mcp.
        training_load: Optional ACWR analysis.
        training_zones: Optional zone definitions from VDOT.
        race_prediction: Optional VDOT-based race prediction.
    """
    goals_text = _format_goals(goals) if goals else "No goals set."
    activities_text = _format_recent_activities(recent_activities)
    stats_text = _format_stats(athlete_stats)
    load_text = _format_training_load(training_load) if training_load else "No load analysis available."
    zones_text = _format_zones(training_zones) if training_zones else "No zone data available."
    prediction_text = _format_race_prediction(race_prediction) if race_prediction else "No race prediction available."

    return f"""You are a running coach assessing race readiness.

## Target Race
{goals_text}

## Recent Training
{activities_text}

## Athlete Statistics
{stats_text}

## Training Load Analysis
{load_text}

## Training Zones
{zones_text}

## Race Prediction (VDOT-based)
{prediction_text}

## Coaching Methodology Reference
{METHODOLOGY}

## Assessment Framework
Using the methodology above, evaluate readiness based on:
1. **Volume adequacy**: Has weekly mileage been sufficient for the goal distance?
2. **Key workouts**: Has the athlete completed race-specific workouts at or near goal pace?
3. **Consistency**: How many weeks of consistent training in the last 8 weeks?
4. **Taper**: Is the current training load appropriate for the time until race day?
5. **VDOT/Riegel check**: Compare the goal time against the VDOT-based prediction.
6. **Population factors**: Apply the population-specific guidelines from the methodology.

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

## Coaching Methodology Reference
{METHODOLOGY}

## Risk Assessment Framework
Using the methodology above (especially the Injury Prevention Red Flags and ACWR Action
Thresholds sections), evaluate based on:
1. **10% rule**: Flag any weeks that exceeded the guideline.
2. **ACWR**: Apply the action thresholds from the methodology.
3. **Load variability**: Week-to-week consistency of the chronic period.
4. **Pattern recognition**: Look for back-to-back high weeks, sudden drops, or erratic patterns.
5. **Population factors**: Apply the population-specific guidelines from the methodology.

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


def _format_athlete_context(context: dict) -> str:
    if not context:
        return ""
    lines = []
    if context.get("age"):
        lines.append(f"- Age: {context['age']}")
    if context.get("gender"):
        lines.append(f"- Gender: {context['gender']}")
    if context.get("level"):
        lines.append(f"- Experience level: {context['level']}")
    if context.get("condition"):
        lines.append(f"- Current condition: {context['condition']}")
    if context.get("description"):
        lines.append(f"- Notes: {context['description']}")
    return "\n".join(lines)


def _format_race_prediction(prediction: dict) -> str:
    if not prediction:
        return "No prediction available."
    lines = [
        f"- VDOT: {prediction.get('vdot', 'N/A')}",
        f"- Predicted time: {prediction.get('predicted_time', 'N/A')}",
    ]
    source = prediction.get("source_race")
    if source:
        lines.append(f"- Based on: {source.get('distance', '?')} in {source.get('time', '?')}")
    target = prediction.get("target_distance")
    if target:
        lines.append(f"- Target distance: {target}")
    return "\n".join(lines)


def _format_zones(zones: dict) -> str:
    if not zones or "zones" not in zones:
        return "No zone data."
    lines = []
    for name, data in zones["zones"].items():
        pace = data.get("pace_range_per_km", "N/A")
        hr = data.get("hr_range_bpm", "N/A")
        lines.append(f"- **{name}**: pace {pace}/km, HR {hr}")
    return "\n".join(lines)
