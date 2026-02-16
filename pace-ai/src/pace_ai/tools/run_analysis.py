"""Run-level analysis tools — HR drift, pacing, workout detection, training distribution."""

from __future__ import annotations

from typing import Any


def analyze_run(
    activity: dict[str, Any],
    streams: dict[str, list] | None = None,
    athlete_zones: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Compute structured analysis of a single run.

    Calculates HR drift, pace variability, time-in-zone distribution,
    effort appropriateness, split analysis, and cadence assessment.

    Args:
        activity: Full activity detail (from strava-mcp get_activity).
        streams: Optional time-series data keyed by type (heartrate, velocity_smooth, etc.).
        athlete_zones: Optional HR zone definitions (from strava-mcp get_athlete_zones).

    Returns:
        Structured analysis with computed metrics and coaching flags.
    """
    result: dict[str, Any] = {
        "activity_id": activity.get("id"),
        "name": activity.get("name", "Untitled"),
    }

    # ── Split analysis ────────────────────────────────────────────────
    splits = activity.get("splits_metric", [])
    if splits:
        split_paces = [s.get("moving_time", s.get("elapsed_time", 0)) for s in splits if s.get("distance", 0) > 500]
        if split_paces:
            avg_split = sum(split_paces) / len(split_paces)
            std_split = (sum((p - avg_split) ** 2 for p in split_paces) / len(split_paces)) ** 0.5
            cv = round(std_split / avg_split * 100, 1) if avg_split > 0 else 0

            # Positive/negative split detection
            mid = len(split_paces) // 2
            first_half_avg = sum(split_paces[:mid]) / mid if mid > 0 else 0
            second_half_avg = sum(split_paces[mid:]) / (len(split_paces) - mid) if len(split_paces) - mid > 0 else 0

            split_ratio = round(second_half_avg / first_half_avg, 3) if first_half_avg > 0 else 1.0

            result["pacing"] = {
                "split_count": len(split_paces),
                "average_split_seconds": round(avg_split, 1),
                "pace_cv_pct": cv,
                "pacing_grade": "excellent" if cv < 3 else "good" if cv < 5 else "uneven" if cv < 8 else "poor",
                "split_ratio": split_ratio,
                "split_type": "negative" if split_ratio < 0.98 else "even" if split_ratio < 1.02 else "positive",
            }

    # ── Heart rate analysis ───────────────────────────────────────────
    hr_stream = streams.get("heartrate", []) if streams else []
    if hr_stream and len(hr_stream) >= 10:
        mid = len(hr_stream) // 2
        first_half_hr = sum(hr_stream[:mid]) / mid
        second_half_hr = sum(hr_stream[mid:]) / (len(hr_stream) - mid)
        drift_pct = round((second_half_hr - first_half_hr) / first_half_hr * 100, 1) if first_half_hr > 0 else 0

        result["hr_analysis"] = {
            "average_hr": round(sum(hr_stream) / len(hr_stream), 1),
            "max_hr": max(hr_stream),
            "min_hr": min(hr_stream),
            "first_half_avg_hr": round(first_half_hr, 1),
            "second_half_avg_hr": round(second_half_hr, 1),
            "cardiac_drift_pct": drift_pct,
            "drift_assessment": (
                "normal" if abs(drift_pct) < 3 else "mild_drift" if abs(drift_pct) < 5 else "significant_drift"
            ),
        }

        # Time-in-zone analysis
        if athlete_zones and "heart_rate" in athlete_zones:
            zones = athlete_zones["heart_rate"].get("zones", [])
            if zones:
                zone_times = _compute_time_in_zones(hr_stream, zones, streams.get("time"))
                result["zone_distribution"] = zone_times

    # ── Cadence analysis ──────────────────────────────────────────────
    cadence_stream = streams.get("cadence", []) if streams else []
    avg_cadence = activity.get("average_cadence")
    if avg_cadence:
        # Strava stores cadence as half-cycles; double for steps per minute
        spm = avg_cadence * 2 if avg_cadence < 120 else avg_cadence
        result["cadence"] = {
            "average_spm": round(spm, 1),
            "assessment": "low" if spm < 160 else "normal" if spm < 185 else "high",
        }
    elif cadence_stream:
        spm_values = [c * 2 if c < 120 else c for c in cadence_stream if c > 0]
        if spm_values:
            avg = sum(spm_values) / len(spm_values)
            result["cadence"] = {
                "average_spm": round(avg, 1),
                "assessment": "low" if avg < 160 else "normal" if avg < 185 else "high",
            }

    # ── Effort flags ──────────────────────────────────────────────────
    flags = []
    if "hr_analysis" in result and result["hr_analysis"]["cardiac_drift_pct"] > 5:
        flags.append("High cardiac drift suggests the run was harder than intended or dehydration occurred.")
    if "pacing" in result and result["pacing"]["pacing_grade"] == "poor":
        flags.append("Pacing was inconsistent. Consider more even effort distribution.")
    if "pacing" in result and result["pacing"]["split_type"] == "positive" and result["pacing"]["split_ratio"] > 1.05:
        flags.append("Significant positive split — started too fast. Practice even pacing.")
    if "zone_distribution" in result:
        easy_pct = sum(z["time_pct"] for z in result["zone_distribution"] if z["zone_index"] <= 2)
        if easy_pct < 50 and activity.get("workout_type", 0) == 0:
            flags.append(f"Only {easy_pct:.0f}% of time in zones 1-2. If this was an easy run, slow down.")

    result["flags"] = flags

    # ── HR reliability warnings ────────────────────────────────────────
    hr_warnings = _assess_hr_reliability(activity, streams)
    if hr_warnings:
        result["hr_reliability_warnings"] = hr_warnings

    return result


def detect_workout_type(
    activity: dict[str, Any],
    streams: dict[str, list] | None = None,
) -> dict[str, Any]:
    """Auto-classify workout type from laps, pace, and HR patterns.

    Detects: easy_run, long_run, tempo, intervals, race, recovery, progression.

    Args:
        activity: Full activity detail (with laps and splits).
        streams: Optional time-series data.

    Returns:
        Detected type, confidence, and breakdown (e.g. interval segments).
    """
    distance_m = activity.get("distance", 0)
    moving_time_s = activity.get("moving_time", 0)
    laps = activity.get("laps", [])
    splits = activity.get("splits_metric", [])
    workout_type = activity.get("workout_type", 0)

    # If user explicitly marked it
    if workout_type == 1:
        return {"detected_type": "race", "confidence": "high", "source": "user_tagged"}

    avg_speed = distance_m / moving_time_s if moving_time_s > 0 else 0
    distance_km = distance_m / 1000

    # Interval detection: multiple laps with large pace variance
    if len(laps) >= 4:
        lap_speeds = [lp.get("average_speed", 0) for lp in laps if lp.get("distance", 0) > 100]
        if lap_speeds and len(lap_speeds) >= 4:
            avg = sum(lap_speeds) / len(lap_speeds)
            variance = sum((s - avg) ** 2 for s in lap_speeds) / len(lap_speeds)
            cv = (variance**0.5) / avg * 100 if avg > 0 else 0

            if cv > 15:
                # Separate work and rest laps
                work_laps = [lp for lp in laps if lp.get("average_speed", 0) > avg]
                rest_laps = [lp for lp in laps if lp.get("average_speed", 0) <= avg]

                work_distances = [lp.get("distance", 0) for lp in work_laps]
                work_times = [lp.get("moving_time", 0) for lp in work_laps]

                avg_rest = (
                    round(sum(lp.get("moving_time", 0) for lp in rest_laps) / len(rest_laps), 0) if rest_laps else 0
                )
                return {
                    "detected_type": "intervals",
                    "confidence": "high" if cv > 25 else "moderate",
                    "source": "lap_analysis",
                    "interval_count": len(work_laps),
                    "avg_work_distance_m": round(sum(work_distances) / len(work_distances), 0) if work_distances else 0,
                    "avg_work_time_s": round(sum(work_times) / len(work_times), 0) if work_times else 0,
                    "avg_rest_time_s": avg_rest,
                }

    # Progression detection: splits consistently getting faster
    if splits and len(splits) >= 4:
        split_times = [s.get("moving_time", s.get("elapsed_time", 0)) for s in splits if s.get("distance", 0) > 500]
        if len(split_times) >= 4:
            decreasing_count = sum(1 for i in range(1, len(split_times)) if split_times[i] < split_times[i - 1])
            if decreasing_count >= len(split_times) * 0.7:
                return {"detected_type": "progression", "confidence": "moderate", "source": "split_analysis"}

    # Tempo detection: relatively even pace, moderate-to-hard effort
    if splits and len(splits) >= 3:
        split_times = [s.get("moving_time", s.get("elapsed_time", 0)) for s in splits if s.get("distance", 0) > 500]
        if split_times:
            avg_split = sum(split_times) / len(split_times)
            std_split = (sum((p - avg_split) ** 2 for p in split_times) / len(split_times)) ** 0.5
            cv = std_split / avg_split * 100 if avg_split > 0 else 0
            avg_hr = activity.get("average_heartrate", 0)
            max_hr = activity.get("max_heartrate", 0)

            # Tempo: even pacing (low CV) and moderately hard HR
            hr_pct = avg_hr / max_hr * 100 if max_hr > 0 else 0
            if cv < 5 and hr_pct > 80 and 3 <= distance_km <= 15:
                return {"detected_type": "tempo", "confidence": "moderate", "source": "pace_hr_analysis"}

    # Long run: >15km or >90 minutes
    if distance_km >= 15 or moving_time_s >= 5400:
        return {"detected_type": "long_run", "confidence": "high", "source": "distance_duration"}

    # Recovery: very short and slow
    if distance_km < 6 and avg_speed < 2.8:
        return {"detected_type": "recovery", "confidence": "moderate", "source": "distance_pace"}

    # Default: easy run
    return {"detected_type": "easy_run", "confidence": "low", "source": "default"}


def get_training_distribution(
    activities: list[dict[str, Any]],
    athlete_zones: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Classify runs by intensity and compute training distribution.

    Uses HR data when available, falls back to suffer_score or pace-based heuristics.

    Args:
        activities: List of activity summaries (from strava-mcp get_recent_activities).
        athlete_zones: Optional HR zone definitions.

    Returns:
        Percentage split (easy/moderate/hard), run-by-run classification, and 80/20 assessment.
    """
    runs = [a for a in activities if a.get("type") == "Run" or a.get("sport_type") in ("Run", "TrailRun", "VirtualRun")]

    if not runs:
        return {"error": "No running activities found.", "run_count": 0}

    classifications: list[dict[str, Any]] = []
    easy_time = 0
    moderate_time = 0
    hard_time = 0

    for run in runs:
        moving_time = run.get("moving_time_s", run.get("moving_time", 0))
        avg_hr = run.get("average_heartrate")
        max_hr = run.get("max_heartrate")
        suffer_score = run.get("suffer_score")

        intensity = _classify_intensity(avg_hr, max_hr, suffer_score, moving_time, athlete_zones)
        classifications.append(
            {
                "activity_id": run.get("id"),
                "name": run.get("name", ""),
                "date": run.get("start_date", ""),
                "distance_km": run.get("distance_km", run.get("distance", 0) / 1000 if run.get("distance") else 0),
                "moving_time_s": moving_time,
                "intensity": intensity,
            }
        )

        if intensity == "easy":
            easy_time += moving_time
        elif intensity == "moderate":
            moderate_time += moving_time
        else:
            hard_time += moving_time

    total_time = easy_time + moderate_time + hard_time
    if total_time == 0:
        return {"error": "No time data available.", "run_count": len(runs)}

    easy_pct = round(easy_time / total_time * 100, 1)
    moderate_pct = round(moderate_time / total_time * 100, 1)
    hard_pct = round(hard_time / total_time * 100, 1)

    # 80/20 assessment
    easy_like_pct = easy_pct  # Only genuinely easy counts
    hard_like_pct = moderate_pct + hard_pct

    if easy_like_pct >= 75:
        polarization = "well_polarized"
        assessment = (
            f"Good polarization: {easy_like_pct:.0f}% easy / {hard_like_pct:.0f}% hard. Close to the 80/20 ideal."
        )
    elif easy_like_pct >= 60:
        polarization = "moderate"
        assessment = (
            f"Moderate polarization: {easy_like_pct:.0f}% easy / {hard_like_pct:.0f}% hard. "
            "Too much moderate intensity — slow down your easy runs."
        )
    else:
        polarization = "poorly_polarized"
        assessment = (
            f"Poor polarization: {easy_like_pct:.0f}% easy / {hard_like_pct:.0f}% hard. "
            "Most runs are too hard. Risk of overtraining. Significantly slow down easy days."
        )

    return {
        "run_count": len(classifications),
        "total_time_s": total_time,
        "distribution": {
            "easy_pct": easy_pct,
            "moderate_pct": moderate_pct,
            "hard_pct": hard_pct,
        },
        "polarization": polarization,
        "assessment": assessment,
        "classifications": classifications,
    }


def assess_fitness_trend(
    best_efforts: list[dict[str, Any]],
    weekly_summaries: list[dict[str, Any]],
) -> dict[str, Any]:
    """Assess fitness trend from best efforts and weekly training data.

    Computes VDOT trend from best efforts, and efficiency trend from weekly summaries.

    Args:
        best_efforts: List of best effort records (from strava-mcp get_best_efforts).
        weekly_summaries: Weekly aggregates (from strava-mcp get_weekly_summary).

    Returns:
        Fitness trend assessment with VDOT trajectory and volume trends.
    """
    from pace_ai.tools.analysis import _vdot_from_time

    result: dict[str, Any] = {}

    # VDOT from best efforts
    vdot_estimates = []
    for effort in best_efforts:
        distance_m = effort.get("distance_m", 0)
        elapsed = effort.get("elapsed_time", 0)
        if distance_m >= 1000 and elapsed > 0:
            vdot = round(_vdot_from_time(distance_m, elapsed), 1)
            vdot_estimates.append(
                {
                    "distance": effort.get("distance_name", ""),
                    "time": effort.get("elapsed_time_formatted", ""),
                    "vdot": vdot,
                }
            )

    if vdot_estimates:
        vdot_values = [v["vdot"] for v in vdot_estimates]
        result["vdot_estimates"] = vdot_estimates
        result["current_vdot"] = round(max(vdot_values), 1)
        result["vdot_range"] = {"min": round(min(vdot_values), 1), "max": round(max(vdot_values), 1)}

    # Volume trend from weekly summaries
    if weekly_summaries and len(weekly_summaries) >= 2:
        distances = [w.get("total_distance_km", 0) for w in weekly_summaries]
        first_half = distances[: len(distances) // 2]
        second_half = distances[len(distances) // 2 :]

        first_avg = sum(first_half) / len(first_half) if first_half else 0
        second_avg = sum(second_half) / len(second_half) if second_half else 0

        volume_trend_pct = round((second_avg - first_avg) / first_avg * 100, 1) if first_avg > 0 else 0.0

        result["volume_trend"] = {
            "first_half_avg_km": round(first_avg, 1),
            "second_half_avg_km": round(second_avg, 1),
            "trend_pct": volume_trend_pct,
            "trend_direction": "increasing"
            if volume_trend_pct > 5
            else "decreasing"
            if volume_trend_pct < -5
            else "stable",
        }

        # Consistency (weeks with runs / total weeks)
        active_weeks = sum(1 for d in distances if d > 0)
        result["consistency"] = {
            "active_weeks": active_weeks,
            "total_weeks": len(distances),
            "consistency_pct": round(active_weeks / len(distances) * 100, 1) if distances else 0,
        }

    # Overall trend narrative
    narratives = []
    if "current_vdot" in result:
        narratives.append(f"Current VDOT: {result['current_vdot']} (estimated from best efforts).")
    if "volume_trend" in result:
        direction = result["volume_trend"]["trend_direction"]
        if direction == "increasing":
            narratives.append("Training volume is trending upward — good progressive overload.")
        elif direction == "decreasing":
            narratives.append("Training volume is declining — intentional taper or potential detraining.")
        else:
            narratives.append("Training volume is stable.")
    if "consistency" in result:
        cpct = result["consistency"]["consistency_pct"]
        if cpct >= 90:
            narratives.append("Excellent training consistency.")
        elif cpct >= 70:
            narratives.append("Good consistency, but some missed weeks.")
        else:
            narratives.append("Inconsistent training — consistency is the #1 predictor of improvement.")

    result["narrative"] = " ".join(narratives)
    return result


def assess_race_readiness(
    goals: list[dict[str, Any]],
    best_efforts: list[dict[str, Any]],
    weekly_summaries: list[dict[str, Any]],
    training_load: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Compute structured race readiness assessment.

    Evaluates volume adequacy, VDOT alignment with goal, long run readiness,
    consistency, and training load status.

    Args:
        goals: Active goals (from pace-ai get_goals).
        best_efforts: Best efforts (from strava-mcp get_best_efforts).
        weekly_summaries: Weekly aggregates (from strava-mcp get_weekly_summary).
        training_load: Optional ACWR analysis.

    Returns:
        Readiness scores per goal with specific strengths and risks.
    """
    from pace_ai.tools.analysis import RACE_DISTANCES, _vdot_from_time

    if not goals:
        return {"error": "No goals set. Use set_goal to define a target race."}

    assessments = []
    for goal in goals:
        race_type = goal.get("race_type", "").lower()
        target_seconds = goal.get("target_time_seconds", 0)

        race_distance_m = RACE_DISTANCES.get(race_type, 0)
        target_vdot = None
        if race_distance_m > 0 and target_seconds > 0:
            target_vdot = round(_vdot_from_time(race_distance_m, target_seconds), 1)

        # Current VDOT from best efforts (preferred)
        current_vdot = None
        for effort in best_efforts:
            dist = effort.get("distance_m", 0)
            elapsed = effort.get("elapsed_time", 0)
            if dist >= 1000 and elapsed > 0:
                v = round(_vdot_from_time(dist, elapsed), 1)
                if current_vdot is None or v > current_vdot:
                    current_vdot = v

        # Fallback: estimate VDOT from weekly summary pace when no best efforts
        if current_vdot is None and weekly_summaries:
            for w in reversed(weekly_summaries):
                dist_km = w.get("total_distance_km", 0)
                time_s = w.get("total_time_s", 0)
                if dist_km >= 5 and time_s > 0:
                    avg_speed_mps = (dist_km * 1000) / time_s
                    # Estimate from a hypothetical 5K at average training pace
                    est_5k_time = 5000 / avg_speed_mps
                    current_vdot = round(_vdot_from_time(5000, est_5k_time), 1)
                    break

        # Volume adequacy
        peak_weekly_km = max((w.get("total_distance_km", 0) for w in weekly_summaries), default=0)
        longest_run_km = max((w.get("longest_run_km", 0) for w in weekly_summaries), default=0)
        race_distance_km = race_distance_m / 1000 if race_distance_m else 0

        # Score components (each 0-10)
        scores = {}

        # VDOT alignment
        if target_vdot and current_vdot:
            vdot_gap = current_vdot - target_vdot
            if vdot_gap >= 2:
                scores["fitness"] = 10
            elif vdot_gap >= 0:
                scores["fitness"] = 8
            elif vdot_gap >= -2:
                scores["fitness"] = 6
            elif vdot_gap >= -5:
                scores["fitness"] = 4
            else:
                scores["fitness"] = 2

        # Volume adequacy (peak week should be 1.5-2x race distance for marathon, 2-3x for half)
        if race_distance_km > 0 and peak_weekly_km > 0:
            ratio = peak_weekly_km / race_distance_km
            if ratio >= 2.0:
                scores["volume"] = 10
            elif ratio >= 1.5:
                scores["volume"] = 8
            elif ratio >= 1.0:
                scores["volume"] = 5
            else:
                scores["volume"] = 3

        # Long run readiness
        if race_distance_km > 0 and longest_run_km > 0:
            long_ratio = longest_run_km / race_distance_km
            if long_ratio >= 0.75:
                scores["long_run"] = 10
            elif long_ratio >= 0.5:
                scores["long_run"] = 7
            elif long_ratio >= 0.35:
                scores["long_run"] = 4
            else:
                scores["long_run"] = 2

        # Consistency
        if weekly_summaries:
            active = sum(1 for w in weekly_summaries if w.get("total_distance_km", 0) > 0)
            pct = active / len(weekly_summaries) * 100
            if pct >= 90:
                scores["consistency"] = 10
            elif pct >= 75:
                scores["consistency"] = 7
            elif pct >= 50:
                scores["consistency"] = 4
            else:
                scores["consistency"] = 2

        # Training load
        if training_load:
            acwr = training_load.get("acwr", 1.0)
            if 0.8 <= acwr <= 1.3:
                scores["load_management"] = 9
            elif 0.6 <= acwr <= 1.5:
                scores["load_management"] = 6
            else:
                scores["load_management"] = 3

        # Overall score
        overall = round(sum(scores.values()) / len(scores), 1) if scores else 0

        # Build strengths/risks
        strengths = []
        risks = []
        if scores.get("fitness", 0) >= 8:
            strengths.append("Fitness level supports the goal time.")
        elif "fitness" in scores:
            gap = (target_vdot or 0) - (current_vdot or 0)
            risks.append(f"VDOT gap of {gap:.1f} — goal may be aggressive.")

        if scores.get("volume", 0) >= 8:
            strengths.append("Weekly volume is adequate for this distance.")
        elif "volume" in scores:
            risks.append(f"Peak weekly mileage ({peak_weekly_km:.1f} km) may be insufficient.")

        if scores.get("long_run", 0) >= 7:
            strengths.append(f"Longest run ({longest_run_km:.1f} km) provides good race preparation.")
        elif "long_run" in scores:
            risks.append(f"Longest run ({longest_run_km:.1f} km) is short for this race distance.")

        if scores.get("consistency", 0) >= 7:
            strengths.append("Consistent training pattern.")
        elif "consistency" in scores:
            risks.append("Inconsistent training — missed weeks reduce preparedness.")

        assessments.append(
            {
                "goal": goal.get("race_type", ""),
                "target_time": goal.get("target_time_formatted", ""),
                "target_vdot": target_vdot,
                "current_vdot": current_vdot,
                "overall_score": overall,
                "component_scores": scores,
                "strengths": strengths,
                "risks": risks,
            }
        )

    return {"assessments": assessments}


# ── Private helpers ───────────────────────────────────────────────────


def detect_anomalies(
    activity: dict[str, Any],
    streams: dict[str, list] | None = None,
) -> dict[str, Any]:
    """Detect data quality issues in an activity.

    Flags GPS glitches (impossible speeds), HR anomalies (flat signal, impossible values),
    pace outlier splits, and missing data. Helps Claude avoid coaching on bad data.

    Args:
        activity: Full activity detail from strava-mcp.
        streams: Optional time-series data (heartrate, velocity_smooth, etc.).

    Returns:
        Anomaly flags, data quality score, and per-issue details.
    """
    anomalies: list[dict[str, Any]] = []

    distance_m = activity.get("distance", 0)
    moving_time_s = activity.get("moving_time", 0)
    avg_speed = distance_m / moving_time_s if moving_time_s > 0 else 0

    # GPS / distance anomalies
    if distance_m > 0 and moving_time_s > 0:
        # Impossible running speed (>7.5 m/s ≈ 2:13/km, sub-2hr marathon pace)
        if avg_speed > 7.5:
            anomalies.append(
                {
                    "type": "gps",
                    "severity": "high",
                    "detail": f"Average speed {avg_speed:.2f} m/s is impossibly fast for running.",
                }
            )
        # Zero distance with moving time
        if distance_m < 100 and moving_time_s > 300:
            anomalies.append(
                {
                    "type": "gps",
                    "severity": "high",
                    "detail": f"Only {distance_m:.0f}m recorded over {moving_time_s}s — likely GPS failure.",
                }
            )

    # Split pace anomalies
    splits = activity.get("splits_metric", [])
    if splits:
        split_times = [s.get("moving_time", s.get("elapsed_time", 0)) for s in splits if s.get("distance", 0) > 500]
        if len(split_times) >= 3:
            avg_split = sum(split_times) / len(split_times)
            for i, st in enumerate(split_times):
                if avg_split > 0 and abs(st - avg_split) / avg_split > 0.5:
                    anomalies.append(
                        {
                            "type": "pace",
                            "severity": "moderate",
                            "detail": f"Split {i + 1} ({st}s) deviates >50% from average ({avg_split:.0f}s)"
                            " — possible GPS glitch or stop.",
                        }
                    )

    # HR anomalies from streams
    if streams and "heartrate" in streams:
        hr_data = streams["heartrate"]
        if hr_data:
            max_hr = max(hr_data)
            min_hr = min(hr_data)
            avg_hr = sum(hr_data) / len(hr_data)

            # Impossibly high HR
            if max_hr > 250:
                anomalies.append(
                    {
                        "type": "hr",
                        "severity": "high",
                        "detail": f"Max HR {max_hr} bpm exceeds physiological limit — sensor malfunction.",
                    }
                )
            # Impossibly low HR while running (< 40 bpm sustained)
            low_count = sum(1 for hr in hr_data if hr < 40)
            if low_count > len(hr_data) * 0.1:
                anomalies.append(
                    {
                        "type": "hr",
                        "severity": "high",
                        "detail": f"{low_count}/{len(hr_data)} HR readings below 40 bpm — sensor dropout.",
                    }
                )
            # Flat HR signal (zero variance = stuck sensor)
            if max_hr == min_hr and len(hr_data) > 10:
                anomalies.append(
                    {
                        "type": "hr",
                        "severity": "high",
                        "detail": f"HR is constant at {max_hr} bpm — sensor stuck.",
                    }
                )
            # Very low variance (nearly flat)
            elif len(hr_data) > 20:
                variance = sum((hr - avg_hr) ** 2 for hr in hr_data) / len(hr_data)
                if variance < 1.0 and avg_hr > 60:
                    anomalies.append(
                        {
                            "type": "hr",
                            "severity": "moderate",
                            "detail": "HR variance < 1 bpm² — sensor may not be reading correctly.",
                        }
                    )

    # HR anomalies from activity summary (no streams needed)
    elif activity.get("average_heartrate"):
        avg_hr_act = activity["average_heartrate"]
        max_hr_act = activity.get("max_heartrate", 0)
        if max_hr_act > 250:
            anomalies.append(
                {
                    "type": "hr",
                    "severity": "high",
                    "detail": f"Max HR {max_hr_act} bpm exceeds physiological limit.",
                }
            )
        if avg_hr_act and max_hr_act and max_hr_act > 0 and avg_hr_act > max_hr_act:
            anomalies.append(
                {
                    "type": "hr",
                    "severity": "moderate",
                    "detail": f"Average HR ({avg_hr_act}) exceeds max HR ({max_hr_act}) — data inconsistency.",
                }
            )

    # Missing data flags
    missing = []
    if not activity.get("average_heartrate") and not (streams and "heartrate" in streams):
        missing.append("heart_rate")
    if not splits:
        missing.append("splits")
    if not activity.get("average_cadence"):
        missing.append("cadence")

    # Data quality score (10 = perfect, 0 = unusable)
    high_count = sum(1 for a in anomalies if a["severity"] == "high")
    moderate_count = sum(1 for a in anomalies if a["severity"] == "moderate")
    quality_score = max(0, 10 - high_count * 3 - moderate_count * 1 - len(missing) * 0.5)

    return {
        "activity_id": activity.get("id"),
        "anomalies": anomalies,
        "anomaly_count": len(anomalies),
        "missing_data": missing,
        "data_quality_score": round(quality_score, 1),
        "usable_for_coaching": quality_score >= 5,
    }


def _compute_time_in_zones(
    hr_stream: list[int],
    zones: list[dict[str, int]],
    time_stream: list[int] | None = None,
) -> list[dict[str, Any]]:
    """Compute time spent in each HR zone from a heart rate stream."""
    if not zones or not hr_stream:
        return []

    zone_seconds = [0.0] * len(zones)

    for i, hr in enumerate(hr_stream):
        # Compute time delta; guard against missing/short time_stream
        dt = max(0, time_stream[i] - time_stream[i - 1]) if time_stream and i > 0 and i < len(time_stream) else 1

        for z_idx, zone in enumerate(zones):
            z_min = zone.get("min", 0)
            z_max = zone.get("max", 999)
            if z_max == -1:
                z_max = 999
            if z_min <= hr < z_max:
                zone_seconds[z_idx] += dt
                break

    total = sum(zone_seconds)
    result = []
    for i, secs in enumerate(zone_seconds):
        result.append(
            {
                "zone_index": i + 1,
                "zone_range": f"{zones[i].get('min', 0)}-"
                f"{zones[i].get('max', '∞') if zones[i].get('max', -1) != -1 else '∞'}",
                "time_seconds": round(secs, 1),
                "time_pct": round(secs / total * 100, 1) if total > 0 else 0,
            }
        )
    return result


def calculate_cardiac_decoupling(
    hr_stream: list[int],
    velocity_stream: list[float],
    time_stream: list[int] | None = None,
) -> dict[str, Any]:
    """Calculate cardiac decoupling (Pa:Hr drift) between run halves.

    Compares the pace-to-HR ratio in the first and second halves of a run.
    A key indicator of aerobic fitness — well-trained runners maintain
    a stable pace:HR relationship throughout steady runs.

    Args:
        hr_stream: Heart rate data points (bpm).
        velocity_stream: Velocity data points (m/s).
        time_stream: Optional timestamps for weighted calculation.

    Returns:
        Decoupling percentage, assessment, and half-by-half breakdown.
    """
    min_points = 20
    if len(hr_stream) < min_points or len(velocity_stream) < min_points:
        return {
            "error": f"Need at least {min_points} data points. Got HR={len(hr_stream)}, vel={len(velocity_stream)}.",
        }

    n = min(len(hr_stream), len(velocity_stream))
    mid = n // 2

    # Filter out zero-velocity points (stops) from both halves
    def _half_ratio(start: int, end: int) -> tuple[float, float, float]:
        total_pace = 0.0
        total_hr = 0.0
        count = 0
        for i in range(start, end):
            if velocity_stream[i] > 0.5 and hr_stream[i] > 60:  # Moving and valid HR
                total_pace += velocity_stream[i]
                total_hr += hr_stream[i]
                count += 1
        avg_vel = total_pace / count if count > 0 else 0
        avg_hr = total_hr / count if count > 0 else 0
        ratio = avg_vel / avg_hr if avg_hr > 0 else 0
        return ratio, avg_vel, avg_hr

    first_ratio, first_vel, first_hr = _half_ratio(0, mid)
    second_ratio, second_vel, second_hr = _half_ratio(mid, n)

    if first_ratio == 0:
        return {"error": "Insufficient valid data in first half (too many stops or zero HR)."}

    decoupling_pct = round((first_ratio - second_ratio) / first_ratio * 100, 1)

    if decoupling_pct < 3:
        assessment = "excellent"
        interpretation = "Minimal decoupling — strong aerobic fitness. Pace:HR stayed stable."
    elif decoupling_pct < 5:
        assessment = "good"
        interpretation = "Slight decoupling. Aerobic system handled the effort well."
    elif decoupling_pct < 10:
        assessment = "adequate"
        interpretation = "Moderate decoupling. Aerobic fitness is developing but not yet strong for this duration."
    else:
        assessment = "poor"
        interpretation = (
            "Significant decoupling (>10%). Possible causes: insufficient aerobic base, "
            "dehydration, heat, or pace was above aerobic threshold."
        )

    return {
        "decoupling_pct": decoupling_pct,
        "assessment": assessment,
        "interpretation": interpretation,
        "first_half": {
            "avg_velocity_mps": round(first_vel, 2),
            "avg_hr_bpm": round(first_hr, 1),
            "efficiency_ratio": round(first_ratio, 4),
        },
        "second_half": {
            "avg_velocity_mps": round(second_vel, 2),
            "avg_hr_bpm": round(second_hr, 1),
            "efficiency_ratio": round(second_ratio, 4),
        },
    }


def _assess_hr_reliability(
    activity: dict[str, Any],
    streams: dict[str, list] | None = None,
) -> list[dict[str, str]]:
    """Assess conditions that may make HR data unreliable.

    Flags known sources of HR measurement error so Claude can caveat
    HR-based coaching advice when data quality is compromised.
    """
    warnings: list[dict[str, str]] = []

    moving_time_s = activity.get("moving_time", 0)

    # Optical HR lag in first ~5 minutes
    if streams and "heartrate" in streams:
        hr_data = streams["heartrate"]
        if len(hr_data) > 60:
            # Check for initial HR ramp-up (first 5 min HR much lower than next 5 min)
            early = hr_data[: min(60, len(hr_data) // 4)]
            later = hr_data[min(60, len(hr_data) // 4) : min(120, len(hr_data) // 2)]
            if early and later:
                early_avg = sum(early) / len(early)
                later_avg = sum(later) / len(later)
                if later_avg > 0 and (later_avg - early_avg) / later_avg > 0.15:
                    warnings.append(
                        {
                            "condition": "optical_hr_lag",
                            "detail": "HR data shows >15% jump after initial minutes"
                            " — likely optical sensor warm-up lag.",
                        }
                    )

    # Long run drift caveat (>90 min)
    if moving_time_s > 5400:
        warnings.append(
            {
                "condition": "long_run_cardiac_drift",
                "detail": "Run >90 min — cardiac drift is expected even at steady effort. HR zones less reliable.",
            }
        )

    # Heat effect on HR
    avg_temp = activity.get("average_temp")
    if avg_temp is not None and avg_temp > 25:
        warnings.append(
            {
                "condition": "heat_elevated_hr",
                "detail": f"Temperature {avg_temp}°C — heat elevates HR 5-10% above normal for the same effort.",
            }
        )

    # Short intervals — HR doesn't stabilize
    laps = activity.get("laps", [])
    if len(laps) >= 4:
        short_laps = [lp for lp in laps if lp.get("moving_time", 0) < 300 and lp.get("distance", 0) > 100]
        if len(short_laps) > len(laps) * 0.4:
            warnings.append(
                {
                    "condition": "interval_hr_lag",
                    "detail": "Many laps <5 min — HR doesn't fully respond to short intervals. Use pace for intensity.",
                }
            )

    return warnings


def _classify_intensity(
    avg_hr: float | None,
    max_hr: float | None,
    suffer_score: float | None,
    moving_time: int,
    athlete_zones: dict[str, Any] | None,
) -> str:
    """Classify a run's intensity as easy/moderate/hard."""
    # HR-based classification (preferred)
    if avg_hr and max_hr and max_hr > 0:
        hr_pct = avg_hr / max_hr * 100
        if hr_pct < 75:
            return "easy"
        if hr_pct < 85:
            return "moderate"
        return "hard"

    # Zone-based classification
    if avg_hr and athlete_zones and "heart_rate" in athlete_zones:
        zones = athlete_zones["heart_rate"].get("zones", [])
        if len(zones) >= 4:
            z2_max = zones[1].get("max", 152)
            z3_max = zones[2].get("max", 171)
            if avg_hr < z2_max:
                return "easy"
            if avg_hr < z3_max:
                return "moderate"
            return "hard"

    # Suffer score fallback (Strava's relative effort)
    if suffer_score is not None and moving_time > 0:
        score_per_min = suffer_score / (moving_time / 60)
        if score_per_min < 1.5:
            return "easy"
        if score_per_min < 3.0:
            return "moderate"
        return "hard"

    return "unknown"
