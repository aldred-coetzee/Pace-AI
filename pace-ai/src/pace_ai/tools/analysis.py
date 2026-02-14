"""Training analysis tools — ACWR, VDOT, Riegel, training zones."""

from __future__ import annotations

import math
from typing import Any


# ── ACWR (Acute:Chronic Workload Ratio) ──────────────────────────────


def calculate_acwr(weekly_distances: list[float]) -> dict[str, Any]:
    """Compute acute:chronic workload ratio from weekly distance data.

    Uses rolling averages: acute = last 1 week, chronic = last 4 weeks.
    Optimal ACWR range: 0.8–1.3 (Gabbett 2016).

    Args:
        weekly_distances: List of weekly distances (most recent last), minimum 4 weeks.

    Returns:
        ACWR value, risk level, monotony, strain, and interpretation.
    """
    if len(weekly_distances) < 4:
        msg = "Need at least 4 weeks of data for ACWR calculation."
        raise ValueError(msg)

    acute = weekly_distances[-1]
    chronic = sum(weekly_distances[-4:]) / 4

    if chronic == 0:
        return {
            "acwr": 0,
            "acute_load": acute,
            "chronic_load": chronic,
            "risk_level": "insufficient_data",
            "interpretation": "No chronic training load to compare against.",
        }

    acwr = round(acute / chronic, 2)

    # Monotony and strain (Foster 1998)
    recent_4 = weekly_distances[-4:]
    mean_load = sum(recent_4) / len(recent_4)
    std_load = (sum((x - mean_load) ** 2 for x in recent_4) / len(recent_4)) ** 0.5
    monotony = round(mean_load / std_load, 2) if std_load > 0 else 0
    strain = round(mean_load * monotony, 1)

    # Risk classification
    if acwr < 0.8:
        risk_level = "undertraining"
        interpretation = "Training load is significantly below your chronic average. Risk of detraining."
    elif acwr <= 1.3:
        risk_level = "optimal"
        interpretation = "Training load is in the optimal range (0.8–1.3). Good balance of stimulus and recovery."
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
        "monotony": monotony,
        "strain": strain,
        "week_over_week_change_pct": round((acute - weekly_distances[-2]) / weekly_distances[-2] * 100, 1)
        if weekly_distances[-2] > 0
        else None,
    }


# ── VDOT (Jack Daniels' Running Formula) ────────────────────────────


def _vdot_from_time(distance_m: float, time_seconds: float) -> float:
    """Estimate VDOT from a race result using the Daniels/Gilbert formula.

    Based on the oxygen cost and VO2max fraction curves.
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


def predict_race_time(recent_race_distance: str, recent_race_time: str, target_distance: str) -> dict[str, Any]:
    """Predict race time using VDOT model.

    Args:
        recent_race_distance: Distance of recent race (e.g. "5k", "10k", "half marathon").
        recent_race_time: Finish time of recent race (H:MM:SS or M:SS).
        target_distance: Target race distance to predict.

    Returns:
        Predicted time, VDOT, and equivalent performances.
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

    # Equivalent performances at all distances
    equivalents = {}
    for name, dist in RACE_DISTANCES.items():
        eq_seconds = _time_from_vdot(vdot, dist)
        equivalents[name] = format_time(eq_seconds)

    return {
        "vdot": vdot,
        "predicted_time": format_time(predicted_seconds),
        "predicted_seconds": predicted_seconds,
        "riegel_predicted_time": format_time(riegel_seconds),
        "riegel_predicted_seconds": riegel_seconds,
        "source_race": {"distance": recent_race_distance, "time": recent_race_time},
        "target_distance": target_distance,
        "equivalent_performances": equivalents,
    }


# ── Training Zones (Daniels) ────────────────────────────────────────


def calculate_training_zones(threshold_pace_per_km: str | None = None, threshold_hr: int | None = None, vdot: float | None = None) -> dict[str, Any]:
    """Calculate Daniels' training zones from a threshold reference.

    Provide at least one of: threshold_pace_per_km, threshold_hr, or vdot.

    Args:
        threshold_pace_per_km: Threshold (lactate/tempo) pace as M:SS per km.
        threshold_hr: Threshold heart rate in bpm.
        vdot: VDOT value (overrides pace-based calculation).

    Returns:
        Training zones with pace and/or HR ranges.
    """
    from pace_ai.tools.goals import parse_time

    zones: dict[str, Any] = {}

    if threshold_pace_per_km is not None:
        threshold_secs = parse_time(threshold_pace_per_km)
        # Daniels' zone multipliers relative to threshold pace (T pace = 1.0)
        # Faster pace = lower seconds/km
        zone_multipliers = {
            "easy": (1.20, 1.35),       # 20-35% slower than threshold
            "marathon": (1.08, 1.15),    # 8-15% slower than threshold
            "threshold": (0.97, 1.03),   # ~threshold pace
            "interval": (0.88, 0.93),    # 7-12% faster than threshold
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
