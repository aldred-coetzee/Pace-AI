"""Environmental adjustment calculations — heat and altitude pace corrections."""

from __future__ import annotations

from typing import Any


def calculate_heat_adjustment(
    temperature_f: float | None = None,
    temperature_c: float | None = None,
    dew_point_f: float | None = None,
    dew_point_c: float | None = None,
) -> dict[str, Any]:
    """Calculate pace adjustment for heat and humidity.

    Uses the temperature + dew point method from running science literature.
    At a combined value (F) of 100, effect is minimal. At 150+, expect 4.5-6% slower.

    Provide temperature in either F or C (F takes precedence). Dew point is optional
    but improves accuracy.

    Args:
        temperature_f: Temperature in Fahrenheit.
        temperature_c: Temperature in Celsius.
        dew_point_f: Dew point in Fahrenheit.
        dew_point_c: Dew point in Celsius.

    Returns:
        Adjustment factor, slowdown percentage, and coaching guidance.
    """
    # Resolve temperature to Fahrenheit
    if temperature_f is not None:
        temp_f = temperature_f
    elif temperature_c is not None:
        temp_f = temperature_c * 9 / 5 + 32
    else:
        msg = "Provide temperature_f or temperature_c."
        raise ValueError(msg)

    # Resolve dew point (default to temp - 20F if unknown)
    if dew_point_f is not None:
        dp_f = dew_point_f
    elif dew_point_c is not None:
        dp_f = dew_point_c * 9 / 5 + 32
    else:
        dp_f = temp_f - 20  # Rough estimate when humidity is unknown

    combined = temp_f + dp_f

    # Piecewise slowdown model (based on Running Writings / VDOT adjustment data)
    if combined <= 100:
        slowdown_pct = 0.0
    elif combined <= 120:
        slowdown_pct = (combined - 100) * 0.05  # 0-1%
    elif combined <= 140:
        slowdown_pct = 1.0 + (combined - 120) * 0.1  # 1-3%
    elif combined <= 160:
        slowdown_pct = 3.0 + (combined - 140) * 0.15  # 3-6%
    else:
        slowdown_pct = 6.0 + (combined - 160) * 0.2  # 6%+, danger zone

    slowdown_pct = round(slowdown_pct, 1)
    adjustment_factor = round(1 + slowdown_pct / 100, 4)

    # Guidance
    if slowdown_pct < 1:
        risk = "minimal"
        guidance = "Normal training. Hydrate as usual."
    elif slowdown_pct < 3:
        risk = "moderate"
        guidance = "Run by effort, not pace. Easy runs will feel harder. Add 15-30 sec/km."
    elif slowdown_pct < 6:
        risk = "high"
        guidance = "Run by heart rate or RPE only. Ignore pace targets. Shorten long runs or shift to early morning."
    else:
        risk = "extreme"
        guidance = "Consider moving workout indoors or cross-training. Heat illness risk is significant."

    return {
        "temperature_f": round(temp_f, 1),
        "dew_point_f": round(dp_f, 1),
        "combined_value": round(combined, 1),
        "slowdown_pct": slowdown_pct,
        "adjustment_factor": adjustment_factor,
        "risk_level": risk,
        "guidance": guidance,
    }


def calculate_altitude_adjustment(
    altitude_ft: float | None = None,
    altitude_m: float | None = None,
) -> dict[str, Any]:
    """Calculate pace adjustment for altitude.

    Performance declines ~2% per 1,000 feet above 3,000 feet (Daniels, Buskirk 1966).
    VO2max drops 3% per 1,000 ft above ~5,000 ft. Actual race performance impact is
    less than VO2max drop due to reduced air resistance.

    Args:
        altitude_ft: Altitude in feet.
        altitude_m: Altitude in meters.

    Returns:
        Adjustment factor, slowdown percentage, and acclimatization guidance.
    """
    if altitude_ft is not None:
        alt_ft = altitude_ft
    elif altitude_m is not None:
        alt_ft = altitude_m * 3.28084
    else:
        msg = "Provide altitude_ft or altitude_m."
        raise ValueError(msg)

    # No significant effect below 3,000 ft
    if alt_ft <= 3000:
        return {
            "altitude_ft": round(alt_ft, 0),
            "altitude_m": round(alt_ft / 3.28084, 0),
            "slowdown_pct": 0.0,
            "adjustment_factor": 1.0,
            "vo2max_reduction_pct": 0.0,
            "acclimatization_days": 0,
            "guidance": "No altitude adjustment needed.",
        }

    feet_above_3000 = alt_ft - 3000
    # ~2% performance slowdown per 1,000 ft above 3,000 ft
    slowdown_pct = round(feet_above_3000 / 1000 * 2, 1)
    # VO2max drops more aggressively (~3% per 1,000 ft above ~5,000 ft)
    vo2max_reduction = round(max(0, (alt_ft - 5000) / 1000 * 3), 1)
    adjustment_factor = round(1 + slowdown_pct / 100, 4)

    # Acclimatization time (rough: 1-2 days per 1,000 ft above 5,000 ft)
    acclimatization_days = 2 if alt_ft <= 5000 else 2 + round((alt_ft - 5000) / 1000 * 1.5)

    # Guidance
    if slowdown_pct < 3:
        guidance = "Mild altitude. Run by effort for the first few days. Expect slight pace slowdown."
    elif slowdown_pct < 6:
        guidance = (
            "Moderate altitude. Run by HR/RPE, not pace. Stay hydrated. "
            "Reduce intensity for 3-5 days while acclimatizing."
        )
    else:
        guidance = (
            "High altitude. Significant VO2max reduction. "
            "Cut volume by 20-30% for the first week. Avoid hard sessions for 5+ days."
        )

    return {
        "altitude_ft": round(alt_ft, 0),
        "altitude_m": round(alt_ft / 3.28084, 0),
        "slowdown_pct": slowdown_pct,
        "adjustment_factor": adjustment_factor,
        "vo2max_reduction_pct": vo2max_reduction,
        "acclimatization_days": acclimatization_days,
        "guidance": guidance,
    }
