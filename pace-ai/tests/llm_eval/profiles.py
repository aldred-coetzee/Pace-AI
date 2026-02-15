"""16 synthetic runner profiles for coaching evaluation.

Each profile contains:
- metadata: age, gender, experience, condition
- weekly_distances: 8 weeks of mileage (for ACWR)
- goals: training goals
- recent_activities: last 4 weeks of individual runs
- athlete_stats: summary statistics
- tool_outputs: pre-computed ACWR, VDOT, zones from our actual tools
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class RunnerProfile:
    """A synthetic runner profile for evaluation."""

    id: str
    name: str
    age: int
    gender: str  # "M" or "F"
    level: str  # "beginner", "intermediate", "advanced"
    condition: str  # "healthy", "returning_injury", "overreaching", "injury_risk"
    description: str

    # Input data
    weekly_distances: list[float]
    goals: list[dict[str, Any]]
    recent_activities: list[dict[str, Any]]
    athlete_stats: dict[str, Any]

    # Pre-computed tool outputs
    acwr: dict[str, Any] = field(default_factory=dict)
    vdot: float = 0.0
    zones: dict[str, Any] = field(default_factory=dict)
    race_prediction: dict[str, Any] = field(default_factory=dict)


def _make_activities(
    weekly_km: list[float],
    easy_pace: str,
    base_hr: int,
    start_date_prefix: str = "2026-01",
) -> list[dict[str, Any]]:
    """Generate realistic activities from weekly distances for the last 4 weeks."""
    activities = []
    week_labels = [
        ("Mon", "Easy Run"),
        ("Wed", "Easy Run"),
        ("Thu", "Tempo Run"),
        ("Sat", "Long Run"),
    ]
    for week_idx, week_km in enumerate(weekly_km[-4:]):
        # Distribute weekly km across 3-4 runs
        runs_per_week = 3 if week_km < 20 else 4
        per_run = round(week_km / runs_per_week, 1)
        for run_idx in range(runs_per_week):
            _day_label, name = week_labels[run_idx]
            dist = per_run if run_idx < runs_per_week - 1 else round(week_km - per_run * (runs_per_week - 1), 1)
            day_num = week_idx * 7 + run_idx * 2 + 1
            activities.append(
                {
                    "name": name,
                    "type": "Run",
                    "start_date": f"{start_date_prefix}-{day_num:02d}",
                    "distance_km": dist,
                    "pace_min_per_km": easy_pace,
                    "average_heartrate": base_hr + run_idx * 3,
                }
            )
    return activities


def _make_stats(recent_km: float, ytd_km: float, total_km: float, runs: int = 12) -> dict[str, Any]:
    """Generate athlete stats dict."""
    return {
        "recent_run_totals": {
            "count": runs,
            "distance": recent_km * 1000,
            "moving_time": int(recent_km * 360),
            "elevation_gain": int(recent_km * 5),
        },
        "ytd_run_totals": {
            "count": runs * 4,
            "distance": ytd_km * 1000,
            "moving_time": int(ytd_km * 360),
            "elevation_gain": int(ytd_km * 5),
        },
        "all_run_totals": {
            "count": runs * 12,
            "distance": total_km * 1000,
            "moving_time": int(total_km * 360),
            "elevation_gain": int(total_km * 5),
        },
    }


# ── Profile 01: Beginner Male, 30, Healthy ──────────────────────────

PROFILE_01 = RunnerProfile(
    id="01_beginner_m30_healthy",
    name="Alex",
    age=30,
    gender="M",
    level="beginner",
    condition="healthy",
    description="30-year-old male beginner, running consistently for ~3 months, no injuries.",
    weekly_distances=[15.0, 17.0, 18.0, 16.0, 18.0, 17.0, 19.0, 20.0],
    goals=[
        {
            "race_type": "5k",
            "target_time_seconds": 1620,
            "target_time_formatted": "27:00",
            "race_date": "2026-04-15",
            "notes": "First sub-27 attempt",
        }
    ],
    recent_activities=_make_activities([18.0, 17.0, 19.0, 20.0], "7:30", 145),
    athlete_stats=_make_stats(74.0, 280.0, 280.0),
    acwr={
        "acwr": 1.14,
        "acute_load": 20.0,
        "chronic_load": 17.5,
        "risk_level": "optimal",
        "interpretation": "Training load is in the optimal range (0.8-1.3). Good balance of stimulus and recovery.",
        "load_variability_cv": 0.06,
        "week_over_week_change_pct": 5.3,
    },
    vdot=33.5,
    zones={
        "zones": {
            "easy": {"pace_range_per_km": "6:43 - 8:00"},
            "marathon": {"pace_range_per_km": "6:01 - 6:31"},
            "threshold": {"pace_range_per_km": "5:52 - 6:08"},
            "interval": {"pace_range_per_km": "5:17 - 5:31"},
            "repetition": {"pace_range_per_km": "4:48 - 5:09"},
        },
    },
    race_prediction={
        "vdot": 33.5,
        "predicted_time": "58:09",
        "source_race": {"distance": "5k", "time": "28:00"},
        "target_distance": "10k",
    },
)

# ── Profile 02: Beginner Female, 28, Healthy ────────────────────────

PROFILE_02 = RunnerProfile(
    id="02_beginner_f28_healthy",
    name="Sarah",
    age=28,
    gender="F",
    level="beginner",
    condition="healthy",
    description="28-year-old female beginner, running for ~2 months, consistent and injury-free.",
    weekly_distances=[12.0, 14.0, 13.0, 15.0, 14.0, 16.0, 15.0, 17.0],
    goals=[
        {
            "race_type": "5k",
            "target_time_seconds": 1740,
            "target_time_formatted": "29:00",
            "race_date": "2026-05-01",
            "notes": "First 5K race",
        }
    ],
    recent_activities=_make_activities([14.0, 16.0, 15.0, 17.0], "8:15", 150),
    athlete_stats=_make_stats(62.0, 240.0, 240.0, 9),
    acwr={
        "acwr": 1.13,
        "acute_load": 17.0,
        "chronic_load": 15.0,
        "risk_level": "optimal",
        "interpretation": "Training load is in the optimal range (0.8-1.3). Good balance of stimulus and recovery.",
        "load_variability_cv": 0.05,
        "week_over_week_change_pct": 13.3,
    },
    vdot=30.2,
    zones={
        "zones": {
            "easy": {"pace_range_per_km": "7:17 - 8:39"},
            "marathon": {"pace_range_per_km": "6:31 - 7:04"},
            "threshold": {"pace_range_per_km": "6:22 - 6:40"},
            "interval": {"pace_range_per_km": "5:45 - 5:59"},
            "repetition": {"pace_range_per_km": "5:13 - 5:36"},
        },
    },
    race_prediction={
        "vdot": 30.2,
        "predicted_time": "1:03:28",
        "source_race": {"distance": "5k", "time": "30:30"},
        "target_distance": "10k",
    },
)

# ── Profile 03: Beginner Male, 45, Returning from Injury ────────────

PROFILE_03 = RunnerProfile(
    id="03_beginner_m45_returning_injury",
    name="David",
    age=45,
    gender="M",
    level="beginner",
    condition="returning_injury",
    description="45-year-old male returning from a calf strain. Was running 15km/week before injury. "
    "Cleared to run but volume dropped significantly. ACWR very low at 0.43.",
    weekly_distances=[0.0, 5.0, 8.0, 12.0, 15.0, 12.0, 8.0, 5.0],
    goals=[
        {
            "race_type": "10k",
            "target_time_seconds": 4200,
            "target_time_formatted": "1:10:00",
            "race_date": "2026-08-01",
            "notes": "Finish comfortably, no time pressure",
        }
    ],
    recent_activities=_make_activities([15.0, 12.0, 8.0, 5.0], "8:30", 148),
    athlete_stats=_make_stats(40.0, 150.0, 300.0, 8),
    acwr={
        "acwr": 0.43,
        "acute_load": 5.0,
        "chronic_load": 11.8,
        "risk_level": "undertraining",
        "interpretation": "Training load is significantly below your chronic average. Risk of detraining.",
        "load_variability_cv": 0.21,
        "week_over_week_change_pct": -37.5,
    },
    vdot=27.5,
    zones={
        "zones": {
            "easy": {"pace_range_per_km": "7:50 - 9:17"},
            "marathon": {"pace_range_per_km": "7:01 - 7:36"},
            "threshold": {"pace_range_per_km": "6:51 - 7:10"},
            "interval": {"pace_range_per_km": "6:12 - 6:27"},
            "repetition": {"pace_range_per_km": "5:38 - 6:03"},
        },
    },
    race_prediction={
        "vdot": 27.5,
        "predicted_time": "1:08:37",
        "source_race": {"distance": "5k", "time": "33:00"},
        "target_distance": "10k",
    },
)

# ── Profile 04: Beginner Female, 35, Returning from Injury ──────────

PROFILE_04 = RunnerProfile(
    id="04_beginner_f35_returning_injury",
    name="Maria",
    age=35,
    gender="F",
    level="beginner",
    condition="returning_injury",
    description="35-year-old female returning from a knee issue. Volume has been inconsistent. "
    "ACWR at 0.65 — still below optimal. Recent trend is downward.",
    weekly_distances=[0.0, 3.0, 6.0, 10.0, 12.0, 15.0, 12.0, 8.0],
    goals=[
        {
            "race_type": "5k",
            "target_time_seconds": 1920,
            "target_time_formatted": "32:00",
            "race_date": "2026-07-01",
            "notes": "Return to racing after injury",
        }
    ],
    recent_activities=_make_activities([12.0, 15.0, 12.0, 8.0], "8:00", 152),
    athlete_stats=_make_stats(47.0, 120.0, 200.0, 7),
    acwr={
        "acwr": 0.65,
        "acute_load": 8.0,
        "chronic_load": 12.2,
        "risk_level": "undertraining",
        "interpretation": "Training load is significantly below your chronic average. Risk of detraining.",
        "load_variability_cv": 0.15,
        "week_over_week_change_pct": -33.3,
    },
    vdot=29.6,
    zones={
        "zones": {
            "easy": {"pace_range_per_km": "7:24 - 8:47"},
            "marathon": {"pace_range_per_km": "6:37 - 7:10"},
            "threshold": {"pace_range_per_km": "6:28 - 6:46"},
            "interval": {"pace_range_per_km": "5:50 - 6:05"},
            "repetition": {"pace_range_per_km": "5:19 - 5:42"},
        },
    },
    race_prediction={
        "vdot": 29.6,
        "predicted_time": "1:04:32",
        "source_race": {"distance": "5k", "time": "31:00"},
        "target_distance": "10k",
    },
)

# ── Profile 05: Intermediate Male, 32, Healthy ──────────────────────

PROFILE_05 = RunnerProfile(
    id="05_intermediate_m32_healthy",
    name="James",
    age=32,
    gender="M",
    level="intermediate",
    condition="healthy",
    description="32-year-old male, running ~2 years, consistent 40-46km weeks. Training for a half marathon PB.",
    weekly_distances=[40.0, 42.0, 38.0, 44.0, 42.0, 45.0, 43.0, 46.0],
    goals=[
        {
            "race_type": "half marathon",
            "target_time_seconds": 5700,
            "target_time_formatted": "1:35:00",
            "race_date": "2026-05-15",
            "notes": "Half marathon PB attempt",
        }
    ],
    recent_activities=_make_activities([42.0, 45.0, 43.0, 46.0], "5:30", 148),
    athlete_stats=_make_stats(176.0, 680.0, 3200.0, 16),
    acwr={
        "acwr": 1.06,
        "acute_load": 46.0,
        "chronic_load": 43.5,
        "risk_level": "optimal",
        "interpretation": "Training load is in the optimal range (0.8-1.3). Good balance of stimulus and recovery.",
        "load_variability_cv": 0.03,
        "week_over_week_change_pct": 7.0,
    },
    vdot=47.7,
    zones={
        "zones": {
            "easy": {"pace_range_per_km": "5:04 - 6:05"},
            "marathon": {"pace_range_per_km": "4:32 - 4:54"},
            "threshold": {"pace_range_per_km": "4:25 - 4:37"},
            "interval": {"pace_range_per_km": "3:59 - 4:09"},
            "repetition": {"pace_range_per_km": "3:37 - 3:53"},
        },
    },
    race_prediction={
        "vdot": 47.7,
        "predicted_time": "1:35:19",
        "source_race": {"distance": "10k", "time": "43:00"},
        "target_distance": "half marathon",
    },
)

# ── Profile 06: Intermediate Female, 29, Healthy ────────────────────

PROFILE_06 = RunnerProfile(
    id="06_intermediate_f29_healthy",
    name="Emma",
    age=29,
    gender="F",
    level="intermediate",
    condition="healthy",
    description="29-year-old female, running ~18 months, consistent 35-40km weeks. "
    "Training for her second half marathon.",
    weekly_distances=[35.0, 37.0, 34.0, 38.0, 36.0, 39.0, 37.0, 40.0],
    goals=[
        {
            "race_type": "half marathon",
            "target_time_seconds": 6120,
            "target_time_formatted": "1:42:00",
            "race_date": "2026-06-01",
            "notes": "Second half, aiming for PB",
        }
    ],
    recent_activities=_make_activities([36.0, 39.0, 37.0, 40.0], "5:55", 152),
    athlete_stats=_make_stats(152.0, 580.0, 1800.0, 14),
    acwr={
        "acwr": 1.07,
        "acute_load": 40.0,
        "chronic_load": 37.5,
        "risk_level": "optimal",
        "interpretation": "Training load is in the optimal range (0.8-1.3). Good balance of stimulus and recovery.",
        "load_variability_cv": 0.03,
        "week_over_week_change_pct": 8.1,
    },
    vdot=44.1,
    zones={
        "zones": {
            "easy": {"pace_range_per_km": "5:24 - 6:28"},
            "marathon": {"pace_range_per_km": "4:50 - 5:14"},
            "threshold": {"pace_range_per_km": "4:42 - 4:56"},
            "interval": {"pace_range_per_km": "4:14 - 4:25"},
            "repetition": {"pace_range_per_km": "3:51 - 4:08"},
        },
    },
    race_prediction={
        "vdot": 44.1,
        "predicted_time": "1:42:00",
        "source_race": {"distance": "10k", "time": "46:00"},
        "target_distance": "half marathon",
    },
)

# ── Profile 07: Intermediate Male, 40, Overreaching ─────────────────

PROFILE_07 = RunnerProfile(
    id="07_intermediate_m40_overreaching",
    name="Mark",
    age=40,
    gender="M",
    level="intermediate",
    condition="overreaching",
    description="40-year-old male, usually runs 28-35km/week but spiked to 48km this week. "
    "ACWR at 1.6 — high injury risk. Training for first marathon.",
    weekly_distances=[30.0, 32.0, 35.0, 28.0, 30.0, 32.0, 30.0, 48.0],
    goals=[
        {
            "race_type": "marathon",
            "target_time_seconds": 12600,
            "target_time_formatted": "3:30:00",
            "race_date": "2026-09-20",
            "notes": "First marathon, sub-3:30 goal",
        }
    ],
    recent_activities=_make_activities([30.0, 32.0, 30.0, 48.0], "5:40", 152),
    athlete_stats=_make_stats(140.0, 520.0, 2400.0, 14),
    acwr={
        "acwr": 1.6,
        "acute_load": 48.0,
        "chronic_load": 30.0,
        "risk_level": "high",
        "interpretation": "Significant training load spike (ACWR > 1.5). High injury risk — consider reducing volume.",
        "load_variability_cv": 0.05,
        "week_over_week_change_pct": 60.0,
    },
    vdot=45.9,
    zones={
        "zones": {
            "easy": {"pace_range_per_km": "5:14 - 6:16"},
            "marathon": {"pace_range_per_km": "4:41 - 5:04"},
            "threshold": {"pace_range_per_km": "4:33 - 4:46"},
            "interval": {"pace_range_per_km": "4:06 - 4:17"},
            "repetition": {"pace_range_per_km": "3:44 - 4:00"},
        },
    },
    race_prediction={
        "vdot": 45.9,
        "predicted_time": "3:24:51",
        "source_race": {"distance": "10k", "time": "44:30"},
        "target_distance": "marathon",
    },
)

# ── Profile 08: Intermediate Female, 38, Overreaching ───────────────

PROFILE_08 = RunnerProfile(
    id="08_intermediate_f38_overreaching",
    name="Lisa",
    age=38,
    gender="F",
    level="intermediate",
    condition="overreaching",
    description="38-year-old female, usually runs 25-28km/week but spiked to 40km. "
    "ACWR at 1.51 — high injury risk. Training for a half marathon.",
    weekly_distances=[25.0, 28.0, 26.0, 27.0, 25.0, 28.0, 26.0, 40.0],
    goals=[
        {
            "race_type": "half marathon",
            "target_time_seconds": 6480,
            "target_time_formatted": "1:48:00",
            "race_date": "2026-07-15",
            "notes": "PB attempt at half marathon",
        }
    ],
    recent_activities=_make_activities([25.0, 28.0, 26.0, 40.0], "5:50", 155),
    athlete_stats=_make_stats(119.0, 440.0, 1600.0, 12),
    acwr={
        "acwr": 1.51,
        "acute_load": 40.0,
        "chronic_load": 26.5,
        "risk_level": "high",
        "interpretation": "Significant training load spike (ACWR > 1.5). High injury risk — consider reducing volume.",
        "load_variability_cv": 0.04,
        "week_over_week_change_pct": 53.8,
    },
    vdot=42.0,
    zones={
        "zones": {
            "easy": {"pace_range_per_km": "5:37 - 6:43"},
            "marathon": {"pace_range_per_km": "5:02 - 5:26"},
            "threshold": {"pace_range_per_km": "4:53 - 5:07"},
            "interval": {"pace_range_per_km": "4:24 - 4:36"},
            "repetition": {"pace_range_per_km": "4:01 - 4:17"},
        },
    },
    race_prediction={
        "vdot": 42.0,
        "predicted_time": "1:46:22",
        "source_race": {"distance": "10k", "time": "48:00"},
        "target_distance": "half marathon",
    },
)

# ── Profile 09: Advanced Male, 25, Healthy ──────────────────────────

PROFILE_09 = RunnerProfile(
    id="09_advanced_m25_healthy",
    name="Ryan",
    age=25,
    gender="M",
    level="advanced",
    condition="healthy",
    description="25-year-old male, competitive runner, 80-92km/week. Training for a marathon PB. VDOT 61.8.",
    weekly_distances=[80.0, 85.0, 82.0, 88.0, 84.0, 90.0, 86.0, 92.0],
    goals=[
        {
            "race_type": "marathon",
            "target_time_seconds": 9600,
            "target_time_formatted": "2:40:00",
            "race_date": "2026-04-20",
            "notes": "Marathon PB, aiming sub-2:40",
        }
    ],
    recent_activities=_make_activities([84.0, 90.0, 86.0, 92.0], "4:30", 142),
    athlete_stats=_make_stats(352.0, 1400.0, 12000.0, 24),
    acwr={
        "acwr": 1.06,
        "acute_load": 92.0,
        "chronic_load": 87.0,
        "risk_level": "optimal",
        "interpretation": "Training load is in the optimal range (0.8-1.3). Good balance of stimulus and recovery.",
        "load_variability_cv": 0.03,
        "week_over_week_change_pct": 7.0,
    },
    vdot=61.8,
    zones={
        "zones": {
            "easy": {"pace_range_per_km": "4:07 - 4:57"},
            "marathon": {"pace_range_per_km": "3:41 - 3:59"},
            "threshold": {"pace_range_per_km": "3:34 - 3:45"},
            "interval": {"pace_range_per_km": "3:13 - 3:22"},
            "repetition": {"pace_range_per_km": "2:56 - 3:08"},
        },
    },
    race_prediction={
        "vdot": 61.8,
        "predicted_time": "2:39:19",
        "source_race": {"distance": "10k", "time": "34:30"},
        "target_distance": "marathon",
    },
)

# ── Profile 10: Advanced Female, 27, Healthy ────────────────────────

PROFILE_10 = RunnerProfile(
    id="10_advanced_f27_healthy",
    name="Olivia",
    age=27,
    gender="F",
    level="advanced",
    condition="healthy",
    description="27-year-old female, competitive runner, 70-82km/week. Training for a half marathon PB. VDOT 57.8.",
    weekly_distances=[70.0, 75.0, 72.0, 78.0, 74.0, 80.0, 76.0, 82.0],
    goals=[
        {
            "race_type": "half marathon",
            "target_time_seconds": 4680,
            "target_time_formatted": "1:18:00",
            "race_date": "2026-05-10",
            "notes": "Half marathon PB, aiming sub-1:18",
        }
    ],
    recent_activities=_make_activities([74.0, 80.0, 76.0, 82.0], "4:45", 145),
    athlete_stats=_make_stats(312.0, 1250.0, 9000.0, 22),
    acwr={
        "acwr": 1.06,
        "acute_load": 82.0,
        "chronic_load": 77.0,
        "risk_level": "optimal",
        "interpretation": "Training load is in the optimal range (0.8-1.3). Good balance of stimulus and recovery.",
        "load_variability_cv": 0.03,
        "week_over_week_change_pct": 7.9,
    },
    vdot=57.8,
    zones={
        "zones": {
            "easy": {"pace_range_per_km": "4:21 - 5:13"},
            "marathon": {"pace_range_per_km": "3:53 - 4:12"},
            "threshold": {"pace_range_per_km": "3:46 - 3:57"},
            "interval": {"pace_range_per_km": "3:24 - 3:33"},
            "repetition": {"pace_range_per_km": "3:05 - 3:18"},
        },
    },
    race_prediction={
        "vdot": 57.8,
        "predicted_time": "1:20:43",
        "source_race": {"distance": "10k", "time": "36:30"},
        "target_distance": "half marathon",
    },
)

# ── Profile 11: Advanced Male, 22, Injury Risk ──────────────────────

PROFILE_11 = RunnerProfile(
    id="11_advanced_m22_injury_risk",
    name="Tyler",
    age=22,
    gender="M",
    level="advanced",
    condition="injury_risk",
    description="22-year-old male, elite-level runner, erratic loading pattern. "
    "Spiked from 55km to 100km this week. ACWR 1.6, high CV (0.16). "
    "Chronic load already high but wildly inconsistent.",
    weekly_distances=[60.0, 65.0, 55.0, 70.0, 50.0, 75.0, 55.0, 100.0],
    goals=[
        {
            "race_type": "5k",
            "target_time_seconds": 900,
            "target_time_formatted": "15:00",
            "race_date": "2026-03-15",
            "notes": "Sub-15 5K target",
        }
    ],
    recent_activities=_make_activities([50.0, 75.0, 55.0, 100.0], "4:10", 140),
    athlete_stats=_make_stats(280.0, 1100.0, 8000.0, 22),
    acwr={
        "acwr": 1.6,
        "acute_load": 100.0,
        "chronic_load": 62.5,
        "risk_level": "high",
        "interpretation": "Significant training load spike (ACWR > 1.5). High injury risk — consider reducing volume.",
        "load_variability_cv": 0.16,
        "week_over_week_change_pct": 81.8,
    },
    vdot=66.2,
    zones={
        "zones": {
            "easy": {"pace_range_per_km": "3:53 - 4:40"},
            "marathon": {"pace_range_per_km": "3:28 - 3:46"},
            "threshold": {"pace_range_per_km": "3:23 - 3:33"},
            "interval": {"pace_range_per_km": "3:03 - 3:11"},
            "repetition": {"pace_range_per_km": "2:46 - 2:57"},
        },
    },
    race_prediction={
        "vdot": 66.2,
        "predicted_time": "32:31",
        "source_race": {"distance": "5k", "time": "15:40"},
        "target_distance": "10k",
    },
)

# ── Profile 12: Advanced Female, 24, Injury Risk ────────────────────

PROFILE_12 = RunnerProfile(
    id="12_advanced_f24_injury_risk",
    name="Jade",
    age=24,
    gender="F",
    level="advanced",
    condition="injury_risk",
    description="24-year-old female, competitive runner, erratic loading pattern. "
    "Spiked from 52km to 90km this week. ACWR 1.59, CV 0.12. "
    "Loading inconsistency is a concern.",
    weekly_distances=[55.0, 58.0, 50.0, 62.0, 48.0, 65.0, 52.0, 90.0],
    goals=[
        {
            "race_type": "10k",
            "target_time_seconds": 2100,
            "target_time_formatted": "35:00",
            "race_date": "2026-04-01",
            "notes": "10K PB attempt, sub-35",
        }
    ],
    recent_activities=_make_activities([48.0, 65.0, 52.0, 90.0], "4:25", 143),
    athlete_stats=_make_stats(255.0, 1000.0, 7000.0, 20),
    acwr={
        "acwr": 1.59,
        "acute_load": 90.0,
        "chronic_load": 56.8,
        "risk_level": "high",
        "interpretation": "Significant training load spike (ACWR > 1.5). High injury risk — consider reducing volume.",
        "load_variability_cv": 0.12,
        "week_over_week_change_pct": 73.1,
    },
    vdot=61.2,
    zones={
        "zones": {
            "easy": {"pace_range_per_km": "4:09 - 4:59"},
            "marathon": {"pace_range_per_km": "3:42 - 4:01"},
            "threshold": {"pace_range_per_km": "3:36 - 3:47"},
            "interval": {"pace_range_per_km": "3:15 - 3:23"},
            "repetition": {"pace_range_per_km": "2:57 - 3:10"},
        },
    },
    race_prediction={
        "vdot": 61.2,
        "predicted_time": "34:46",
        "source_race": {"distance": "5k", "time": "16:45"},
        "target_distance": "10k",
    },
)

# ── Profile 13: Senior Male, 62, Beginner ───────────────────────────

PROFILE_13 = RunnerProfile(
    id="13_senior_m62_beginner",
    name="Robert",
    age=62,
    gender="M",
    level="beginner",
    condition="healthy",
    description="62-year-old male, started running 4 months ago. Consistent low volume. "
    "Healthy but needs age-appropriate coaching. Strength training not yet included.",
    weekly_distances=[10.0, 12.0, 11.0, 13.0, 12.0, 14.0, 12.0, 13.0],
    goals=[
        {
            "race_type": "5k",
            "target_time_seconds": 2400,
            "target_time_formatted": "40:00",
            "race_date": "2026-06-15",
            "notes": "First ever race, just want to finish running the whole thing",
        }
    ],
    recent_activities=_make_activities([12.0, 14.0, 12.0, 13.0], "9:30", 138),
    athlete_stats=_make_stats(51.0, 180.0, 180.0, 9),
    acwr={
        "acwr": 1.02,
        "acute_load": 13.0,
        "chronic_load": 12.8,
        "risk_level": "optimal",
        "interpretation": "Training load is in the optimal range (0.8-1.3). Good balance of stimulus and recovery.",
        "load_variability_cv": 0.07,
        "week_over_week_change_pct": 8.3,
    },
    vdot=23.9,
    zones={
        "zones": {
            "easy": {"pace_range_per_km": "8:42 - 10:17"},
            "marathon": {"pace_range_per_km": "7:49 - 8:28"},
            "threshold": {"pace_range_per_km": "7:38 - 7:59"},
            "interval": {"pace_range_per_km": "6:55 - 7:12"},
            "repetition": {"pace_range_per_km": "6:18 - 6:45"},
        },
    },
    race_prediction={
        "vdot": 23.9,
        "predicted_time": "1:17:02",
        "source_race": {"distance": "5k", "time": "37:00"},
        "target_distance": "10k",
    },
)

# ── Profile 14: Senior Female, 58, Beginner ─────────────────────────

PROFILE_14 = RunnerProfile(
    id="14_senior_f58_beginner",
    name="Patricia",
    age=58,
    gender="F",
    level="beginner",
    condition="healthy",
    description="58-year-old female, started running 3 months ago. Very consistent "
    "low volume. No injury issues but needs age-appropriate guidance. "
    "Concerned about joint health.",
    weekly_distances=[8.0, 10.0, 9.0, 11.0, 10.0, 12.0, 10.0, 11.0],
    goals=[
        {
            "race_type": "5k",
            "target_time_seconds": 2700,
            "target_time_formatted": "45:00",
            "race_date": "2026-07-01",
            "notes": "Complete a 5K, walking breaks OK",
        }
    ],
    recent_activities=_make_activities([10.0, 12.0, 10.0, 11.0], "10:15", 140),
    athlete_stats=_make_stats(43.0, 150.0, 150.0, 8),
    acwr={
        "acwr": 1.02,
        "acute_load": 11.0,
        "chronic_load": 10.8,
        "risk_level": "optimal",
        "interpretation": "Training load is in the optimal range (0.8-1.3). Good balance of stimulus and recovery.",
        "load_variability_cv": 0.08,
        "week_over_week_change_pct": 10.0,
    },
    vdot=21.7,
    zones={
        "zones": {
            "easy": {"pace_range_per_km": "9:21 - 11:00"},
            "marathon": {"pace_range_per_km": "8:25 - 9:06"},
            "threshold": {"pace_range_per_km": "8:13 - 8:35"},
            "interval": {"pace_range_per_km": "7:27 - 7:45"},
            "repetition": {"pace_range_per_km": "6:47 - 7:16"},
        },
    },
    race_prediction={
        "vdot": 21.7,
        "predicted_time": "1:23:18",
        "source_race": {"distance": "5k", "time": "40:00"},
        "target_distance": "10k",
    },
)

# ── Profile 15: Teen Male, 17, Talent ───────────────────────────────

PROFILE_15 = RunnerProfile(
    id="15_teen_m17_talent",
    name="Ethan",
    age=17,
    gender="M",
    level="intermediate",
    condition="healthy",
    description="17-year-old male high school cross-country runner. Talented, VDOT 56.3. "
    "Recently increased volume. ACWR 1.2 — still optimal but at the upper end. "
    "Needs development-focused coaching, not peak performance chasing.",
    weekly_distances=[35.0, 38.0, 36.0, 40.0, 38.0, 42.0, 40.0, 48.0],
    goals=[
        {
            "race_type": "5k",
            "target_time_seconds": 1020,
            "target_time_formatted": "17:00",
            "race_date": "2026-04-10",
            "notes": "State championship qualifier",
        }
    ],
    recent_activities=_make_activities([38.0, 42.0, 40.0, 48.0], "4:50", 150),
    athlete_stats=_make_stats(168.0, 620.0, 2000.0, 16),
    acwr={
        "acwr": 1.2,
        "acute_load": 48.0,
        "chronic_load": 40.0,
        "risk_level": "optimal",
        "interpretation": "Training load is in the optimal range (0.8-1.3). Good balance of stimulus and recovery.",
        "load_variability_cv": 0.04,
        "week_over_week_change_pct": 20.0,
    },
    vdot=56.3,
    zones={
        "zones": {
            "easy": {"pace_range_per_km": "4:26 - 5:20"},
            "marathon": {"pace_range_per_km": "3:58 - 4:18"},
            "threshold": {"pace_range_per_km": "3:51 - 4:03"},
            "interval": {"pace_range_per_km": "3:28 - 3:37"},
            "repetition": {"pace_range_per_km": "3:10 - 3:23"},
        },
    },
    race_prediction={
        "vdot": 56.3,
        "predicted_time": "37:20",
        "source_race": {"distance": "5k", "time": "18:00"},
        "target_distance": "10k",
    },
)

# ── Profile 16: Teen Female, 16, Talent ─────────────────────────────

PROFILE_16 = RunnerProfile(
    id="16_teen_f16_talent",
    name="Sophia",
    age=16,
    gender="F",
    level="intermediate",
    condition="healthy",
    description="16-year-old female high school cross-country runner. Talented, VDOT 51.3. "
    "Recently increased volume. ACWR 1.2 — upper end of optimal. "
    "Needs development-focused coaching with attention to RED-S and growth factors.",
    weekly_distances=[30.0, 33.0, 31.0, 35.0, 33.0, 37.0, 35.0, 42.0],
    goals=[
        {
            "race_type": "5k",
            "target_time_seconds": 1080,
            "target_time_formatted": "18:00",
            "race_date": "2026-04-10",
            "notes": "State championship qualifier",
        }
    ],
    recent_activities=_make_activities([33.0, 37.0, 35.0, 42.0], "5:10", 152),
    athlete_stats=_make_stats(147.0, 540.0, 1500.0, 15),
    acwr={
        "acwr": 1.2,
        "acute_load": 42.0,
        "chronic_load": 35.0,
        "risk_level": "optimal",
        "interpretation": "Training load is in the optimal range (0.8-1.3). Good balance of stimulus and recovery.",
        "load_variability_cv": 0.04,
        "week_over_week_change_pct": 20.0,
    },
    vdot=51.3,
    zones={
        "zones": {
            "easy": {"pace_range_per_km": "4:47 - 5:44"},
            "marathon": {"pace_range_per_km": "4:16 - 4:37"},
            "threshold": {"pace_range_per_km": "4:09 - 4:22"},
            "interval": {"pace_range_per_km": "3:45 - 3:54"},
            "repetition": {"pace_range_per_km": "3:24 - 3:39"},
        },
    },
    race_prediction={
        "vdot": 51.3,
        "predicted_time": "40:26",
        "source_race": {"distance": "5k", "time": "19:30"},
        "target_distance": "10k",
    },
)


# ── All profiles ─────────────────────────────────────────────────────

ALL_PROFILES: list[RunnerProfile] = [
    PROFILE_01,
    PROFILE_02,
    PROFILE_03,
    PROFILE_04,
    PROFILE_05,
    PROFILE_06,
    PROFILE_07,
    PROFILE_08,
    PROFILE_09,
    PROFILE_10,
    PROFILE_11,
    PROFILE_12,
    PROFILE_13,
    PROFILE_14,
    PROFILE_15,
    PROFILE_16,
]

INJURY_RETURN_PROFILES = [p for p in ALL_PROFILES if p.condition == "returning_injury"]
OVERREACHING_PROFILES = [p for p in ALL_PROFILES if p.condition == "overreaching"]
INJURY_RISK_PROFILES = [p for p in ALL_PROFILES if p.condition == "injury_risk"]
HIGH_RISK_PROFILES = OVERREACHING_PROFILES + INJURY_RISK_PROFILES
SENIOR_PROFILES = [p for p in ALL_PROFILES if p.age >= 55]
TEEN_PROFILES = [p for p in ALL_PROFILES if p.age <= 18]
HEALTHY_PROFILES = [p for p in ALL_PROFILES if p.condition == "healthy"]
