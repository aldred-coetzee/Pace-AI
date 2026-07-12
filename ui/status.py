"""Deterministic status assessment — no LLM calls required.

Replaces the 4 parallel/sequential Claude calls in the status route with
pure Python rule-based logic over the same data gathered by _gather_status_data.
"""

from __future__ import annotations

import re
from datetime import datetime


# ── HTML helpers ──────────────────────────────────────────────────────────────


def render_status_section(
    title: str,
    status: str,
    content_html: str,
    *,
    verdict_text: str | None = None,
) -> str:
    """Render a single status section card to HTML.

    If verdict_text is provided, renders a verdict card instead of a regular section.
    Status values: ok (green), caution (amber), concern (red), info (neutral).
    """
    css_class = f"status-{status}" if status in ("ok", "caution", "concern") else "status-info"

    if verdict_text is not None:
        return (
            f'<div class="status-verdict {css_class}">'
            f'<div class="verdict-label">{verdict_text}</div>'
            f'<div class="status-body"><div class="md-content">{content_html}</div></div>'
            f"</div>"
        )
    else:
        return (
            f'<div class="status-section {css_class}">'
            f'<div class="status-header">'
            f'<span class="status-dot"></span>'
            f'<span class="status-title">{title}</span>'
            f"</div>"
            f'<div class="status-body"><div class="md-content">{content_html}</div></div>'
            f"</div>"
        )


def _table(headers: list[str], rows: list[list[str]]) -> str:
    """Build a simple HTML table."""
    th = "".join(f"<th>{h}</th>" for h in headers)
    body_rows = []
    for row in rows:
        tds = "".join(f"<td>{cell}</td>" for cell in row)
        body_rows.append(f"<tr>{tds}</tr>")
    return (
        f"<table><thead><tr>{th}</tr></thead>"
        f"<tbody>{''.join(body_rows)}</tbody></table>"
    )


# ── Training Load ─────────────────────────────────────────────────────────────


def assess_training_load(weekly_distances: list[dict]) -> tuple[str, str]:
    """Assess training load via ACWR.

    weekly_distances is sorted most-recent-first. Index 0 = current week.
    Returns (status, html).
    """
    if not weekly_distances:
        return "info", "<p>No weekly distance data available.</p>"

    # Current week = index 0; chronic = weeks 2-5 (indices 1-4)
    current_miles = weekly_distances[0].get("distance_miles", 0) or 0
    chronic_weeks = weekly_distances[1:5]
    chronic_miles = [w.get("distance_miles", 0) or 0 for w in chronic_weeks]

    if not chronic_miles or all(m == 0 for m in chronic_miles):
        status = "info"
        acwr_text = "<p>Insufficient chronic training data to calculate ACWR.</p>"
    else:
        chronic_avg = sum(chronic_miles) / len(chronic_miles)
        if chronic_avg > 0:
            acwr = current_miles / chronic_avg
        else:
            acwr = 0.0

        if acwr > 1.5:
            status = "concern"
        elif acwr > 1.2 or (0 < acwr < 0.7):
            status = "caution"
        else:
            status = "ok"

        acwr_text = (
            f"<p>ACWR: <strong>{acwr:.2f}</strong> "
            f"({current_miles:.1f} mi this week / {chronic_avg:.1f} mi chronic avg)</p>"
        )

    # Build last-6-weeks table
    display_weeks = weekly_distances[:6]
    rows = []
    for i, w in enumerate(display_weeks):
        week_start = w.get("week_start", "")
        try:
            d = datetime.strptime(week_start, "%Y-%m-%d").date()
            label = d.strftime("%-d %b")
        except (ValueError, TypeError):
            label = week_start or "?"
        tag = " (current)" if i == 0 else ""
        miles = w.get("distance_miles", 0) or 0
        runs = w.get("activity_count", 0) or 0
        rows.append([f"{label}{tag}", f"{miles:.1f}", str(runs)])

    table = _table(["Week", "Miles", "Runs"], rows)
    html = acwr_text + table
    return status, html


# ── Recent Runs ───────────────────────────────────────────────────────────────


def _parse_z2_ceiling(facts: list[dict]) -> float | None:
    """Extract the Z2 HR upper bound from athlete facts.

    Looks for facts mentioning Z2/zone 2 with a range like "145-165" or "145–165".
    Returns the upper number, or None if not found.
    """
    z2_pattern = re.compile(
        r"(?:z2|zone\s*2)[^\d]*(\d{2,3})\s*[-–]\s*(\d{2,3})",
        re.IGNORECASE,
    )
    for fact in facts:
        text = fact.get("fact", "")
        m = z2_pattern.search(text)
        if m:
            return float(m.group(2))
    return None


def assess_recent_runs(
    activities: list[dict], facts: list[dict]
) -> tuple[str, str]:
    """Assess recent runs, flagging zone drift on easy runs.

    Returns (status, html).
    """
    # Filter to running activities only
    runs = [
        a for a in activities if "run" in (a.get("sport_type") or "").lower()
    ]

    if not runs:
        return "info", "<p>No recent runs found.</p>"

    z2_ceiling = _parse_z2_ceiling(facts)

    # Detect zone drift: easy/recovery/slow run with avg HR above Z2 ceiling
    easy_keywords = {"easy", "recovery", "slow"}
    zone_drift_runs: list[str] = []

    if z2_ceiling is not None:
        for run in runs:
            name_lower = (run.get("name") or "").lower()
            if any(kw in name_lower for kw in easy_keywords):
                hr = run.get("average_hr") or run.get("average_heartrate")
                if hr and float(hr) > z2_ceiling:
                    zone_drift_runs.append(run.get("name", run.get("date", "?")))

    if len(zone_drift_runs) >= 2:
        status = "caution"
        drift_note = (
            f"<p>Zone drift detected on {len(zone_drift_runs)} easy runs "
            f"(HR above Z2 ceiling of {z2_ceiling:.0f}bpm): "
            + ", ".join(zone_drift_runs[:5])
            + ".</p>"
        )
    else:
        status = "ok"
        if z2_ceiling is not None and zone_drift_runs:
            drift_note = (
                f"<p>1 easy run above Z2 ceiling ({z2_ceiling:.0f}bpm): "
                + zone_drift_runs[0]
                + ".</p>"
            )
        elif z2_ceiling is None:
            drift_note = "<p>No Z2 HR ceiling found in athlete facts — zone drift check skipped.</p>"
        else:
            drift_note = "<p>No zone drift detected on easy runs.</p>"

    # Table: last 10 runs
    recent_runs = runs[:10]
    rows = []
    for run in recent_runs:
        d = run.get("date", "")
        try:
            parsed = datetime.strptime(d, "%Y-%m-%d").date()
            date_label = parsed.strftime("%-d %b")
        except (ValueError, TypeError):
            date_label = d
        name = run.get("name", "")
        dist = run.get("distance_miles")
        dist_str = f"{dist:.1f}" if dist is not None else "-"
        pace = run.get("pace_min_per_mile")
        if pace is not None:
            mins = int(pace)
            secs = round((pace - mins) * 60)
            pace_str = f"{mins}:{secs:02d}/mi"
        else:
            pace_str = "-"
        hr = run.get("average_hr") or run.get("average_heartrate")
        hr_str = f"{int(hr)}" if hr else "-"
        rows.append([date_label, name, dist_str, pace_str, hr_str])

    table = _table(["Date", "Name", "Miles", "Pace", "HR"], rows)
    html = drift_note + table
    return status, html


# ── Recovery ──────────────────────────────────────────────────────────────────


def assess_recovery(wellness: list[dict]) -> tuple[str, str]:
    """Assess recovery from wellness data (HRV + RHR).

    wellness sorted most-recent-first. Returns (status, html).
    """
    if not wellness:
        return "info", "<p>No wellness data available.</p>"

    # Recent 3-day avg vs 7-day baseline
    recent_3 = wellness[:3]
    baseline_7 = wellness[:7]

    def _avg(records: list[dict], key: str) -> float | None:
        vals = [r[key] for r in records if r.get(key) is not None]
        return sum(vals) / len(vals) if vals else None

    recent_hrv = _avg(recent_3, "hrv")
    baseline_hrv = _avg(baseline_7, "hrv")
    recent_rhr = _avg(recent_3, "resting_hr")
    baseline_rhr = _avg(baseline_7, "resting_hr")

    hrv_status = "info"
    rhr_status = "info"

    hrv_note = ""
    rhr_note = ""

    if recent_hrv is not None and baseline_hrv is not None and baseline_hrv > 0:
        ratio = recent_hrv / baseline_hrv
        if ratio < 0.85:
            hrv_status = "concern"
            hrv_note = f"HRV {recent_hrv:.0f}ms (recent 3-day) vs {baseline_hrv:.0f}ms (7-day avg) — suppressed ({ratio:.0%})"
        elif ratio < 0.93:
            hrv_status = "caution"
            hrv_note = f"HRV {recent_hrv:.0f}ms vs {baseline_hrv:.0f}ms — slightly low ({ratio:.0%})"
        else:
            hrv_status = "ok"
            hrv_note = f"HRV {recent_hrv:.0f}ms (stable, {ratio:.0%} of baseline)"
    elif recent_hrv is not None:
        hrv_note = f"HRV {recent_hrv:.0f}ms (insufficient baseline)"

    if recent_rhr is not None and baseline_rhr is not None:
        delta = recent_rhr - baseline_rhr
        if delta > 5:
            rhr_status = "concern"
            rhr_note = f"RHR {recent_rhr:.0f}bpm vs {baseline_rhr:.0f}bpm avg (+{delta:.0f}bpm elevated)"
        elif delta > 3:
            rhr_status = "caution"
            rhr_note = f"RHR {recent_rhr:.0f}bpm vs {baseline_rhr:.0f}bpm avg (+{delta:.0f}bpm)"
        else:
            rhr_status = "ok"
            rhr_note = f"RHR {recent_rhr:.0f}bpm (normal)"
    elif recent_rhr is not None:
        rhr_note = f"RHR {recent_rhr:.0f}bpm (insufficient baseline)"

    # Worst of HRV / RHR
    rank = {"concern": 3, "caution": 2, "ok": 1, "info": 0}
    status = max([hrv_status, rhr_status], key=lambda s: rank.get(s, 0))

    summary_parts = []
    if hrv_note:
        summary_parts.append(hrv_note)
    if rhr_note:
        summary_parts.append(rhr_note)
    summary_html = (
        "<p>" + " | ".join(summary_parts) + "</p>" if summary_parts else ""
    )

    # Table: last 7 days wellness
    display_wellness = wellness[:7]
    rows = []
    for w in display_wellness:
        d = w.get("date", "")
        try:
            parsed = datetime.strptime(d, "%Y-%m-%d").date()
            date_label = parsed.strftime("%-d %b")
        except (ValueError, TypeError):
            date_label = d
        rhr_val = w.get("resting_hr")
        hrv_val = w.get("hrv")
        bb_low = w.get("body_battery_low")
        bb_high = w.get("body_battery_high")
        stress = w.get("stress_avg")
        sleep = w.get("sleep_score")

        bb_str = f"{bb_low}–{bb_high}" if bb_low is not None and bb_high is not None else "-"
        rows.append([
            date_label,
            f"{int(rhr_val)}" if rhr_val else "-",
            f"{int(hrv_val)}" if hrv_val else "-",
            bb_str,
            f"{int(stress)}" if stress else "-",
            f"{int(sleep)}" if sleep else "-",
        ])

    table = _table(["Date", "RHR", "HRV", "Body Battery", "Stress", "Sleep"], rows)
    html = summary_html + table
    return status, html


# ── Injury Status ─────────────────────────────────────────────────────────────


def assess_injury(diary_entries: list[dict], facts: list[dict]) -> tuple[str, str]:
    """Assess injury status from diary entries and athlete facts.

    Returns (status, html).
    """
    injury_facts = [f for f in facts if f.get("category") in ("injury", "training_response")]

    # Filter diary entries with niggles or notes
    entries_with_data = [
        e for e in diary_entries
        if (e.get("niggles") or "").strip() or (e.get("notes") or "").strip()
    ]
    entries_with_niggles = [
        e for e in diary_entries if (e.get("niggles") or "").strip()
    ]

    has_data = bool(diary_entries or injury_facts)

    if not has_data:
        return "info", "<p>No diary or injury data available.</p>"

    if entries_with_niggles:
        status = "caution"
    elif not injury_facts:
        status = "ok"
    else:
        # Has injury facts but no recent niggles — still flag as caution
        status = "caution"

    # Build content
    parts: list[str] = []

    # Injury facts list
    if injury_facts:
        items = "".join(f"<li>{f['fact']}</li>" for f in injury_facts)
        parts.append(f"<ul>{items}</ul>")
    else:
        parts.append("<p>No injury facts recorded.</p>")

    # Diary table (only rows with niggles or notes)
    if entries_with_data:
        rows = []
        for e in entries_with_data:
            d = e.get("date", "")
            try:
                parsed = datetime.strptime(d, "%Y-%m-%d").date()
                date_label = parsed.strftime("%-d %b")
            except (ValueError, TypeError):
                date_label = d
            stress = str(e.get("stress_1_5") or "-")
            niggles = e.get("niggles") or ""
            notes = e.get("notes") or ""
            rows.append([date_label, stress, niggles, notes])

        table = _table(["Date", "Stress", "Niggles", "Notes"], rows)
        parts.append(table)
    elif diary_entries:
        parts.append("<p>No niggles or notes in diary this week.</p>")

    html = "\n".join(parts)
    return status, html


# ── Overall Readiness ─────────────────────────────────────────────────────────


def assess_readiness(
    training_status: str,
    recovery_status: str,
    injury_status: str,
    training_html: str,
    recovery_html: str,
    injury_html: str,
) -> tuple[str, str, str]:
    """Assess overall readiness as the worst of training/recovery/injury.

    Returns (status, verdict_text, content_html).
    """
    rank = {"concern": 3, "caution": 2, "ok": 1, "info": 0}
    statuses = [training_status, recovery_status, injury_status]
    overall = max(statuses, key=lambda s: rank.get(s, 0))

    verdicts = {
        "ok": "Ready to train",
        "caution": "Train with caution",
        "concern": "Recovery priority",
        "info": "Insufficient data",
    }
    verdict_text = verdicts.get(overall, "Insufficient data")

    # Build bullet list of flagging areas
    flags = []
    for label, s in [
        ("Training load", training_status),
        ("Recovery", recovery_status),
        ("Injury / niggles", injury_status),
    ]:
        if s in ("caution", "concern"):
            flags.append(f"<li>{label}: {s.upper()}</li>")

    if flags:
        content_html = f"<ul>{''.join(flags)}</ul>"
    else:
        content_html = "<p>All systems green.</p>"

    return overall, verdict_text, content_html


# ── Status Snapshot Text ──────────────────────────────────────────────────────


def build_status_snapshot(
    training_status: str,
    training_html: str,
    recovery_status: str,
    recovery_html: str,
    injury_status: str,
    injury_html: str,
    readiness_status: str,
    readiness_verdict: str,
) -> str:
    """Build a concise plain-text status summary for plan/chat agents.

    Returns a multi-line string suitable for injecting into LLM system prompts.
    """
    lines = [
        f"Training Load: {training_status.upper()}",
        f"Recovery: {recovery_status.upper()}",
        f"Injury Status: {injury_status.upper()}",
        f"Overall Readiness: {readiness_status.upper()} — {readiness_verdict}",
    ]
    return "\n".join(lines)
