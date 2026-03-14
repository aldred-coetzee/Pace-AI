"""Flask chat UI for Pace-AI — thin route layer."""

from __future__ import annotations

import asyncio
import json
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor

from flask import Flask, Response, render_template_string, request, session

from ui.config import (
    CLAUDE_CMD,
    DB_PATH,
    NUTRITION_GENERAL_SECTIONS,
    NUTRITION_PLAN_SECTIONS,
    NUTRITION_RACE_SECTIONS,
    PLAN_REPORT_SECTIONS,
    PROJECT_ROOT,
    STATUS_INJURY_SECTIONS,
    STATUS_READINESS_SECTIONS,
    STATUS_RECOVERY_SECTIONS,
    STATUS_TRAINING_SECTIONS,
    HistoryDB,
    _sync_all,
    append_coaching_log,
    get_coaching_context,
    log,
    update_coaching_context,
)
from ui.context import (
    _build_chat_context,
    _build_injury_context,
    _build_nutrition_context,
    _build_plan_context,
    _build_readiness_context,
    _build_recovery_context,
    _build_training_context,
    _gather_status_data,
    _render_body_comp_html,
    _render_schedule_html,
)
from ui.plans import (
    _default_date_range,
    _enrich_plan_with_exercises,
    _extract_weekly_plan,
    _format_plan_table,
    _strip_plan_json,
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

    cmd = list(CLAUDE_CMD)
    cmd.extend(["--system-prompt", context])

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

    log.info("--- chat claude -p call ---")
    log.info("system prompt length: %d chars", len(context))
    log.info("conversation messages: %d (recent: %d)", len(history), len(recent))
    log.info("user message: %r", user_message[:100])

    try:
        result = subprocess.run(
            cmd,
            input=prompt_text,
            capture_output=True,
            text=True,
            timeout=300,
            cwd=str(PROJECT_ROOT),
        )
        log.info("return code: %d", result.returncode)
        log.info("stdout: %d bytes", len(result.stdout))
        log.info(
            "stderr: %d bytes | %s",
            len(result.stderr),
            result.stderr[:200] if result.stderr else "(empty)",
        )
        reply = result.stdout.strip() or result.stderr.strip() or "(no response)"
    except subprocess.TimeoutExpired:
        log.exception("claude -p timed out")
        reply = "(timeout — Claude took too long)"
    except Exception as e:
        log.exception("claude -p failed")
        reply = f"(error: {e})"

    log.info("reply length: %d chars", len(reply))

    # Check if the response contains a revised weekly plan
    extracted_plan = _extract_weekly_plan(reply)
    if extracted_plan:
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


def _call_claude_status(
    context: str, prompt_text: str = "Assess my current training status."
) -> str:
    """Run a single claude -p subprocess call for a status sub-group.

    Returns the raw stdout string. Handles timeouts and errors gracefully.
    """
    cmd = list(CLAUDE_CMD)
    cmd.extend(["--system-prompt", context])
    try:
        result = subprocess.run(
            cmd,
            input=prompt_text,
            capture_output=True,
            text=True,
            timeout=120,
            cwd=str(PROJECT_ROOT),
        )
        return result.stdout.strip() or result.stderr.strip() or "(no response)"
    except subprocess.TimeoutExpired:
        log.exception("status claude -p timed out")
        return "(timeout — Claude took too long)"
    except Exception as e:
        log.exception("status claude -p failed")
        return f"(error: {e})"


def _merge_status_html(
    group_results: dict[str, str],
    readiness_raw: str,
    schedule_html: str,
    body_comp_html: str,
) -> str:
    """Merge parallel Claude results + direct-rendered sections into final HTML.

    Renders each group's JSON output into section cards, then assembles them
    in the correct order with injected schedule and body composition cards.
    """
    from datetime import date

    parts = ['<div class="status-report">']
    parts.append(
        f'<div class="status-date">{date.today().strftime("%A %-d %B %Y")}</div>'
    )

    # Group A: training_load + recent_runs
    training_raw = group_results.get("training", "")
    _render_group_sections(parts, training_raw, STATUS_TRAINING_SECTIONS)

    # Group B: recovery
    recovery_raw = group_results.get("recovery", "")
    _render_group_sections(parts, recovery_raw, STATUS_RECOVERY_SECTIONS)

    # Direct-rendered: body composition
    parts.append(body_comp_html)

    # Group C: injury_status
    injury_raw = group_results.get("injury", "")
    _render_group_sections(parts, injury_raw, STATUS_INJURY_SECTIONS)

    # Direct-rendered: upcoming schedule
    parts.append(schedule_html)

    # Group D: overall_readiness (verdict)
    _render_group_sections(
        parts,
        readiness_raw,
        STATUS_READINESS_SECTIONS,
        verdict_section="overall_readiness",
    )

    parts.append("</div>")
    return "\n".join(parts)


def _render_group_sections(
    parts: list[str],
    raw: str,
    sections: list[tuple],
    *,
    verdict_section: str | None = None,
) -> None:
    """Parse JSON from a Claude group response and append section cards to parts list."""
    m = re.search(r"```json\s*\n(.*?)\n\s*```", raw, re.DOTALL)
    if not m:
        # Fallback: show raw text if JSON parsing fails
        if raw and not raw.startswith("("):
            parts.append(
                '<div class="status-section status-info">'
                '<div class="status-header"><span class="status-title">Status</span></div>'
                f'<div class="status-body"><div class="md-content">{raw}</div></div>'
                "</div>"
            )
        return

    try:
        data = json.loads(m.group(1))
    except json.JSONDecodeError:
        return

    for key, display_title, has_status, _hint in sections:
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

    # 3. Build focused contexts
    training_ctx = _build_training_context(data)
    recovery_ctx = _build_recovery_context(data)
    injury_ctx = _build_injury_context(data)

    log.info("--- status parallel claude -p calls ---")
    log.info("training context: %d chars", len(training_ctx))
    log.info("recovery context: %d chars", len(recovery_ctx))
    log.info("injury context: %d chars", len(injury_ctx))

    # 4. Run Groups A, B, C in parallel
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = {
            "training": pool.submit(
                _call_claude_status,
                training_ctx,
                "Assess training load and recent runs.",
            ),
            "recovery": pool.submit(
                _call_claude_status, recovery_ctx, "Assess recovery status."
            ),
            "injury": pool.submit(
                _call_claude_status, injury_ctx, "Assess injury status."
            ),
        }
        group_results = {k: f.result() for k, f in futures.items()}

    log.info("training result: %d chars", len(group_results["training"]))
    log.info("recovery result: %d chars", len(group_results["recovery"]))
    log.info("injury result: %d chars", len(group_results["injury"]))

    # 5. Build readiness context from results and call Claude
    readiness_ctx = _build_readiness_context(data, group_results)
    log.info("readiness context: %d chars", len(readiness_ctx))
    readiness_raw = _call_claude_status(
        readiness_ctx, "Give an overall readiness assessment."
    )
    log.info("readiness result: %d chars", len(readiness_raw))

    # 6. Merge everything into final HTML
    rendered = _merge_status_html(
        group_results, readiness_raw, schedule_html, body_comp_html
    )

    # Build combined raw snapshot for PLAN and CHAT agents
    snapshot_parts = []
    for key in ("training", "recovery", "injury"):
        if group_results.get(key):
            snapshot_parts.append(group_results[key])
    if readiness_raw:
        snapshot_parts.append(readiness_raw)
    status_snapshot = "\n\n".join(snapshot_parts)

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

    # Auto-generate status if not cached (using parallel approach)
    if not store.get("status_snapshot"):
        log.info("No status cached — auto-generating before plan (parallel)")
        db = HistoryDB(DB_PATH)
        status_data = _gather_status_data(db)

        schedule_html = _render_schedule_html(status_data.get("schedule") or [])
        body_comp_html = _render_body_comp_html(db)

        training_ctx = _build_training_context(status_data)
        recovery_ctx = _build_recovery_context(status_data)
        injury_ctx = _build_injury_context(status_data)

        with ThreadPoolExecutor(max_workers=3) as pool:
            futures = {
                "training": pool.submit(
                    _call_claude_status,
                    training_ctx,
                    "Assess training load and recent runs.",
                ),
                "recovery": pool.submit(
                    _call_claude_status, recovery_ctx, "Assess recovery status."
                ),
                "injury": pool.submit(
                    _call_claude_status, injury_ctx, "Assess injury status."
                ),
            }
            auto_results = {k: f.result() for k, f in futures.items()}

        readiness_ctx = _build_readiness_context(status_data, auto_results)
        readiness_raw = _call_claude_status(
            readiness_ctx, "Give an overall readiness assessment."
        )

        rendered_status = _merge_status_html(
            auto_results, readiness_raw, schedule_html, body_comp_html
        )

        snapshot_parts = []
        for key in ("training", "recovery", "injury"):
            if auto_results.get(key):
                snapshot_parts.append(auto_results[key])
        if readiness_raw:
            snapshot_parts.append(readiness_raw)
        store["status_snapshot"] = "\n\n".join(snapshot_parts)
        store["status_generated_at"] = datetime.now().isoformat()
        store["messages"].append(
            {"role": "assistant", "content": rendered_status, "agent": "status"}
        )

    # Build plan context and call
    plan_context = _build_plan_context(store["status_snapshot"], date_range)

    log.info("--- plan claude -p call ---")
    log.info("plan context length: %d chars", len(plan_context))

    cmd = list(CLAUDE_CMD)
    cmd.extend(["--system-prompt", plan_context])

    try:
        result = subprocess.run(
            cmd,
            input=f"Create a training plan for {date_range}.",
            capture_output=True,
            text=True,
            timeout=300,
            cwd=str(PROJECT_ROOT),
        )
        reply = result.stdout.strip() or result.stderr.strip() or "(no response)"
    except subprocess.TimeoutExpired:
        log.exception("plan claude -p timed out")
        reply = "(timeout — Claude took too long)"
    except Exception as e:
        log.exception("plan claude -p failed")
        reply = f"(error: {e})"

    log.info("plan reply length: %d chars", len(reply))

    # Extract plan JSON (may contain report sections + sessions)
    extracted_plan = _extract_weekly_plan(reply)
    if extracted_plan:
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
        "- updated_context: the full rewritten coaching context (max 2000 words), "
        "intelligently merging the existing context with anything new or changed from "
        "this session. Preserve what is still relevant, drop what is stale.\n\n"
        "Return JSON only. No prose, no markdown fences."
    )

    log.info("--- end-session claude -p call ---")
    log.info("conversation messages: %d", len(messages))
    log.info("prompt length: %d chars", len(prompt))

    try:
        result = subprocess.run(
            CLAUDE_CMD,
            input=prompt,
            capture_output=True,
            text=True,
            timeout=120,
            cwd=str(PROJECT_ROOT),
        )
        raw = result.stdout.strip() or result.stderr.strip() or ""
        log.info("end-session return code: %d", result.returncode)
        log.info("end-session raw length: %d chars", len(raw))
    except subprocess.TimeoutExpired:
        log.exception("end-session claude -p timed out")
        return render_template_string(
            END_SESSION_HTML,
            error="Claude timed out during session logging.",
            raw_response=None,
            summary=None,
            prescriptions=None,
            follow_ups=None,
            updated_context=None,
        )
    except Exception as e:
        log.exception("end-session claude -p failed")
        return render_template_string(
            END_SESSION_HTML,
            error=f"Claude call failed: {e}",
            raw_response=None,
            summary=None,
            prescriptions=None,
            follow_ups=None,
            updated_context=None,
        )

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

    # Save full conversation to history
    try:
        import sqlite3 as _sq

        confirmed_plan = store.get("confirmed_plan")
        conn = _sq.connect(_SESSION_DB)
        conn.execute(
            "INSERT INTO conversations (messages, summary, plan) VALUES (?, ?, ?)",
            (
                json.dumps(messages, default=str),
                summary,
                json.dumps(confirmed_plan, default=str) if confirmed_plan else None,
            ),
        )
        conn.commit()
        conn.close()
        log.info("Conversation saved to history")
    except Exception:
        log.exception("Failed to save conversation to history")

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

    log.info("--- nutrition claude -p call (mode=%s) ---", mode)
    log.info("nutrition context length: %d chars", len(context))

    cmd = list(CLAUDE_CMD)
    cmd.extend(["--system-prompt", context])

    try:
        result = subprocess.run(
            cmd,
            input=prompt_text,
            capture_output=True,
            text=True,
            timeout=300,
            cwd=str(PROJECT_ROOT),
        )
        reply = result.stdout.strip() or result.stderr.strip() or "(no response)"
    except subprocess.TimeoutExpired:
        log.exception("nutrition claude -p timed out")
        reply = "(timeout — Claude took too long)"
    except Exception as e:
        log.exception("nutrition claude -p failed")
        reply = f"(error: {e})"

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
        "SELECT created_at, messages, summary, plan FROM conversations ORDER BY created_at DESC LIMIT 50"
    ).fetchall()
    conn.close()

    sessions = []
    for row in rows:
        try:
            messages = json.loads(row["messages"])
        except (json.JSONDecodeError, TypeError):
            messages = []
        sessions.append(
            {
                "date": (row["created_at"] or "")[:16].replace("T", " "),
                "summary": row["summary"],
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
