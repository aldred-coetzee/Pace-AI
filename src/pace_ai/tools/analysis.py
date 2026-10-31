"""Training analysis tools — ACWR, VDOT, Riegel, training zones."""

from __future__ import annotations

import math
from typing import Any

# ── ACWR (Acute:Chronic Workload Ratio) ──────────────────────────────


def calculate_acwr(weekly_distances: list[float]) -> dict[str, Any]:
    """Compute acute:chronic workload ratio from weekly distance data.

    Uses the uncoupled method (Windt & Gabbett 2019): acute = last 1 week,
    chronic = mean of the 4 weeks BEFORE the acute week. This avoids the
    mathematical coupling artefact of including the acute week in the chronic
    average.

    Optimal ACWR range: 0.8-1.3 (Gabbett 2016).

    Args:
        weekly_distances: List of weekly distances (most recent last), minimum 5 weeks.

    Returns:
        ACWR value, risk level, load variability, and interpretation.
    """
    if len(weekly_distances) < 5:
        msg = "Need at least 5 weeks of data for ACWR calculation."
        raise ValueError(msg)

    acute = weekly_distances[-1]
    chronic_weeks = weekly_distances[-5:-1]  # 4 weeks BEFORE the acute week
    chronic = sum(chronic_weeks) / 4

    if chronic == 0:
        return {
            "acwr": 0,
            "acute_load": acute,
            "chronic_load": chronic,
            "risk_level": "insufficient_data",
            "interpretation": "No chronic training load to compare against.",
        }

    acwr = round(acute / chronic, 2)

    # Load variability — coefficient of variation of the chronic-period weeks.
    # This is NOT Foster's "monotony" (which requires daily data within a single week).
    # CV measures how consistent week-to-week loading has been during the chronic period.
    mean_load = sum(chronic_weeks) / len(chronic_weeks)
    std_load = (sum((x - mean_load) ** 2 for x in chronic_weeks) / len(chronic_weeks)) ** 0.5
    load_variability_cv = round(std_load / mean_load, 2) if mean_load > 0 else 0

    # Risk classification
    if acwr < 0.8:
        risk_level = "undertraining"
        interpretation = "Training load is significantly below your chronic average. Risk of detraining."
    elif acwr <= 1.3:
        risk_level = "optimal"
        interpretation = "Training load is in the optimal range (0.8-1.3). Good balance of stimulus and recovery."
    elif acwr <= 1.5:
        risk_level = "elevated"
        interpretation = "Training load spike detected (ACWR > 1.3). Moderate injury risk — monitor recovery."
    else:
        risk_level = "high"
        interpretation = "Significant training load spike (ACWR > 1.5). High injury risk — consider reducing volume."

    return {
        "acwr": acwr,
        "acute_load": acute,
        "chronic_load": round(chronic, 1),
        "risk_level": risk_level,
        "interpretation": interpretation,
        "load_variability_cv": load_variability_cv,
        "week_over_week_change_pct": round((acute - weekly_distances[-2]) / weekly_distances[-2] * 100, 1)
        if weekly_distances[-2] > 0
        else None,
    }


# ── VDOT (Jack Daniels' Running Formula) ────────────────────────────


def _vdot_from_time(distance_m: float, time_seconds: float) -> float:
    """Estimate VDOT from a race result using the Daniels/Gilbert formula.

    Based on the oxygen cost and VO2max fraction curves from
    Daniels & Gilbert, "Oxygen Power" (1979).
    """
    time_min = time_seconds / 60
    # Oxygen cost of running at velocity (ml/kg/min)
    velocity = distance_m / time_min  # m/min
    vo2 = -4.60 + 0.182258 * velocity + 0.000104 * velocity**2

    # Fraction of VO2max sustained (percent VO2max as function of time)
    pct_max = 0.8 + 0.1894393 * math.exp(-0.012778 * time_min) + 0.2989558 * math.exp(-0.1932605 * time_min)

    return vo2 / pct_max


def _time_from_vdot(vdot: float, distance_m: float) -> float:
    """Predict race time (seconds) from VDOT and distance using binary search."""
    lo, hi = 1.0, 86400.0  # 1 second to 24 hours
    for _ in range(100):
        mid = (lo + hi) / 2
        estimated_vdot = _vdot_from_time(distance_m, mid)
        if estimated_vdot < vdot:
            hi = mid
        else:
            lo = mid
    return round((lo + hi) / 2)


def _pace_secs_from_vo2(target_vo2: float) -> int:
    """Compute pace (seconds per km) for a given oxygen cost.

    Inverts the Daniels/Gilbert oxygen cost equation:
        vo2 = -4.60 + 0.182258 * v + 0.000104 * v^2
    using the quadratic formula.
    """
    a = 0.000104
    b = 0.182258
    c = -4.60 - target_vo2
    discriminant = b**2 - 4 * a * c
    velocity = (-b + math.sqrt(discriminant)) / (2 * a)  # m/min
    return int(60000 / velocity)  # seconds per km


RACE_DISTANCES = {
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

# Daniels' zone definitions as %VO2max ranges (from Daniels' Running Formula).
_ZONE_VO2MAX_PCT = {
    "easy": (0.59, 0.74),
    "marathon": (0.75, 0.84),
    "threshold": (0.83, 0.88),
    "interval": (0.95, 1.00),
    "repetition": (1.05, 1.20),
}


def _cameron_predict(source_dist_m: float, source_time_s: float, target_dist_m: float) -> int:
    """Predict race time using the Cameron model.

    The Cameron model uses distance-specific fatigue/drop-off factors and is
    considered more accurate than Riegel for longer distances. The drop-off
    factor captures that pace slows more at longer distances.

    Formula: t2 = t1 * (d2/d1) * (f(d2)/f(d1))
    where f(d) = 13.49681 - 0.048865*d + 2.438936/(d^0.7905)  (d in miles)
    """
    # Convert to miles for the Cameron coefficients
    d1 = source_dist_m / 1609.344
    d2 = target_dist_m / 1609.344

    def _fatigue(d_miles: float) -> float:
        return 13.49681 - 0.048865 * d_miles + 2.438936 / (d_miles**0.7905)

    f1 = _fatigue(d1)
    f2 = _fatigue(d2)

    return round(source_time_s * (d2 / d1) * (f2 / f1))


def predict_race_time(
    recent_race_distance: str,
    recent_race_time: str,
    target_distance: str,
    temperature_c: float | None = None,
    altitude_m: float | None = None,
) -> dict[str, Any]:
    """Predict race time using VDOT, Riegel, and Cameron models.

    Args:
        recent_race_distance: Distance of recent race (e.g. "5k", "10k", "half marathon").
        recent_race_time: Finish time of recent race (H:MM:SS or M:SS).
        target_distance: Target race distance to predict.
        temperature_c: Race-day temperature in Celsius (optional, applies heat slowdown).
        altitude_m: Race-day altitude in meters (optional, applies altitude slowdown).

    Returns:
        Predicted time, VDOT, Cameron prediction, and equivalent performances.
    """
    from pace_ai.tools.goals import format_time, parse_time

    source_dist = RACE_DISTANCES.get(recent_race_distance.lower())
    target_dist = RACE_DISTANCES.get(target_distance.lower())

    if source_dist is None:
        msg = f"Unknown distance: {recent_race_distance}. Use one of: {', '.join(RACE_DISTANCES)}"
        raise ValueError(msg)
    if target_dist is None:
        msg = f"Unknown distance: {target_distance}. Use one of: {', '.join(RACE_DISTANCES)}"
        raise ValueError(msg)

    time_seconds = parse_time(recent_race_time)
    vdot = round(_vdot_from_time(source_dist, time_seconds), 1)
    predicted_seconds = _time_from_vdot(vdot, target_dist)

    # Riegel comparison
    riegel_seconds = round(time_seconds * (target_dist / source_dist) ** 1.06)

    # Cameron model (uses fatigue factors specific to each distance)
    cameron_seconds = _cameron_predict(source_dist, time_seconds, target_dist)

    # Equivalent performances at all distances
    equivalents = {}
    for name, dist in RACE_DISTANCES.items():
        eq_seconds = _time_from_vdot(vdot, dist)
        equivalents[name] = format_time(eq_seconds)

    # Build caveats for marathon predictions from short distances
    caveats: list[str] = []
    if target_dist >= 42000 and source_dist <= 10000:
        caveats.append(
            "Predicting marathon from short races is unreliable. "
            "A half marathon is the best predictor for marathon times."
        )
    if target_dist >= 42000:
        caveats.append("Riegel and VDOT systematically underestimate marathon times for runners under 60 km/week.")

    result: dict[str, Any] = {
        "vdot": vdot,
        "predicted_time": format_time(predicted_seconds),
        "predicted_seconds": predicted_seconds,
        "riegel_predicted_time": format_time(riegel_seconds),
        "riegel_predicted_seconds": riegel_seconds,
        "cameron_predicted_time": format_time(cameron_seconds),
        "cameron_predicted_seconds": cameron_seconds,
        "source_race": {"distance": recent_race_distance, "time": recent_race_time},
        "target_distance": target_distance,
        "equivalent_performances": equivalents,
        "caveats": caveats,
    }

    # Apply environment adjustments if provided
    if temperature_c is not None or altitude_m is not None:
        from pace_ai.tools.environment import calculate_altitude_adjustment, calculate_heat_adjustment

        env_factor = 1.0
        env_adjustments: dict[str, Any] = {}

        if temperature_c is not None:
            heat = calculate_heat_adjustment(temperature_c=temperature_c)
            env_factor *= heat["adjustment_factor"]
            env_adjustments["heat"] = heat
            if heat["slowdown_pct"] > 0:
                caveats.append(f"Heat adjustment: +{heat['slowdown_pct']}% slower at {temperature_c}\u00b0C.")

        if altitude_m is not None:
            alt = calculate_altitude_adjustment(altitude_m=altitude_m)
            env_factor *= alt["adjustment_factor"]
            env_adjustments["altitude"] = alt
            if alt["slowdown_pct"] > 0:
                caveats.append(f"Altitude adjustment: +{alt['slowdown_pct']}% slower at {alt['altitude_m']:.0f}m.")

        adj_predicted = round(predicted_seconds * env_factor)
        adj_riegel = round(riegel_seconds * env_factor)
        adj_cameron = round(cameron_seconds * env_factor)
        result["environment_adjusted"] = {
            "adjustment_factor": round(env_factor, 4),
            "adjusted_predicted_time": format_time(adj_predicted),
            "adjusted_predicted_seconds": adj_predicted,
            "adjusted_riegel_time": format_time(adj_riegel),
            "adjusted_riegel_seconds": adj_riegel,
            "adjusted_cameron_time": format_time(adj_cameron),
            "adjusted_cameron_seconds": adj_cameron,
            "adjustments_applied": env_adjustments,
        }

    return result


# ── Training Zones (Daniels) ────────────────────────────────────────


def calculate_training_zones(
    threshold_pace_per_km: str | None = None,
    threshold_hr: int | None = None,
    vdot: float | None = None,
) -> dict[str, Any]:
    """Calculate Daniels' training zones from a threshold reference.

    Provide at least one of: threshold_pace_per_km, threshold_hr, or vdot.

    When vdot is provided, zones are computed directly from the Daniels/Gilbert
    oxygen cost curve using published %VO2max ranges for each zone. This is the
    most accurate method.

    Args:
        threshold_pace_per_km: Threshold (lactate/tempo) pace as M:SS per km.
        threshold_hr: Threshold heart rate in bpm.
        vdot: VDOT value (computes zones using Daniels' %VO2max curve).

    Returns:
        Training zones with pace and/or HR ranges.
    """
    from pace_ai.tools.goals import parse_time

    zones: dict[str, Any] = {}

    if vdot is not None:
        # Compute zones from VDOT using Daniels' %VO2max ranges.
        for zone_name, (lo_pct, hi_pct) in _ZONE_VO2MAX_PCT.items():
            fast_pace = _pace_secs_from_vo2(vdot * hi_pct)  # higher %VO2max → faster
            slow_pace = _pace_secs_from_vo2(vdot * lo_pct)  # lower %VO2max → slower
            fast_min, fast_sec = divmod(fast_pace, 60)
            slow_min, slow_sec = divmod(slow_pace, 60)
            zones[zone_name] = {
                "pace_range_per_km": f"{fast_min}:{fast_sec:02d} - {slow_min}:{slow_sec:02d}",
                "pace_seconds_per_km": (fast_pace, slow_pace),
            }
    elif threshold_pace_per_km is not None:
        threshold_secs = parse_time(threshold_pace_per_km)
        # Daniels' zone multipliers relative to threshold pace (T pace = 1.0)
        # Faster pace = lower seconds/km
        zone_multipliers = {
            "easy": (1.20, 1.35),  # 20-35% slower than threshold
            "marathon": (1.08, 1.15),  # 8-15% slower than threshold
            "threshold": (0.97, 1.03),  # ~threshold pace
            "interval": (0.88, 0.93),  # 7-12% faster than threshold
            "repetition": (0.80, 0.86),  # 14-20% faster than threshold
        }

        for zone_name, (lo_mult, hi_mult) in zone_multipliers.items():
            lo_pace = int(threshold_secs * lo_mult)
            hi_pace = int(threshold_secs * hi_mult)
            minutes_lo, secs_lo = divmod(lo_pace, 60)
            minutes_hi, secs_hi = divmod(hi_pace, 60)
            zones[zone_name] = {
                "pace_range_per_km": f"{minutes_hi}:{secs_hi:02d} - {minutes_lo}:{secs_lo:02d}",
                "pace_seconds_per_km": (hi_pace, lo_pace),
            }

    if threshold_hr is not None:
        hr_zones = {
            "easy": (int(threshold_hr * 0.65), int(threshold_hr * 0.79)),
            "marathon": (int(threshold_hr * 0.80), int(threshold_hr * 0.87)),
            "threshold": (int(threshold_hr * 0.88), int(threshold_hr * 0.92)),
            "interval": (int(threshold_hr * 0.93), int(threshold_hr * 0.97)),
            "repetition": (int(threshold_hr * 0.98), threshold_hr),
        }
        for zone_name, (lo_hr, hi_hr) in hr_zones.items():
            if zone_name not in zones:
                zones[zone_name] = {}
            zones[zone_name]["hr_range_bpm"] = (lo_hr, hi_hr)

    if not zones:
        msg = "Provide at least one of: threshold_pace_per_km, threshold_hr, or vdot."
        raise ValueError(msg)

    return {
        "zones": zones,
        "reference": {
            "threshold_pace_per_km": threshold_pace_per_km,
            "threshold_hr": threshold_hr,
            "vdot": vdot,
        },
        "description": {
            "easy": "Recovery and base building. Conversational pace. Most of your weekly mileage.",
            "marathon": "Marathon-specific endurance. Comfortably hard, sustainable for 2+ hours.",
            "threshold": "Lactate threshold / tempo pace. Comfortably hard for 20-40 minutes.",
            "interval": "VO2max development. Hard effort, 3-5 minute repeats with equal rest.",
            "repetition": "Speed and running economy. Short, fast repeats (200m-400m) with full recovery.",
        },
    }


# ── Karvonen HR Zones ────────────────────────────────────────────────


def calculate_hr_zones_karvonen(
    max_hr: int,
    resting_hr: int,
) -> dict[str, Any]:
    """Calculate HR training zones using the Karvonen (Heart Rate Reserve) method.

    More accurate than %MaxHR for recreational runners because it accounts for
    individual resting heart rate. Formula: Target HR = (HRR x %Intensity) + Resting HR.

    Args:
        max_hr: Maximum heart rate in bpm (from field test or 220-age estimate).
        resting_hr: Resting heart rate in bpm (measured upon waking).

    Returns:
        HR zones with Karvonen-based ranges and methodology notes.
    """
    if max_hr <= resting_hr:
        msg = f"max_hr ({max_hr}) must be greater than resting_hr ({resting_hr})."
        raise ValueError(msg)
    if max_hr < 100 or max_hr > 230:
        msg = f"max_hr ({max_hr}) outside plausible range 100-230 bpm."
        raise ValueError(msg)
    if resting_hr < 25 or resting_hr > 120:
        msg = f"resting_hr ({resting_hr}) outside plausible range 25-120 bpm."
        raise ValueError(msg)

    hrr = max_hr - resting_hr

    # Zone definitions using %HRR (Karvonen) — aligned with Daniels zone purposes
    zone_defs = {
        "easy": (0.50, 0.70),
        "marathon": (0.70, 0.80),
        "threshold": (0.80, 0.88),
        "interval": (0.88, 0.95),
        "repetition": (0.95, 1.00),
    }

    zones: dict[str, Any] = {}
    for zone_name, (lo_pct, hi_pct) in zone_defs.items():
        lo_hr = int(hrr * lo_pct + resting_hr)
        hi_hr = int(hrr * hi_pct + resting_hr)
        zones[zone_name] = {
            "hr_range_bpm": (lo_hr, hi_hr),
            "hrr_pct_range": (round(lo_pct * 100), round(hi_pct * 100)),
        }

    return {
        "method": "karvonen",
        "max_hr": max_hr,
        "resting_hr": resting_hr,
        "heart_rate_reserve": hrr,
        "zones": zones,
        "description": {
            "easy": "Recovery and base building. Conversational pace.",
            "marathon": "Marathon-specific endurance. Comfortably hard.",
            "threshold": "Lactate threshold effort. Comfortably hard for 20-40 minutes.",
            "interval": "VO2max development. Hard effort, 3-5 minute repeats.",
            "repetition": "Speed and economy. Short, fast repeats with full recovery.",
        },
        "notes": [
            "Karvonen method uses Heart Rate Reserve (HRR = Max HR - Resting HR).",
            "More accurate than %MaxHR for individuals with low or high resting HR.",
            "Max HR should ideally come from a field test, not the 220-age formula.",
            "Measure resting HR first thing in the morning before getting out of bed.",
        ],
    }


# ── Daily ACWR (EWMA) ────────────────────────────────────────────────


def calculate_acwr_daily(daily_distances: list[float]) -> dict[str, Any]:
    """Compute ACWR using EWMA (exponentially weighted moving averages).

    EWMA avoids the mathematical coupling issue with rolling-average ACWR
    (Williams et al. 2017). Also detects single-session spikes.

    Args:
        daily_distances: Daily distances in km (most recent last), minimum 28 days.

    Returns:
        EWMA-based ACWR, spike detection, and day-by-day analysis.
    """
    if len(daily_distances) < 28:
        msg = "Need at least 28 days of data for daily ACWR calculation."
        raise ValueError(msg)

    # EWMA parameters: acute = 7-day half-life, chronic = 28-day half-life
    acute_decay = 2 / (7 + 1)  # ~0.25
    chronic_decay = 2 / (28 + 1)  # ~0.069

    acute_ewma = daily_distances[0]
    chronic_ewma = daily_distances[0]

    for d in daily_distances[1:]:
        acute_ewma = d * acute_decay + acute_ewma * (1 - acute_decay)
        chronic_ewma = d * chronic_decay + chronic_ewma * (1 - chronic_decay)

    if chronic_ewma <= 0:
        return {
            "acwr_ewma": 0,
            "acute_ewma": round(acute_ewma, 2),
            "chronic_ewma": round(chronic_ewma, 2),
            "risk_level": "insufficient_data",
            "interpretation": "No chronic training load to compare against.",
        }

    acwr = round(acute_ewma / chronic_ewma, 2)

    # Spike detection: find any single day > 110% of max in prior 28 days
    spikes = []
    for i in range(28, len(daily_distances)):
        prior_max = max(daily_distances[max(0, i - 28) : i])
        if prior_max > 0 and daily_distances[i] > prior_max * 1.1:
            spikes.append(
                {
                    "day_index": i,
                    "distance_km": round(daily_distances[i], 1),
                    "prior_max_km": round(prior_max, 1),
                    "spike_pct": round((daily_distances[i] - prior_max) / prior_max * 100, 1),
                }
            )

    # Consecutive hard days (>= median * 1.5 for 3+ days in a row)
    non_zero = [d for d in daily_distances if d > 0]
    median_distance = sorted(non_zero)[len(non_zero) // 2] if non_zero else 0
    threshold = median_distance * 1.5
    consecutive_hard = 0
    max_consecutive_hard = 0
    for d in daily_distances[-14:]:  # last 2 weeks
        if d >= threshold:
            consecutive_hard += 1
            max_consecutive_hard = max(max_consecutive_hard, consecutive_hard)
        else:
            consecutive_hard = 0

    # Risk classification
    if acwr < 0.8:
        risk_level = "undertraining"
        interpretation = "EWMA training load below chronic average. Risk of detraining."
    elif acwr <= 1.3:
        risk_level = "optimal"
        interpretation = "EWMA ACWR in optimal range (0.8-1.3)."
    elif acwr <= 1.5:
        risk_level = "elevated"
        interpretation = "EWMA ACWR elevated (>1.3). Monitor recovery closely."
    else:
        risk_level = "high"
        interpretation = "EWMA ACWR high (>1.5). Significant injury risk."

    if spikes:
        risk_level = max(risk_level, "elevated", key=["undertraining", "optimal", "elevated", "high"].index)
        interpretation += f" {len(spikes)} single-session spike(s) detected in recent history."

    if max_consecutive_hard >= 3:
        interpretation += f" {max_consecutive_hard} consecutive hard days in last 2 weeks — recovery needed."

    return {
        "acwr_ewma": acwr,
        "acute_ewma": round(acute_ewma, 2),
        "chronic_ewma": round(chronic_ewma, 2),
        "risk_level": risk_level,
        "interpretation": interpretation,
        "spikes": spikes,
        "max_consecutive_hard_days": max_consecutive_hard,
    }
