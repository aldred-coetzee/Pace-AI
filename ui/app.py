"""Flask chat UI for Pace-AI — thin route layer."""

from __future__ import annotations

import asyncio
import json
import re

from flask import Flask, Response, render_template_string, request, session

from ui.config import (
    DB_PATH,
    NUTRITION_GENERAL_SECTIONS,
    NUTRITION_PLAN_SECTIONS,
    NUTRITION_RACE_SECTIONS,
    PLAN_REPORT_SECTIONS,
    HistoryDB,
    _sync_all,
    append_coaching_log,
    get_coaching_context,
    log,
    update_coaching_context,
)
from ui.llm import call_llm
from ui.context import (
    _build_chat_context,
    _build_nutrition_context,
    _build_plan_context,
    _gather_status_data,
    _render_body_comp_html,
    _render_schedule_html,
)
from ui.status import (
    assess_injury,
    assess_readiness,
    assess_recent_runs,
    assess_recovery,
    assess_training_load,
    build_status_snapshot,
    render_status_section,
)
from ui.plans import (
    _default_date_range,
    _enrich_plan_with_exercises,
    _extract_weekly_plan,
    _format_plan_table,
    _strip_plan_json,
    _validate_plan_dates,
)
from ui.scheduling import schedule_plan_to_garmin
from ui.sessions import (
    _SESSION_DB,
    _delete_session,
    _get_store,
    _persist_store,
    _sessions,
)
from ui.templates import (
    CONFIRM_PLAN_HTML,
    END_SESSION_HTML,
    HISTORY_HTML,
    HTML,
)

app = Flask(__name__)
app.secret_key = "pace-ai-dev-key"


@app.after_request
def _auto_persist_session(response):
    """Persist session to SQLite after every request."""
    _persist_store()
    return response


@app.route("/")
def index():
    store = _get_store()
    messages = store.get("messages", [])
    has_pending_plan = "pending_plan" in store
    has_confirmed_plan = "confirmed_plan" in store

    # Check for active race goals
    has_race_goals = False
    try:
        db = HistoryDB(DB_PATH)
        from pace_ai.tools.goals import get_goals

        goals = get_goals(db)
        has_race_goals = bool(goals)
    except Exception:
        pass

    # Estimate session token usage (~4 chars per token)
    total_chars = sum(len(m.get("content", "")) for m in messages)
    status_snapshot = store.get("status_snapshot")
    if status_snapshot:
        total_chars += len(status_snapshot)
    session_tokens = round(total_chars / 4000, 1)  # in thousands

    # Status cache age
    status_cached = False
    status_age = ""
    if store.get("status_generated_at"):
        from datetime import datetime

        status_cached = True
        try:
            gen_at = datetime.fromisoformat(store["status_generated_at"])
            age_mins = int((datetime.now() - gen_at).total_seconds() / 60)
            if age_mins < 1:
                status_age = "just now"
            elif age_mins < 60:
                status_age = f"{age_mins}m ago"
            else:
                status_age = f"{age_mins // 60}h ago"
        except (ValueError, TypeError):
            status_age = "cached"

    # Last sync time
    db = HistoryDB(DB_PATH)
    sync_status = None
    try:
        syncs = db.get_sync_status()
        if syncs:
            latest = max(s.get("synced_at", "") for s in syncs if s.get("synced_at"))
            if latest:
                sync_status = f"Last sync: {latest[:16].replace('T', ' ')}"
        if not sync_status:
            sync_status = "Not synced yet — click Sync All to load your data"
    except Exception:
        pass

    return render_template_string(
        HTML,
        messages=messages,
        has_pending_plan=has_pending_plan,
        has_confirmed_plan=has_confirmed_plan,
        has_race_goals=has_race_goals,
        message_count=len(messages),
        session_tokens=session_tokens,
        sync_status=sync_status,
        status_cached=status_cached,
        status_age=status_age,
        default_date_from=_default_date_range()[0],
        default_date_to=_default_date_range()[1],
    )


@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.form.get("message", "").strip()
    if not user_message:
        return Response(status=302, headers={"Location": "/"})

    store = _get_store()
    store["messages"].append({"role": "user", "content": user_message})

    # Build CHAT agent context (lightweight, conversational)
    status_snapshot = store.get("status_snapshot")
    pending_plan = store.get("pending_plan")
    context = _build_chat_context(status_snapshot, pending_plan)

    # Build conversation from last 10 messages for context
    history = store.get("messages", [])
    recent = history[-10:]
    if len(recent) > 1:
        convo_lines = []
        for msg in recent:
            role = "Athlete" if msg["role"] == "user" else "Coach"
            convo_lines.append(f"{role}: {msg['content']}")
        prompt_text = (
            "Continue this coaching conversation. Reply only as Coach.\n\n"
            + "\n\n".join(convo_lines)
            + "\n\nCoach:"
        )
    else:
        prompt_text = user_message

    log.info("--- chat LLM call ---")
    log.info("system prompt length: %d chars", len(context))
    log.info("conversation messages: %d (recent: %d)", len(history), len(recent))
    log.info("user message: %r", user_message[:100])

    reply = call_llm(context, prompt_text, timeout=300)

    log.info("reply length: %d chars", len(reply))

    # Check if the response contains a revised weekly plan
    extracted_plan = _extract_weekly_plan(reply)
    if extracted_plan:
        extracted_plan = _validate_plan_dates(extracted_plan)
        log.info(
            "Detected revised plan: %s, %d sessions",
            extracted_plan.get("week_starting"),
            len(extracted_plan.get("sessions", [])),
        )
        store["pending_plan"] = extracted_plan
        display_reply = re.sub(
            r"```(?:json)?\s*\n\{.+\}\s*\n```", "", reply, flags=re.DOTALL
        )
        display_reply = _strip_plan_json(display_reply).strip()
        if not display_reply:
            display_reply = "Here's the revised plan."
        display_reply += _format_plan_table(extracted_plan)
        store["messages"].append(
            {"role": "assistant", "content": display_reply, "agent": "chat"}
        )
    else:
        store["messages"].append(
            {"role": "assistant", "content": reply, "agent": "chat"}
        )

    return Response(status=302, headers={"Location": "/"})


def _render_structured_html(
    raw: str,
    sections: list[tuple],
    *,
    verdict_section: str | None = None,
    title: str | None = None,
    inject_before_verdict: str | None = None,
) -> str:
    """Parse structured JSON from Claude and render to styled section cards.

    Args:
        raw: Raw Claude output containing ```json fences.
        sections: List of (key, title, has_status, content_hint) tuples.
        verdict_section: Section key that has a verdict headline.
        title: Optional date/title line shown above sections.
        inject_before_verdict: Pre-rendered HTML to inject before the verdict section.

    Falls back to raw markdown if JSON parsing fails.
    """
    m = re.search(r"```json\s*\n(.*?)\n\s*```", raw, re.DOTALL)
    if not m:
        return raw

    try:
        data = json.loads(m.group(1))
    except json.JSONDecodeError:
        return raw

    parts = ['<div class="status-report">']
    if title:
        parts.append(f'<div class="status-date">{title}</div>')

    for key, display_title, has_status, _hint in sections:
        # Inject pre-rendered sections before the verdict
        if key == verdict_section and inject_before_verdict:
            parts.append(inject_before_verdict)

        section = data.get(key)
        if not section:
            continue

        content = section.get("content", "")
        status = section.get("status", "info") if has_status else "info"
        css_class = (
            f"status-{status}"
            if status in ("ok", "caution", "concern")
            else "status-info"
        )

        if key == verdict_section:
            verdict = section.get("verdict", "")
            parts.append(f'<div class="status-verdict {css_class}">')
            parts.append(f'<div class="verdict-label">{verdict}</div>')
            parts.append(
                f'<div class="status-body"><div class="md-content">{content}</div></div>'
            )
            parts.append("</div>")
        else:
            parts.append(f'<div class="status-section {css_class}">')
            parts.append('<div class="status-header">')
            if has_status:
                parts.append('<span class="status-dot"></span>')
            parts.append(f'<span class="status-title">{display_title}</span>')
            parts.append("</div>")
            parts.append(
                f'<div class="status-body"><div class="md-content">{content}</div></div>'
            )
            parts.append("</div>")

    parts.append("</div>")
    return "\n".join(parts)


def _render_plan_table_html(sessions: list[dict], week_starting: str = "") -> str:
    """Render sessions into a styled table card — no LLM needed.

    Uses the same status-section structure as schedule/body-composition cards.
    """
    from datetime import datetime

    day_names = {0: "Mon", 1: "Tue", 2: "Wed", 3: "Thu", 4: "Fri", 5: "Sat", 6: "Sun"}

    rows = []
    for s in sessions:
        date_str = s.get("date", "")
        try:
            d = datetime.strptime(date_str, "%Y-%m-%d").date()
            day = day_names[d.weekday()]
            label = f"{day} {d.strftime('%-d %b')}"
        except (ValueError, KeyError):
            label = date_str

        is_rest = s.get("workout_type") == "rest"
        row_class = ' class="rest-row"' if is_rest else ""
        name = s.get("name", "")
        wtype = s.get("workout_type", "")
        duration = s.get("duration_minutes", "")
        duration_str = f"{duration}min" if duration else ""

        if is_rest:
            rows.append(
                f"<tr{row_class}>"
                f'<td>{label}</td><td colspan="3" style="color:var(--text-tertiary)">{name or "Rest"}</td>'
                f"</tr>"
            )
        else:
            rows.append(
                f"<tr{row_class}>"
                f"<td>{label}</td><td>{name}</td><td>{wtype}</td><td>{duration_str}</td>"
                f"</tr>"
            )

    title_text = f"Week of {week_starting}" if week_starting else "Training Plan"
    table_html = (
        "<table><thead><tr><th>Date</th><th>Session</th><th>Type</th><th>Duration</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table>"
    )

    return (
        '<div class="status-section status-info">'
        '<div class="status-header">'
        f'<span class="status-title">{title_text}</span>'
        "</div>"
        f'<div class="status-body">{table_html}</div>'
        "</div>"
    )


def _assemble_status_html(
    training_html: str,
    recent_runs_html: str,
    recovery_html: str,
    injury_html: str,
    readiness_html: str,
    body_comp_html: str,
    schedule_html: str,
) -> str:
    """Assemble pre-rendered section HTML cards into the final status report."""
    from datetime import date

    parts = ['<div class="status-report">']
    parts.append(
        f'<div class="status-date">{date.today().strftime("%A %-d %B %Y")}</div>'
    )
    parts.append(training_html)
    parts.append(recent_runs_html)
    parts.append(recovery_html)
    parts.append(body_comp_html)
    parts.append(injury_html)
    parts.append(schedule_html)
    parts.append(readiness_html)
    parts.append("</div>")
    return "\n".join(parts)


@app.route("/status", methods=["POST"])
def status():
    from datetime import datetime

    store = _get_store()

    # 1. Gather all data upfront
    db = HistoryDB(DB_PATH)
    data = _gather_status_data(db)

    # 2. Direct-render data-only sections
    schedule_html = _render_schedule_html(data.get("schedule") or [])
    body_comp_html = _render_body_comp_html(db)

    # 3. Deterministic rule-based assessments (no LLM)
    log.info("--- status deterministic assessment ---")
    training_status, training_html = assess_training_load(data.get("weekly_distances") or [])
    runs_status, runs_html = assess_recent_runs(
        data.get("activities") or [], data.get("facts") or []
    )
    recovery_status, recovery_html = assess_recovery(data.get("wellness") or [])
    injury_status, injury_html = assess_injury(
        data.get("diary_entries") or [], data.get("facts") or []
    )
    readiness_status, readiness_verdict, readiness_content = assess_readiness(
        training_status, recovery_status, injury_status,
        training_html, recovery_html, injury_html,
    )

    log.info(
        "status: training=%s runs=%s recovery=%s injury=%s readiness=%s",
        training_status, runs_status, recovery_status, injury_status, readiness_status,
    )

    # 4. Render section cards
    training_card = render_status_section("Training Load", training_status, training_html)
    runs_card = render_status_section("Recent Runs", runs_status, runs_html)
    recovery_card = render_status_section("Recovery", recovery_status, recovery_html)
    injury_card = render_status_section("Injury Status", injury_status, injury_html)
    readiness_card = render_status_section(
        "Overall Readiness", readiness_status, readiness_content,
        verdict_text=readiness_verdict,
    )

    # 5. Assemble final HTML
    rendered = _assemble_status_html(
        training_card, runs_card, recovery_card, injury_card,
        readiness_card, body_comp_html, schedule_html,
    )

    # 6. Build text snapshot for PLAN and CHAT agents
    status_snapshot = build_status_snapshot(
        training_status, training_html,
        recovery_status, recovery_html,
        injury_status, injury_html,
        readiness_status, readiness_verdict,
    )

    store["status_snapshot"] = status_snapshot
    store["status_generated_at"] = datetime.now().isoformat()
    store["messages"].append(
        {"role": "assistant", "content": rendered, "agent": "status"}
    )

    return Response(status=302, headers={"Location": "/"})


@app.route("/plan", methods=["POST"])
def plan():
    from datetime import datetime

    store = _get_store()

    date_from = request.form.get("date_from", "").strip()
    date_to = request.form.get("date_to", "").strip()
    if not date_from or not date_to:
        date_from, date_to = _default_date_range()
    date_range = f"{date_from} to {date_to}"

    # Auto-generate status if not cached (deterministic, instant)
    if not store.get("status_snapshot"):
        log.info("No status cached — auto-generating before plan (deterministic)")
        db = HistoryDB(DB_PATH)
        status_data = _gather_status_data(db)

        schedule_html = _render_schedule_html(status_data.get("schedule") or [])
        body_comp_html = _render_body_comp_html(db)

        auto_training_status, auto_training_html = assess_training_load(
            status_data.get("weekly_distances") or []
        )
        auto_runs_status, auto_runs_html = assess_recent_runs(
            status_data.get("activities") or [], status_data.get("facts") or []
        )
        auto_recovery_status, auto_recovery_html = assess_recovery(
            status_data.get("wellness") or []
        )
        auto_injury_status, auto_injury_html = assess_injury(
            status_data.get("diary_entries") or [], status_data.get("facts") or []
        )
        auto_readiness_status, auto_readiness_verdict, auto_readiness_content = assess_readiness(
            auto_training_status, auto_recovery_status, auto_injury_status,
            auto_training_html, auto_recovery_html, auto_injury_html,
        )

        auto_training_card = render_status_section("Training Load", auto_training_status, auto_training_html)
        auto_runs_card = render_status_section("Recent Runs", auto_runs_status, auto_runs_html)
        auto_recovery_card = render_status_section("Recovery", auto_recovery_status, auto_recovery_html)
        auto_injury_card = render_status_section("Injury Status", auto_injury_status, auto_injury_html)
        auto_readiness_card = render_status_section(
            "Overall Readiness", auto_readiness_status, auto_readiness_content,
            verdict_text=auto_readiness_verdict,
        )

        rendered_status = _assemble_status_html(
            auto_training_card, auto_runs_card, auto_recovery_card, auto_injury_card,
            auto_readiness_card, body_comp_html, schedule_html,
        )

        store["status_snapshot"] = build_status_snapshot(
            auto_training_status, auto_training_html,
            auto_recovery_status, auto_recovery_html,
            auto_injury_status, auto_injury_html,
            auto_readiness_status, auto_readiness_verdict,
        )
        store["status_generated_at"] = datetime.now().isoformat()
        store["messages"].append(
            {"role": "assistant", "content": rendered_status, "agent": "status"}
        )

    # Build plan context and call
    plan_context = _build_plan_context(store["status_snapshot"], date_range)

    log.info("--- plan LLM call ---")
    log.info("plan context length: %d chars", len(plan_context))

    reply = call_llm(plan_context, f"Create a training plan for {date_range}.", timeout=300)

    log.info("plan reply length: %d chars", len(reply))

    # Extract plan JSON (may contain report sections + sessions)
    extracted_plan = _extract_weekly_plan(reply)
    if extracted_plan:
        # Validate and fix any day-of-week mismatches in session names
        extracted_plan = _validate_plan_dates(extracted_plan)
        sessions = extracted_plan.get("sessions", [])
        week_starting = extracted_plan.get("week_starting", "")
        log.info(
            "Detected weekly plan: %s, %d sessions",
            week_starting,
            len(sessions),
        )

        # Store sessions dict for scheduling (pending_plan needs week_starting + sessions)
        store["pending_plan"] = {
            "week_starting": week_starting,
            "sessions": sessions,
        }

        # Render report sections via structured HTML + sessions table
        plan_table_html = _render_plan_table_html(sessions, week_starting)
        rendered = _render_structured_html(
            reply,
            PLAN_REPORT_SECTIONS,
            title=f"Training Plan — {date_range}",
        )

        # If structured rendering succeeded (contains status-report div), append table
        if '<div class="status-report">' in rendered:
            # Insert table before closing </div> of status-report
            rendered = rendered.rsplit("</div>", 1)[0] + plan_table_html + "\n</div>"
        else:
            # Fallback: structured parse failed, use raw text + table
            display_reply = re.sub(
                r"```(?:json)?\s*\n\{.+\}\s*\n```", "", reply, flags=re.DOTALL
            )
            display_reply = _strip_plan_json(display_reply).strip()
            if not display_reply:
                display_reply = "Here's your weekly plan."
            display_reply += _format_plan_table(extracted_plan)
            store["messages"].append(
                {"role": "assistant", "content": display_reply, "agent": "plan"}
            )
            return Response(status=302, headers={"Location": "/"})

        store["messages"].append(
            {"role": "assistant", "content": rendered, "agent": "plan"}
        )
    else:
        store["messages"].append(
            {"role": "assistant", "content": reply, "agent": "plan"}
        )

    return Response(status=302, headers={"Location": "/"})


@app.route("/end-session", methods=["POST"])
def end_session():
    store = _get_store()
    messages = store.get("messages", [])

    if not messages:
        return render_template_string(
            END_SESSION_HTML,
            error="No messages in this session.",
            raw_response=None,
            summary=None,
            prescriptions=None,
            follow_ups=None,
            updated_context=None,
        )

    # Load existing coaching context
    db = HistoryDB(DB_PATH)
    existing_ctx = get_coaching_context(db)
    existing_content = (
        existing_ctx["content"] if existing_ctx else "(no existing context)"
    )

    # Format conversation history
    convo_lines = [f"{m['role']}: {m['content']}" for m in messages]
    conversation_text = "\n\n".join(convo_lines)

    # Include confirmed plan if one was scheduled this session
    confirmed_plan = store.get("confirmed_plan")
    plan_section = ""
    if confirmed_plan:
        plan_section = (
            f"\nCONFIRMED SCHEDULED PLAN (use this as ground truth for what was "
            f"actually scheduled — not the conversation):\n"
            f"{json.dumps(confirmed_plan, indent=2)}\n\n"
        )

    prompt = (
        "Here is a coaching conversation and the current coaching context.\n\n"
        f"EXISTING COACHING CONTEXT:\n{existing_content}\n\n"
        f"{plan_section}"
        f"CONVERSATION:\n{conversation_text}\n\n"
        "Produce a JSON object with exactly these fields:\n"
        "- session_summary: 2-3 sentence summary of what was discussed and decided\n"
        "- key_prescriptions: list of specific training instructions given this session\n"
        "- follow_ups: list of things to check or revisit next session\n"
        "- updated_context: the full rewritten coaching context (max 2000 words)\n\n"
        "IMPORTANT RULES FOR updated_context:\n"
        "The coaching context is the coach's DURABLE understanding of the athlete. "
        "It is read by future coaching agents who also have access to current activity, "
        "diary, and wellness data.\n\n"
        "INCLUDE in updated_context (stable, changes slowly):\n"
        "- Athlete profile, training history, long-term goals\n"
        "- Current training phase and parameters (paces, HR zones, weekly structure)\n"
        "- Injury history, rehab protocol details, cut rules\n"
        "- Device info and known limitations\n"
        "- Nutrition principles and preferences\n"
        "- Sleep and recovery guidance\n"
        "- Coaching principles in play\n\n"
        "DO NOT include in updated_context (volatile, goes stale quickly):\n"
        "- Specific scheduled sessions or dates (e.g. 'Tue 17: Easy Run 2.5 mi')\n"
        "- Compliance status claims (e.g. 'NOT YET STARTED as of Mar 14')\n"
        "- Specific session results (e.g. 'Mar 14: DONE: 3.1 mi, 11:35/mi')\n"
        "- Sync status or data availability claims (e.g. 'sync stopped since Mar 11')\n"
        "These belong in session_summary and key_prescriptions instead, where they "
        "are timestamped and clearly historical.\n\n"
        "Return JSON only. No prose, no markdown fences."
    )

    log.info("--- end-session LLM call ---")
    log.info("conversation messages: %d", len(messages))
    log.info("prompt length: %d chars", len(prompt))

    raw = call_llm("You are a running coach assistant.", prompt, timeout=120)
    log.info("end-session raw length: %d chars", len(raw))

    # Strip markdown fences if present
    cleaned = re.sub(r"^```(?:json)?\s*\n?", "", raw, flags=re.MULTILINE)
    cleaned = re.sub(r"\n?```\s*$", "", cleaned, flags=re.MULTILINE)
    cleaned = cleaned.strip()

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        log.error("Failed to parse end-session JSON: %s", e)
        return render_template_string(
            END_SESSION_HTML,
            error=f"Failed to parse JSON from Claude: {e}",
            raw_response=raw,
            summary=None,
            prescriptions=None,
            follow_ups=None,
            updated_context=None,
        )

    summary = data.get("session_summary", "")
    prescriptions = data.get("key_prescriptions", [])
    follow_ups = data.get("follow_ups", [])
    updated_context = data.get("updated_context", "")

    # Persist to database
    try:
        follow_up_str = "; ".join(follow_ups) if follow_ups else None
        append_coaching_log(
            db,
            {
                "summary": summary,
                "prescriptions": prescriptions,
                "follow_up": follow_up_str,
            },
        )
        if updated_context:
            update_coaching_context(db, updated_context)
        log.info("Session logged and context updated successfully")
    except Exception as e:
        log.exception("Failed to persist session log")
        return render_template_string(
            END_SESSION_HTML,
            error=f"Claude responded OK but database write failed: {e}",
            raw_response=raw,
            summary=None,
            prescriptions=None,
            follow_ups=None,
            updated_context=None,
        )

    # Attach the summary to the conversation row (the row itself was written
    # incrementally by _persist_store as messages came in). Fall back to INSERT
    # in the edge case where end-session fires before any persist (shouldn't
    # happen — there must be messages to summarise — but cheap insurance).
    try:
        import sqlite3 as _sq

        sid = session.get("sid")
        confirmed_plan = store.get("confirmed_plan")
        plan_json = json.dumps(confirmed_plan, default=str) if confirmed_plan else None
        conn = _sq.connect(_SESSION_DB)
        cur = conn.execute(
            "UPDATE conversations SET summary = ?, plan = COALESCE(?, plan), updated_at = CURRENT_TIMESTAMP WHERE sid = ?",
            (summary, plan_json, sid),
        )
        if cur.rowcount == 0:
            conn.execute(
                "INSERT INTO conversations (sid, messages, summary, plan, updated_at) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)",
                (sid, json.dumps(messages, default=str), summary, plan_json),
            )
        conn.commit()
        conn.close()
        log.info("Conversation summary saved to history")
    except Exception:
        log.exception("Failed to save conversation summary to history")

    # Clear the session after successful logging
    sid = session.get("sid")
    if sid:
        if sid in _sessions:
            del _sessions[sid]
        _delete_session(sid)
    session.clear()

    return render_template_string(
        END_SESSION_HTML,
        error=None,
        raw_response=None,
        summary=summary,
        prescriptions=prescriptions,
        follow_ups=follow_ups,
        updated_context=updated_context,
    )


@app.route("/sync", methods=["POST"])
def sync():
    db = HistoryDB(DB_PATH)
    try:
        result = asyncio.run(_sync_all(db))
    except Exception as e:
        log.exception("sync_all failed")
        store = _get_store()
        store["messages"].append({"role": "assistant", "content": f"Sync failed: {e}"})
        return Response(status=302, headers={"Location": "/"})

    # Summarise results for the chat
    parts = []
    for source, info in result.get("results", {}).items():
        count = info.get("activities_synced") or info.get("records_synced", 0)
        parts.append(f"{source}: {count}")
    errors = result.get("errors", {})
    summary = "Sync complete — " + ", ".join(parts)
    if errors:
        summary += f" | errors: {', '.join(errors)}"

    store = _get_store()
    store["messages"].append({"role": "assistant", "content": summary})

    # Invalidate cached status so next calls pick up fresh data
    store.pop("status_snapshot", None)
    store.pop("status_generated_at", None)

    return Response(status=302, headers={"Location": "/"})


@app.route("/review-plan", methods=["GET", "POST"])
def review_plan():
    store = _get_store()
    pending = store.get("pending_plan")
    if not pending:
        return Response(status=302, headers={"Location": "/"})
    return render_template_string(CONFIRM_PLAN_HTML, plan=pending)


@app.route("/confirm-plan", methods=["POST"])
def confirm_plan():
    store = _get_store()
    pending = store.pop("pending_plan", None)
    if not pending:
        return Response(status=302, headers={"Location": "/"})

    # Ensure strength/mobility sessions have exercises arrays
    needs_exercises = [
        s
        for s in pending.get("sessions", [])
        if s.get("workout_type") in ("strength", "mobility", "yoga")
        and not s.get("exercises")
    ]
    if needs_exercises:
        log.info(
            "Generating exercises for %d sessions via focused prompt",
            len(needs_exercises),
        )
        enriched = _enrich_plan_with_exercises(pending)
        if enriched:
            pending = enriched

    results, ok_count, fail_count, skip_count = schedule_plan_to_garmin(pending)

    # Store confirmed plan for end-session summarisation
    store["confirmed_plan"] = pending

    # Build a readable summary for the chat
    lines = []
    for r in results:
        icon = {"ok": "+", "fail": "x", "skip": "-"}.get(r["css"], "?")
        lines.append(f"[{icon}] {r['date']} {r['name']}: {r['status']}")
    summary = (
        f"**Plan scheduled** ({ok_count} ok, {fail_count} failed, {skip_count} skipped)\n"
        + "\n".join(lines)
    )
    store["messages"].append({"role": "assistant", "content": summary})

    return Response(status=302, headers={"Location": "/"})


@app.route("/cancel-plan", methods=["POST"])
def cancel_plan():
    store = _get_store()
    store.pop("pending_plan", None)
    store["messages"].append(
        {"role": "assistant", "content": "Plan cancelled — not scheduled."}
    )
    return Response(status=302, headers={"Location": "/"})


@app.route("/nutrition", methods=["POST"])
def nutrition():
    store = _get_store()
    mode = request.form.get("mode", "general").strip()

    if mode not in ("general", "plan", "race"):
        mode = "general"

    # Gather mode-specific data
    confirmed_plan = store.get("confirmed_plan") if mode == "plan" else None
    race_goals = None
    if mode == "race":
        try:
            db = HistoryDB(DB_PATH)
            from pace_ai.tools.goals import get_goals

            race_goals = get_goals(db)
        except Exception:
            log.exception("Failed to load race goals for nutrition")

    status_snapshot = store.get("status_snapshot")
    context = _build_nutrition_context(
        mode=mode,
        status_snapshot=status_snapshot,
        confirmed_plan=confirmed_plan,
        race_goals=race_goals,
    )

    mode_labels = {
        "general": "general nutrition advice",
        "plan": "plan-paired nutrition",
        "race": "race fueling strategy",
    }
    prompt_text = f"Give me {mode_labels.get(mode, 'nutrition advice')}."

    log.info("--- nutrition LLM call (mode=%s) ---", mode)
    log.info("nutrition context length: %d chars", len(context))

    reply = call_llm(context, prompt_text, timeout=300)

    log.info("nutrition reply length: %d chars", len(reply))

    mode_sections = {
        "general": NUTRITION_GENERAL_SECTIONS,
        "plan": NUTRITION_PLAN_SECTIONS,
        "race": NUTRITION_RACE_SECTIONS,
    }
    mode_titles = {
        "general": "Nutrition — General Principles",
        "plan": "Nutrition — Training Plan",
        "race": "Nutrition — Race Strategy",
    }
    rendered = _render_structured_html(
        reply,
        mode_sections.get(mode, NUTRITION_GENERAL_SECTIONS),
        title=mode_titles.get(mode, "Nutrition"),
    )
    store["messages"].append(
        {"role": "assistant", "content": rendered, "agent": "nutrition"}
    )

    return Response(status=302, headers={"Location": "/"})


@app.route("/history")
def history():
    import sqlite3 as _sq

    conn = _sq.connect(_SESSION_DB)
    conn.row_factory = _sq.Row
    rows = conn.execute(
        """SELECT created_at, updated_at, messages, summary, plan
           FROM conversations
           ORDER BY COALESCE(updated_at, created_at) DESC
           LIMIT 50"""
    ).fetchall()
    conn.close()

    sessions = []
    for row in rows:
        try:
            messages = json.loads(row["messages"])
        except (json.JSONDecodeError, TypeError):
            messages = []
        when = row["updated_at"] or row["created_at"] or ""
        sessions.append(
            {
                "date": when[:16].replace("T", " "),
                "summary": row["summary"] or "(in progress)",
                "messages": messages,
                "message_count": len(messages),
            }
        )

    return render_template_string(HISTORY_HTML, sessions=sessions)


@app.route("/clear", methods=["POST"])
def clear():
    sid = session.get("sid")
    if sid:
        if sid in _sessions:
            del _sessions[sid]
        _delete_session(sid)
    session.clear()
    return Response(status=302, headers={"Location": "/"})


if __name__ == "__main__":
    import os
    import webbrowser

    # Only open browser in the reloader parent, not the child process
    if os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        webbrowser.open("http://localhost:5050")
    app.run(debug=True, port=5050)
