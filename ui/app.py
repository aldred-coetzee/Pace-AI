"""Flask chat UI for Pace-AI — thin route layer."""

from __future__ import annotations

import asyncio
import json
import re
import subprocess

from flask import Flask, Response, render_template_string, request, session

from ui.config import (
    CLAUDE_CMD,
    DB_PATH,
    PROJECT_ROOT,
    HistoryDB,
    _sync_all,
    append_coaching_log,
    get_coaching_context,
    log,
    update_coaching_context,
)
from ui.context import (
    _build_chat_context,
    _build_nutrition_context,
    _build_plan_context,
    _build_status_context,
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


@app.route("/status", methods=["POST"])
def status():
    from datetime import datetime

    store = _get_store()
    context = _build_status_context()

    log.info("--- status claude -p call ---")
    log.info("status context length: %d chars", len(context))

    cmd = list(CLAUDE_CMD)
    cmd.extend(["--system-prompt", context])

    try:
        result = subprocess.run(
            cmd,
            input="Assess my current training status.",
            capture_output=True,
            text=True,
            timeout=120,
            cwd=str(PROJECT_ROOT),
        )
        reply = result.stdout.strip() or result.stderr.strip() or "(no response)"
    except subprocess.TimeoutExpired:
        log.exception("status claude -p timed out")
        reply = "(timeout — Claude took too long)"
    except Exception as e:
        log.exception("status claude -p failed")
        reply = f"(error: {e})"

    store["status_snapshot"] = reply
    store["status_generated_at"] = datetime.now().isoformat()
    store["messages"].append({"role": "assistant", "content": reply, "agent": "status"})

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

    # Auto-generate status if not cached
    if not store.get("status_snapshot"):
        log.info("No status cached — auto-generating before plan")
        status_context = _build_status_context()
        cmd = list(CLAUDE_CMD)
        cmd.extend(["--system-prompt", status_context])
        try:
            result = subprocess.run(
                cmd,
                input="Assess my current training status.",
                capture_output=True,
                text=True,
                timeout=120,
                cwd=str(PROJECT_ROOT),
            )
            status_reply = (
                result.stdout.strip() or result.stderr.strip() or "(no status)"
            )
        except Exception as e:
            log.exception("Auto-status for plan failed")
            status_reply = f"(status unavailable: {e})"

        store["status_snapshot"] = status_reply
        store["status_generated_at"] = datetime.now().isoformat()
        store["messages"].append(
            {"role": "assistant", "content": status_reply, "agent": "status"}
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

    # Extract plan JSON
    extracted_plan = _extract_weekly_plan(reply)
    if extracted_plan:
        log.info(
            "Detected weekly plan: %s, %d sessions",
            extracted_plan.get("week_starting"),
            len(extracted_plan.get("sessions", [])),
        )
        store["pending_plan"] = extracted_plan
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

    store["messages"].append(
        {"role": "assistant", "content": reply, "agent": "nutrition"}
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
