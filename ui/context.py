"""Context builders for all agents — STATUS, PLAN, CHAT, NUTRITION."""

from __future__ import annotations

import json

from ui.config import (
    CHAT_SYSTEM_PROMPT,
    DB_PATH,
    NUTRITION_CLAIM_CATEGORIES,
    NUTRITION_MODE_GENERAL,
    NUTRITION_MODE_PLAN,
    NUTRITION_MODE_RACE,
    NUTRITION_SYSTEM_PROMPT,
    PLAN_JSON_SCHEMA,
    PLAN_SYSTEM_PROMPT,
    STATUS_SYSTEM_PROMPT,
    HistoryDB,
    get_athlete_facts,
    get_athlete_profile,
    get_coaching_context,
    get_recent_activities,
    get_recent_coaching_log,
    get_weekly_distances,
    log,
)


def _build_profile_summary(db: HistoryDB) -> str:
    """Build a one-line athlete profile summary for lightweight context."""
    try:
        profile = get_athlete_profile(db)
        if not profile:
            return "Athlete profile not available."
        parts = []
        if profile.get("name"):
            parts.append(profile["name"])
        weekly_km = profile.get("current_weekly_km")
        if weekly_km:
            parts.append(f"{round(weekly_km / 1.60934, 1)} mi/week")
        pace_km = profile.get("typical_easy_pace_min_per_km")
        if pace_km:
            pace_mi = pace_km * 1.60934
            mins = int(pace_mi)
            secs = int((pace_mi - mins) * 60)
            parts.append(f"easy pace {mins}:{secs:02d}/mi")
        if profile.get("injury_history"):
            parts.append(f"injuries: {profile['injury_history'][:80]}")
        return " | ".join(parts) if parts else "Athlete profile loaded."
    except Exception:
        log.exception("Failed to build profile summary")
        return "Athlete profile not available."


def _convert_profile_miles(profile: dict) -> dict:
    """Add mile-based fields to a profile dict (mutates in place, returns it)."""
    pace_km = profile.get("typical_easy_pace_min_per_km")
    if pace_km:
        pace_mi = pace_km * 1.60934
        mins = int(pace_mi)
        secs = int((pace_mi - mins) * 60)
        profile["typical_easy_pace_per_mile"] = f"{mins}:{secs:02d}"
    weekly_km = profile.get("current_weekly_km")
    if weekly_km:
        profile["current_weekly_miles"] = round(weekly_km / 1.60934, 1)
    typical_km = profile.get("typical_weekly_km")
    if typical_km:
        profile["typical_weekly_miles"] = round(typical_km / 1.60934, 1)
    long_km = profile.get("typical_long_run_km")
    if long_km:
        profile["typical_long_run_miles"] = round(long_km / 1.60934, 1)
    max_km = profile.get("max_weekly_km_ever")
    if max_km:
        profile["max_weekly_miles_ever"] = round(max_km / 1.60934, 1)
    return profile


def _build_body_composition(db: HistoryDB) -> str | None:
    """Build body composition section from Withings data."""
    try:
        measurements = db.get_body_measurements(days=28)
        if not measurements:
            return None
        latest = measurements[0]
        lines = ["Latest:"]
        if latest.get("weight_kg"):
            lines.append(f"- Weight: {latest['weight_kg']:.1f} kg")
        if latest.get("body_fat_pct"):
            lines.append(f"- Body fat: {latest['body_fat_pct']:.1f}%")
        if latest.get("systolic_bp") and latest.get("diastolic_bp"):
            lines.append(
                f"- BP: {int(latest['systolic_bp'])}/{int(latest['diastolic_bp'])}"
            )
        lines.append(f"- Date: {latest.get('date', '?')}")
        if len(measurements) >= 4:
            mid = len(measurements) // 2
            recent_w = [
                m["weight_kg"] for m in measurements[:mid] if m.get("weight_kg")
            ]
            older_w = [m["weight_kg"] for m in measurements[mid:] if m.get("weight_kg")]
            if recent_w and older_w:
                diff = sum(recent_w) / len(recent_w) - sum(older_w) / len(older_w)
                direction = "up" if diff > 0.3 else "down" if diff < -0.3 else "stable"
                lines.append(f"- 4-week weight trend: {direction} ({diff:+.1f} kg)")
        return "## Body Composition\n" + "\n".join(lines)
    except Exception:
        log.exception("Failed to load body measurements")
        return None


def _build_diary_section(db: HistoryDB, days: int = 7) -> str | None:
    """Build diary entries section."""
    try:
        diary = db.get_diary_entries(days=days)
        if not diary:
            return None
        lines = []
        for entry in diary:
            parts = [entry.get("date", "?")]
            if entry.get("stress_1_5"):
                parts.append(f"stress:{entry['stress_1_5']}/5")
            if entry.get("niggles"):
                parts.append(f"niggles: {entry['niggles']}")
            if entry.get("notes"):
                parts.append(entry["notes"])
            lines.append("- " + " | ".join(parts))
        return "## Diary (last 7 days)\n" + "\n".join(lines)
    except Exception:
        log.exception("Failed to load diary entries")
        return None


def _build_facts_section(db: HistoryDB) -> tuple[list[dict], str | None]:
    """Build athlete facts section. Returns (facts_list, formatted_section)."""
    try:
        facts = get_athlete_facts(db)
        if facts:
            lines = [f"- [{f['category']}] {f['fact']}" for f in facts]
            return facts, "## Athlete Facts\n" + "\n".join(lines)
        return [], None
    except Exception:
        log.exception("Failed to load athlete facts")
        return [], None


def _build_coaching_sections(db: HistoryDB) -> tuple[str | None, str | None]:
    """Build coaching context and recent log sections. Returns (context_section, log_section)."""
    ctx_section = None
    log_section = None
    try:
        ctx = get_coaching_context(db)
        if ctx:
            ctx_section = f"## Coaching Context\n{ctx['content']}"
    except Exception:
        log.exception("Failed to load coaching context")
    try:
        logs = get_recent_coaching_log(db, limit=3)
        if logs:
            log_lines = []
            for entry in logs:
                line = f"- [{entry.get('created_at', '?')}] {entry.get('summary', '')}"
                if entry.get("follow_up"):
                    line += f" | Follow-up: {entry['follow_up']}"
                log_lines.append(line)
            log_section = "## Recent Coaching Sessions\n" + "\n".join(log_lines)
    except Exception:
        log.exception("Failed to load coaching log")
    return ctx_section, log_section


def _get_relevant_claims(
    db: HistoryDB, profile: dict | None, facts: list[dict]
) -> str | None:
    """Derive relevant research categories from athlete profile/facts and query claims.

    Returns a formatted section string, or None if no claims found.
    """
    from pace_ai.resources.claim_store import query_claims

    categories: set[str] = set()

    # Always include these for any runner — core training pillars
    categories.add("foam_rolling_mobility")
    categories.add("recovery_modalities")
    categories.add("easy_recovery_running")
    categories.add("strength_training_runners")
    categories.add("warmup_cooldown")
    categories.add("concurrent_training")
    categories.add("overtraining_recovery")
    categories.add("sleep_recovery")

    # Derive from injury history
    injury_text = ""
    if profile:
        injury_text = (profile.get("injury_history") or "").lower()
    for f in facts:
        if f.get("category") == "injury":
            injury_text += " " + f.get("fact", "").lower()

    if "achilles" in injury_text or "tendon" in injury_text:
        categories.add("tendon_health")
        categories.add("injury_lower_leg")
    if "knee" in injury_text:
        categories.add("injury_knee")
    if "stress fracture" in injury_text:
        categories.add("injury_stress_fracture")
    if any(w in injury_text for w in ["return", "comeback", "break", "layoff"]):
        categories.add("return_to_running")
        categories.add("detraining")

    # Derive from training phase / notes
    notes = (profile.get("notes") or "").lower() if profile else ""
    if "return" in notes or "comeback" in notes:
        categories.add("return_to_running")
        categories.add("detraining")

    # Derive from goals
    for f in facts:
        if f.get("category") == "goal":
            goal_text = f.get("fact", "").lower()
            if "marathon" in goal_text and "half" not in goal_text:
                categories.add("marathon_training")
            if "half" in goal_text:
                categories.add("half_marathon_training")
            if "5k" in goal_text:
                categories.add("5k_track_training")

    # Age-based
    population = "recreational runners"
    if profile and profile.get("date_of_birth"):
        from datetime import date, datetime

        try:
            dob = datetime.strptime(profile["date_of_birth"][:10], "%Y-%m-%d").date()
            age = (date.today() - dob).days // 365
            if age >= 40:
                categories.add("masters_running")
                population = "masters runners"
        except (ValueError, TypeError):
            pass

    # Training load — always relevant
    categories.add("training_load_acwr")
    categories.add("injury_prevention_general")

    # Query top claims per category (limit to keep prompt reasonable)
    all_claims: list[dict] = []
    for cat in sorted(categories):
        claims = query_claims(cat, population, limit=5)
        all_claims.extend(claims)

    if not all_claims:
        return None

    # Deduplicate and sort by score
    seen: set[str] = set()
    unique: list[dict] = []
    for c in sorted(all_claims, key=lambda x: x.get("score", 0), reverse=True):
        text = c.get("text", "")
        if text not in seen:
            seen.add(text)
            unique.append(c)

    # Limit total to keep prompt reasonable (~60 claims max)
    unique = unique[:60]

    lines = [
        f"Research evidence ({len(unique)} claims from {len(categories)} categories). "
        "Base your coaching on these claims — cite them when relevant."
    ]
    current_cat = ""
    for c in sorted(unique, key=lambda x: x.get("category", "")):
        cat = c.get("category", "")
        if cat != current_cat:
            current_cat = cat
            lines.append(f"\n**{cat}**:")
        lines.append(f"- {c['text']}")

    return "## Research Evidence\n" + "\n".join(lines)


def _get_nutrition_claims(db: HistoryDB) -> str | None:
    """Query nutrition-specific research claims.

    Returns a formatted section string, or None if no claims found.
    """
    from pace_ai.resources.claim_store import query_claims

    population = "recreational runners"
    try:
        profile = get_athlete_profile(db)
        if profile and profile.get("date_of_birth"):
            from datetime import date, datetime

            try:
                dob = datetime.strptime(
                    profile["date_of_birth"][:10], "%Y-%m-%d"
                ).date()
                age = (date.today() - dob).days // 365
                if age >= 40:
                    population = "masters runners"
            except (ValueError, TypeError):
                pass
    except Exception:
        pass

    all_claims: list[dict] = []
    for cat in NUTRITION_CLAIM_CATEGORIES:
        claims = query_claims(cat, population, limit=8)
        all_claims.extend(claims)

    if not all_claims:
        return None

    # Deduplicate and sort by score
    seen: set[str] = set()
    unique: list[dict] = []
    for c in sorted(all_claims, key=lambda x: x.get("score", 0), reverse=True):
        text = c.get("text", "")
        if text not in seen:
            seen.add(text)
            unique.append(c)

    unique = unique[:40]

    lines = [
        f"Nutrition research evidence ({len(unique)} claims). "
        "Base your advice on these claims — cite them when relevant."
    ]
    current_cat = ""
    for c in sorted(unique, key=lambda x: x.get("category", "")):
        cat = c.get("category", "")
        if cat != current_cat:
            current_cat = cat
            lines.append(f"\n**{cat}**:")
        lines.append(f"- {c['text']}")

    return "## Nutrition Research Evidence\n" + "\n".join(lines)


# ── STATUS agent ──


def _build_status_context() -> str:
    """Build context for the STATUS agent — full data, no scheduling/exercises schema."""
    db = HistoryDB(DB_PATH)
    sections: list[str] = [STATUS_SYSTEM_PROMPT]

    try:
        profile = get_athlete_profile(db)
        if profile:
            _convert_profile_miles(profile)
            sections.append(
                f"## Athlete Profile\n{json.dumps(profile, indent=2, default=str)}"
            )
    except Exception:
        log.exception("Failed to load athlete profile")

    try:
        activities = get_recent_activities(db, days=28)
        if activities:
            lines = []
            for a in activities:
                parts = [a.get("start_date", "?")[:10]]
                if a.get("name"):
                    parts.append(a["name"])
                if a.get("distance_miles"):
                    parts.append(f"{a['distance_miles']} mi")
                if a.get("pace_min_per_mile"):
                    parts.append(f"{a['pace_min_per_mile']}/mi")
                if a.get("average_heartrate"):
                    parts.append(f"HR {int(a['average_heartrate'])}")
                if a.get("elapsed_time_s"):
                    mins = a["elapsed_time_s"] // 60
                    parts.append(f"{mins}min")
                lines.append("- " + " | ".join(parts))
            sections.append(
                f"## Recent Activities (28 days, {len(activities)} total)\n"
                + "\n".join(lines)
            )
    except Exception:
        log.exception("Failed to load recent activities")

    try:
        weekly = get_weekly_distances(db, weeks=12)
        if weekly:
            lines = []
            for w in weekly:
                mi = w.get("distance_miles") or 0
                lines.append(
                    f"- {w.get('week_start', '?')}: {mi} mi ({w.get('activity_count', 0)} runs)"
                )
            sections.append("## Weekly Distances (12 weeks)\n" + "\n".join(lines))
    except Exception:
        log.exception("Failed to load weekly distances")

    # Scheduled workouts from Garmin calendar (today + next 9 days)
    try:
        from datetime import date, timedelta

        from garmin_mcp.client import GarminClient
        from garmin_mcp.config import Settings as GarminSettings

        today = date.today()
        cal_end = today + timedelta(days=9)
        garmin_client = GarminClient(GarminSettings.from_env())
        # Fetch calendar months covering the range
        all_items: list[dict] = []
        seen_months: set[tuple[int, int]] = set()
        current = today
        while current <= cal_end:
            key = (current.year, current.month - 1)
            if key not in seen_months:
                seen_months.add(key)
                data = garmin_client.get_calendar(current.year, current.month - 1)
                items = data.get("calendarItems", []) if isinstance(data, dict) else []
                all_items.extend(items)
            current += timedelta(days=1)

        today_str = today.isoformat()
        end_str = cal_end.isoformat()
        scheduled = [
            item
            for item in all_items
            if item.get("date") and today_str <= item["date"] <= end_str
        ]
        if scheduled:
            lines = []
            for item in sorted(scheduled, key=lambda x: x.get("date", "")):
                title = item.get("title", "?")
                d = item.get("date", "?")
                sport = item.get("sportTypeKey", "")
                lines.append(
                    f"- {d} | {title} ({sport})" if sport else f"- {d} | {title}"
                )
            sections.append("## Scheduled Workouts (next 10 days)\n" + "\n".join(lines))
    except Exception:
        log.exception("Failed to load Garmin calendar")

    try:
        wellness = db.get_wellness(days=14)
        if wellness:
            lines = []
            for w in wellness:
                parts = [w.get("date", "?")]
                if w.get("resting_hr"):
                    parts.append(f"RHR {w['resting_hr']}")
                if w.get("hrv"):
                    parts.append(f"HRV {w['hrv']}")
                if w.get("body_battery_high"):
                    parts.append(
                        f"BB {w.get('body_battery_low', '?')}-{w['body_battery_high']}"
                    )
                if w.get("stress_avg"):
                    parts.append(f"stress {w['stress_avg']}")
                if w.get("sleep_score"):
                    parts.append(f"sleep {w['sleep_score']}")
                lines.append("- " + " | ".join(parts))
            sections.append("## Wellness (14 days)\n" + "\n".join(lines))
    except Exception:
        log.exception("Failed to load wellness data")

    body_comp = _build_body_composition(db)
    if body_comp:
        sections.append(body_comp)

    diary = _build_diary_section(db, days=7)
    if diary:
        sections.append(diary)

    facts, facts_section = _build_facts_section(db)
    if facts_section:
        sections.append(facts_section)

    ctx_section, log_section = _build_coaching_sections(db)
    if ctx_section:
        sections.append(ctx_section)
    if log_section:
        sections.append(log_section)

    return "\n\n".join(sections)


# ── PLAN agent ──


def _build_plan_context(status_snapshot: str, date_range: str) -> str:
    """Build context for the PLAN agent — status + research + schema."""
    db = HistoryDB(DB_PATH)
    sections: list[str] = [PLAN_SYSTEM_PROMPT]

    sections.append(f"## Current Status\n{status_snapshot}")

    facts, facts_section = _build_facts_section(db)
    if facts_section:
        sections.append(facts_section)

    ctx_section, _ = _build_coaching_sections(db)
    if ctx_section:
        sections.append(ctx_section)

    try:
        profile = get_athlete_profile(db)
        claims_text = _get_relevant_claims(db, profile, facts)
        if claims_text:
            sections.append(claims_text)
    except Exception:
        log.exception("Failed to load research claims")

    sections.append(PLAN_JSON_SCHEMA)

    sections.append(f"## Date Range\nCreate a plan for: {date_range}")

    return "\n\n".join(sections)


# ── CHAT agent ──


def _build_chat_context(status_snapshot: str | None, pending_plan: dict | None) -> str:
    """Build context for the CHAT agent — lightweight, conversational."""
    db = HistoryDB(DB_PATH)

    plan_instruction = ""
    if pending_plan:
        plan_instruction = (
            "If the athlete requests plan changes, output the full revised "
            "plan JSON in the same format.\n"
        )

    system_prompt = CHAT_SYSTEM_PROMPT.format(plan_instruction=plan_instruction)
    sections: list[str] = [system_prompt]

    summary = _build_profile_summary(db)
    sections.append(f"## Athlete\n{summary}")

    facts, facts_section = _build_facts_section(db)
    if facts_section:
        sections.append(facts_section)

    ctx_section, _ = _build_coaching_sections(db)
    if ctx_section:
        sections.append(ctx_section)

    if status_snapshot:
        sections.append(f"## Latest Status Assessment\n{status_snapshot}")

    if pending_plan:
        sections.append(
            f"## Current Pending Plan\n{json.dumps(pending_plan, indent=2)}"
        )
        sections.append(PLAN_JSON_SCHEMA)

    return "\n\n".join(sections)


# ── NUTRITION agent ──


def _build_nutrition_context(
    mode: str,
    status_snapshot: str | None = None,
    confirmed_plan: dict | None = None,
    race_goals: list[dict] | None = None,
) -> str:
    """Build context for the NUTRITION agent.

    Args:
        mode: One of 'general', 'plan', 'race'.
        status_snapshot: Cached status for activity context.
        confirmed_plan: Confirmed plan JSON (for plan-paired mode).
        race_goals: Active race goals (for race fueling mode).
    """
    db = HistoryDB(DB_PATH)

    # Select mode instruction
    mode_instructions = {
        "general": NUTRITION_MODE_GENERAL,
        "plan": NUTRITION_MODE_PLAN,
        "race": NUTRITION_MODE_RACE,
    }
    mode_instruction = mode_instructions.get(mode, NUTRITION_MODE_GENERAL)

    system_prompt = NUTRITION_SYSTEM_PROMPT.format(mode_instruction=mode_instruction)
    sections: list[str] = [system_prompt]

    # Athlete profile with body composition (weight is critical for g/kg calculations)
    try:
        profile = get_athlete_profile(db)
        if profile:
            _convert_profile_miles(profile)
            sections.append(
                f"## Athlete Profile\n{json.dumps(profile, indent=2, default=str)}"
            )
    except Exception:
        log.exception("Failed to load athlete profile")

    # Body composition from Withings
    body_comp = _build_body_composition(db)
    if body_comp:
        sections.append(body_comp)

    # Nutrition-specific athlete facts
    try:
        all_facts = get_athlete_facts(db)
        nutrition_facts = [f for f in all_facts if f.get("category") == "nutrition"]
        other_facts = [f for f in all_facts if f.get("category") != "nutrition"]

        if nutrition_facts:
            lines = [f"- {f['fact']}" for f in nutrition_facts]
            sections.append(
                "## Dietary Preferences & Nutrition Facts\n" + "\n".join(lines)
            )
        else:
            sections.append(
                "## Dietary Preferences & Nutrition Facts\n"
                "No nutrition preferences recorded. Give generic advice and suggest "
                "the athlete add dietary preferences using athlete facts (category: nutrition)."
            )

        # Include other relevant facts too
        if other_facts:
            lines = [f"- [{f['category']}] {f['fact']}" for f in other_facts]
            sections.append("## Other Athlete Facts\n" + "\n".join(lines))
    except Exception:
        log.exception("Failed to load athlete facts")

    # Coaching context
    ctx_section, _ = _build_coaching_sections(db)
    if ctx_section:
        sections.append(ctx_section)

    # Recent activity summary and weekly distances
    try:
        activities = get_recent_activities(db, days=14)
        if activities:
            lines = []
            for a in activities:
                parts = [a.get("start_date", "?")[:10]]
                if a.get("name"):
                    parts.append(a["name"])
                if a.get("distance_miles"):
                    parts.append(f"{a['distance_miles']} mi")
                if a.get("elapsed_time_s"):
                    mins = a["elapsed_time_s"] // 60
                    parts.append(f"{mins}min")
                lines.append("- " + " | ".join(parts))
            sections.append("## Recent Activities (14 days)\n" + "\n".join(lines))
    except Exception:
        log.exception("Failed to load recent activities")

    try:
        weekly = get_weekly_distances(db, weeks=6)
        if weekly:
            lines = []
            for w in weekly:
                mi = w.get("distance_miles") or 0
                lines.append(
                    f"- {w.get('week_start', '?')}: {mi} mi ({w.get('activity_count', 0)} runs)"
                )
            sections.append("## Weekly Distances (6 weeks)\n" + "\n".join(lines))
    except Exception:
        log.exception("Failed to load weekly distances")

    # Nutrition research claims
    nutrition_claims = _get_nutrition_claims(db)
    if nutrition_claims:
        sections.append(nutrition_claims)

    # Status snapshot (if available)
    if status_snapshot:
        sections.append(f"## Current Training Status\n{status_snapshot}")

    # Mode-specific context
    if mode == "plan" and confirmed_plan:
        sections.append(
            f"## Confirmed Training Plan\n{json.dumps(confirmed_plan, indent=2)}"
        )

    if mode == "race" and race_goals:
        lines = []
        for g in race_goals:
            target_s = g.get("target_time_seconds", 0)
            hours = target_s // 3600
            mins = (target_s % 3600) // 60
            time_str = f"{hours}:{mins:02d}" if hours else f"{mins}min"
            lines.append(
                f"- {g.get('race_type', '?')} | Target: {time_str} "
                f"| Date: {g.get('race_date', 'TBD')} "
                f"| {g.get('notes', '')}"
            )
        sections.append("## Race Goals\n" + "\n".join(lines))

    return "\n\n".join(sections)
