"""Flask chat UI for Pace-AI with athlete context injection."""

from __future__ import annotations

import asyncio
import json
import logging
import re
import subprocess
import sys
import uuid
from pathlib import Path

from flask import Flask, Response, render_template_string, request, session

# Add pace-ai src to import path before importing pace_ai modules
PROJECT_ROOT = Path(__file__).resolve().parent.parent
_pace_src = str(PROJECT_ROOT / "pace-ai" / "src")
if _pace_src not in sys.path:
    sys.path.insert(0, _pace_src)

# ruff: noqa: E402
from pace_ai.database import HistoryDB
from pace_ai.tools.memory import (
    append_coaching_log,
    get_athlete_facts,
    get_coaching_context,
    get_recent_coaching_log,
    update_coaching_context,
)
from pace_ai.tools.profile import get_athlete_profile
from pace_ai.tools.sync import sync_all as _sync_all

# Add garmin-mcp src to import path for direct workout scheduling
_garmin_src = str(PROJECT_ROOT / "garmin-mcp" / "src")
if _garmin_src not in sys.path:
    sys.path.insert(0, _garmin_src)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")
log = logging.getLogger("pace-ui")

app = Flask(__name__)
app.secret_key = "pace-ai-dev-key"

DB_PATH = str(PROJECT_ROOT / "pace_ai.db")

# Server-side session store — cookie only holds a session ID
_sessions: dict[str, dict] = {}


def _get_store() -> dict:
    """Get or create server-side session store for the current request."""
    sid = session.get("sid")
    if sid is None or sid not in _sessions:
        sid = uuid.uuid4().hex
        session["sid"] = sid
        _sessions[sid] = {"messages": [], "athlete_context": None}
    return _sessions[sid]


CLAUDE_CMD = [
    "claude",
    "-p",
    "--dangerously-skip-permissions",
]

HTML = """\
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<link rel="icon" href="/static/favicon.ico" type="image/x-icon">
<title>Pace-AI Chat</title>
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
<style>
body { font-family: monospace; max-width: 800px; margin: 40px auto; padding: 0 20px; background: #1a1a1a; color: #e0e0e0; }
h1 { font-size: 1.2em; color: #aaa; }
.messages { margin-bottom: 20px; }
.msg { padding: 8px 12px; margin: 6px 0; border-radius: 4px; word-wrap: break-word; }
.user { background: #2a3a4a; border-left: 3px solid #4a9eff; white-space: pre-wrap; }
.assistant { background: #2a2a2a; border-left: 3px solid #6c6; }
.assistant table { border-collapse: collapse; margin: 8px 0; }
.assistant th, .assistant td { border: 1px solid #444; padding: 4px 8px; text-align: left; }
.assistant th { background: #333; }
.assistant blockquote { border-left: 3px solid #555; margin: 8px 0; padding: 4px 12px; color: #aaa; }
.assistant code { background: #333; padding: 1px 4px; border-radius: 3px; }
.assistant pre { background: #333; padding: 8px; border-radius: 4px; overflow-x: auto; }
.assistant h2, .assistant h3 { margin: 12px 0 6px; }
.assistant hr { border: none; border-top: 1px solid #444; margin: 12px 0; }
.ctx-banner { background: #1e2e1e; border: 1px solid #3a5a3a; padding: 6px 12px; border-radius: 4px; margin-bottom: 12px; font-size: 0.85em; color: #8a8; }
form { display: flex; gap: 8px; }
textarea { flex: 1; padding: 8px; font-family: monospace; font-size: 14px; background: #222; color: #e0e0e0; border: 1px solid #444; border-radius: 4px; resize: vertical; min-height: 60px; }
button { padding: 8px 20px; background: #4a9eff; color: #fff; border: none; border-radius: 4px; cursor: pointer; font-family: monospace; }
button:hover { background: #3a8eef; }
.end-btn { background: #b44; font-size: 0.85em; padding: 4px 12px; }
.end-btn:hover { background: #c55; }
.clear-btn { background: #555; font-size: 0.85em; padding: 4px 12px; }
.clear-btn:hover { background: #666; }
.spinner { display: none; color: #888; margin: 10px 0; }
.controls { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
</style>
</head>
<body>
<div class="controls">
<h1>Pace-AI Chat (dev)</h1>
<form method="POST" action="/end-session" style="display:inline;">
<button type="submit" class="end-btn">End Session</button>
</form>
<form method="POST" action="/sync" style="display:inline;">
<button type="submit" class="clear-btn">Sync All</button>
</form>
<form method="POST" action="/clear" style="display:inline;">
<button type="submit" class="clear-btn">Clear</button>
</form>
</div>
{% if context_status %}
<div class="ctx-banner">{{ context_status }}</div>
{% endif %}
<div class="messages">
{% for msg in messages %}
{% if msg.role == 'user' %}
<div class="msg user"><strong>you:</strong> {{ msg.content }}</div>
{% else %}
<div class="msg assistant"><strong>coach:</strong> <div class="md-content">{{ msg.content }}</div></div>
{% endif %}
{% endfor %}
</div>
{% if has_pending_plan %}
<div style="background:#1e2e3e; border:1px solid #4a9eff; padding:8px 12px; border-radius:4px; margin-bottom:12px; display:flex; gap:8px; align-items:center;">
<span style="color:#4a9eff;">Plan ready to schedule.</span>
<form method="POST" action="/review-plan" style="display:inline; margin:0;">
<button type="submit" style="background:#4a9eff; color:#fff; border:none; border-radius:4px; padding:6px 16px; cursor:pointer; font-family:monospace;">Schedule</button>
</form>
<form method="POST" action="/cancel-plan" style="display:inline; margin:0;">
<button type="submit" style="background:#555; color:#e0e0e0; border:none; border-radius:4px; padding:6px 16px; cursor:pointer; font-family:monospace;">Discard</button>
</form>
</div>
{% endif %}
<div class="spinner" id="spinner">Thinking...</div>
<form method="POST" action="/chat" id="chat-form">
<textarea name="message" placeholder="Type a message..." autofocus></textarea>
<button type="submit">Send</button>
</form>
<script>
document.querySelectorAll('.md-content').forEach(function(el) {
    el.innerHTML = marked.parse(el.textContent);
});
document.getElementById('chat-form').addEventListener('submit', function() {
    document.getElementById('spinner').style.display = 'block';
    document.querySelector('button[type=submit]').disabled = true;
});
</script>
</body>
</html>
"""


END_SESSION_HTML = """\
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<link rel="icon" href="/static/favicon.ico" type="image/x-icon">
<title>Pace-AI — Session Logged</title>
<style>
body { font-family: monospace; max-width: 800px; margin: 40px auto; padding: 0 20px; background: #1a1a1a; color: #e0e0e0; }
h1 { font-size: 1.2em; color: #aaa; }
h2 { font-size: 1em; color: #8a8; margin-top: 20px; }
.section { background: #2a2a2a; padding: 10px 14px; border-radius: 4px; margin: 8px 0; white-space: pre-wrap; word-wrap: break-word; }
.error { background: #3a1a1a; border: 1px solid #a44; padding: 10px 14px; border-radius: 4px; margin: 8px 0; white-space: pre-wrap; word-wrap: break-word; }
ul { margin: 4px 0; padding-left: 20px; }
a { color: #4a9eff; }
</style>
</head>
<body>
<h1>Session Logged</h1>
{% if error %}
<h2>Error</h2>
<div class="error">{{ error }}</div>
{% if raw_response %}
<h2>Raw Response</h2>
<div class="error">{{ raw_response }}</div>
{% endif %}
{% else %}
<h2>Summary</h2>
<div class="section">{{ summary }}</div>
<h2>Prescriptions</h2>
<div class="section"><ul>{% for p in prescriptions %}<li>{{ p }}</li>{% endfor %}</ul></div>
<h2>Follow-ups</h2>
<div class="section"><ul>{% for f in follow_ups %}<li>{{ f }}</li>{% endfor %}</ul></div>
<h2>Updated Coaching Context</h2>
<div class="section">{{ updated_context }}</div>
{% endif %}
<p><a href="/">Back to chat</a></p>
</body>
</html>
"""


CONFIRM_PLAN_HTML = """\
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<link rel="icon" href="/static/favicon.ico" type="image/x-icon">
<title>Pace-AI — Confirm Weekly Plan</title>
<style>
body { font-family: monospace; max-width: 800px; margin: 40px auto; padding: 0 20px; background: #1a1a1a; color: #e0e0e0; }
h1 { font-size: 1.2em; color: #aaa; }
h2 { font-size: 1em; color: #8a8; margin-top: 20px; }
table { border-collapse: collapse; width: 100%; margin: 12px 0; }
th, td { border: 1px solid #444; padding: 6px 10px; text-align: left; }
th { background: #333; }
tr.rest { color: #666; }
.btn-row { display: flex; gap: 8px; margin-top: 16px; }
button { padding: 8px 20px; border: none; border-radius: 4px; cursor: pointer; font-family: monospace; }
.confirm-btn { background: #4a9eff; color: #fff; }
.confirm-btn:hover { background: #3a8eef; }
.cancel-btn { background: #555; color: #e0e0e0; }
.cancel-btn:hover { background: #666; }
a { color: #4a9eff; }
</style>
</head>
<body>
<h1>Confirm Weekly Plan</h1>
<h2>Week starting {{ plan.week_starting }}</h2>
<table>
<tr><th>Date</th><th>Session</th><th>Type</th><th>Duration</th><th>Description</th></tr>
{% for s in plan.sessions %}
<tr class="{{ 'rest' if s.workout_type == 'rest' else '' }}">
<td>{{ s.date }}</td>
<td>{{ s.name }}</td>
<td>{{ s.workout_type }}</td>
<td>{{ s.duration_minutes }}min</td>
<td>{{ s.description or '' }}</td>
</tr>
{% endfor %}
</table>
<p>{{ plan.sessions | selectattr('workout_type', 'ne', 'rest') | list | length }} sessions will be created and scheduled in Garmin Connect. Rest days are skipped.</p>
<div class="btn-row">
<form method="POST" action="/confirm-plan">
<button type="submit" class="confirm-btn">Confirm &amp; Schedule</button>
</form>
<form method="POST" action="/cancel-plan">
<button type="submit" class="cancel-btn">Cancel</button>
</form>
<a href="/" style="padding: 8px 12px; color: #888;">Back to chat</a>
</div>
</body>
</html>
"""


def _extract_weekly_plan(text: str) -> dict | None:
    """Try to extract a weekly plan JSON block from Claude's response.

    Looks for a JSON object with 'week_starting' and 'sessions' keys,
    either bare or inside markdown code fences.
    """
    # Try to find JSON in code fences first
    fence_match = re.search(r"```(?:json)?\s*\n(\{.*?\})\s*\n```", text, re.DOTALL)
    if fence_match:
        candidate = fence_match.group(1)
        try:
            data = json.loads(candidate)
            if "week_starting" in data and "sessions" in data:
                return data
        except json.JSONDecodeError:
            pass

    # Try to find bare JSON with week_starting
    for match in re.finditer(
        r"\{[^{}]*\"week_starting\"[^{}]*\"sessions\"[^{}]*\[.*?\]\s*\}",
        text,
        re.DOTALL,
    ):
        try:
            data = json.loads(match.group(0))
            if "week_starting" in data and "sessions" in data:
                return data
        except json.JSONDecodeError:
            continue

    return None


def _description_to_steps(description: str, duration_minutes: int | None) -> list[dict]:
    """Parse a workout description into Garmin custom workout steps.

    Extracts exercise lines (e.g. '3x15 eccentric heel drops') and creates
    a lap-button step per exercise. Falls back to a single timed step
    if no exercises are found.

    Returns raw Garmin ExecutableStepDTO dicts.
    """
    _STEP_INTERVAL = {"stepTypeId": 3, "stepTypeKey": "interval"}
    _CONDITION_LAP = {"conditionTypeId": 1, "conditionTypeKey": "lap.button"}
    _CONDITION_TIME = {"conditionTypeId": 2, "conditionTypeKey": "time"}
    _TARGET_NONE = {"workoutTargetTypeId": 1, "workoutTargetTypeKey": "no.target"}

    # Match lines like "3x15 eccentric heel drops" or "3x12 goblet squats (dumbbell)"
    exercise_pattern = re.compile(r"(\d+)\s*x\s*(\d+)\s+(.+?)(?:\.|,|$)", re.IGNORECASE)
    exercises = exercise_pattern.findall(description)

    if not exercises:
        step_seconds = (duration_minutes or 30) * 60
        return [
            {
                "type": "ExecutableStepDTO",
                "stepId": None,
                "stepOrder": 1,
                "stepType": _STEP_INTERVAL,
                "endCondition": _CONDITION_TIME,
                "endConditionValue": float(step_seconds),
                "targetType": _TARGET_NONE,
                "description": description[:50] if description else "Workout",
            }
        ]

    steps: list[dict] = []
    for i, (sets, reps, name) in enumerate(exercises, 1):
        name = name.strip().rstrip(")")
        label = f"{sets}x{reps} {name}"
        if len(label) > 50:
            label = label[:47] + "..."
        steps.append(
            {
                "type": "ExecutableStepDTO",
                "stepId": None,
                "stepOrder": i,
                "stepType": _STEP_INTERVAL,
                "endCondition": _CONDITION_LAP,
                "targetType": _TARGET_NONE,
                "description": label,
            }
        )

    return steps


COACHING_INSTRUCTION = """\
## Units
All paces must be in **minutes per mile** (not per km). \
Data fields like typical_easy_pace_min_per_km are stored in min/km — convert before displaying. \
Distances in miles unless the athlete specifies otherwise.
"""

SCHEDULING_INSTRUCTION = """\
## Workout Scheduling

When you prescribe a weekly training plan, output it as a JSON block so the app \
can schedule it to Garmin. Use this exact schema inside a ```json code fence:

```json
{
  "week_starting": "YYYY-MM-DD",
  "sessions": [
    {
      "date": "YYYY-MM-DD",
      "workout_type": "easy_run|run_walk|tempo|intervals|strides|strength|mobility|yoga|cardio|hiit|walking|rest",
      "name": "Short name shown on watch",
      "duration_minutes": 30,
      "description": "Brief description of the session"
    }
  ]
}
```

Include every day of the week (rest days use workout_type "rest"). \
The user will review the plan in chat and may ask for changes — output a revised \
JSON block each time. Nothing is scheduled until the user explicitly clicks Schedule. \
Do NOT call Garmin tools directly — the app handles scheduling after confirmation. \
You may include coaching commentary before or after the JSON block.
"""


def _build_context() -> str:
    """Assemble athlete context from pace-ai database."""
    db = HistoryDB(DB_PATH)
    sections: list[str] = [COACHING_INSTRUCTION, SCHEDULING_INSTRUCTION]

    try:
        profile = get_athlete_profile(db)
        if profile:
            # Convert km-based fields to miles for display
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
            sections.append(
                f"## Athlete Profile\n{json.dumps(profile, indent=2, default=str)}"
            )
    except Exception:
        log.exception("Failed to load athlete profile")

    # ── Withings body composition ─────────────────────────────────────
    try:
        measurements = db.get_body_measurements(days=28)
        if measurements:
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

            # 4-week trend: compare first half vs second half
            if len(measurements) >= 4:
                mid = len(measurements) // 2
                recent_w = [
                    m["weight_kg"] for m in measurements[:mid] if m.get("weight_kg")
                ]
                older_w = [
                    m["weight_kg"] for m in measurements[mid:] if m.get("weight_kg")
                ]
                if recent_w and older_w:
                    diff = sum(recent_w) / len(recent_w) - sum(older_w) / len(older_w)
                    direction = (
                        "up" if diff > 0.3 else "down" if diff < -0.3 else "stable"
                    )
                    lines.append(f"- 4-week weight trend: {direction} ({diff:+.1f} kg)")

            sections.append("## Body Composition\n" + "\n".join(lines))
    except Exception:
        log.exception("Failed to load body measurements")

    # ── Notion diary entries ──────────────────────────────────────────
    try:
        diary = db.get_diary_entries(days=7)
        if diary:
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
            sections.append("## Diary (last 7 days)\n" + "\n".join(lines))
    except Exception:
        log.exception("Failed to load diary entries")

    try:
        facts = get_athlete_facts(db)
        if facts:
            lines = [f"- [{f['category']}] {f['fact']}" for f in facts]
            sections.append("## Athlete Facts\n" + "\n".join(lines))
    except Exception:
        log.exception("Failed to load athlete facts")

    try:
        ctx = get_coaching_context(db)
        if ctx:
            sections.append(f"## Coaching Context\n{ctx['content']}")
    except Exception:
        log.exception("Failed to load coaching context")

    try:
        logs = get_recent_coaching_log(db, limit=5)
        if logs:
            log_lines = []
            for entry in logs:
                line = f"- [{entry.get('created_at', '?')}] {entry.get('summary', '')}"
                if entry.get("follow_up"):
                    line += f" | Follow-up: {entry['follow_up']}"
                log_lines.append(line)
            sections.append("## Recent Coaching Sessions\n" + "\n".join(log_lines))
    except Exception:
        log.exception("Failed to load coaching log")

    return "\n\n".join(sections) if sections else ""


def _get_session_context() -> str:
    """Get or build context for the current session."""
    store = _get_store()
    ctx = store.get("athlete_context")
    if ctx is None:
        ctx = _build_context()
        store["athlete_context"] = ctx
    return ctx


@app.route("/")
def index():
    store = _get_store()
    messages = store.get("messages", [])
    ctx = store.get("athlete_context")
    if ctx:
        parts = [s.split("\n")[0] for s in ctx.split("## ") if s.strip()]
        context_status = f"Context loaded: {', '.join(parts)}"
    else:
        context_status = None
    has_pending_plan = "pending_plan" in store
    return render_template_string(
        HTML,
        messages=messages,
        context_status=context_status,
        has_pending_plan=has_pending_plan,
    )


@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.form.get("message", "").strip()
    if not user_message:
        return Response(status=302, headers={"Location": "/"})

    store = _get_store()
    store["messages"].append({"role": "user", "content": user_message})

    context = _get_session_context()
    cmd = list(CLAUDE_CMD)
    if context:
        cmd.extend(["--system-prompt", context])

    log.info("--- claude -p call ---")
    log.info(
        "cmd: %s", " ".join(cmd[:4]) + (" --system-prompt <...>" if context else "")
    )
    log.info("system prompt length: %d chars", len(context))
    log.info("user message: %r", user_message[:100])

    try:
        result = subprocess.run(
            cmd,
            input=user_message,
            capture_output=True,
            text=True,
            timeout=120,
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

    # Check if the response contains a weekly plan for confirmation
    plan = _extract_weekly_plan(reply)
    if plan:
        log.info(
            "Detected weekly plan: %s, %d sessions",
            plan.get("week_starting"),
            len(plan.get("sessions", [])),
        )
        store["pending_plan"] = plan
        # Strip the JSON block (fenced or bare) and replace with a readable table
        display_reply = re.sub(
            r"```json\s*\n\{.*?\}\s*\n```", "", reply, flags=re.DOTALL
        )
        # Also strip bare JSON blocks containing week_starting
        display_reply = re.sub(
            r"\{\s*\n\s*\"week_starting\".*?\n\}", "", display_reply, flags=re.DOTALL
        ).strip()
        # Build a markdown table of the plan
        plan_table = (
            f"\n\n**Proposed plan — week of {plan.get('week_starting', '?')}:**\n\n"
        )
        plan_table += "| Date | Session | Type | Duration |\n|------|---------|------|----------|\n"
        for s in plan.get("sessions", []):
            plan_table += (
                f"| {s.get('date', '')} | {s.get('name', '')} "
                f"| {s.get('workout_type', '')} | {s.get('duration_minutes', '')}min |\n"
            )
        plan_table += "\nSuggest changes, or click **Schedule** when ready."
        if not display_reply:
            display_reply = "Here's your weekly plan."
        display_reply += plan_table
        store["messages"].append({"role": "assistant", "content": display_reply})
    else:
        store["messages"].append({"role": "assistant", "content": reply})

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

    # Clear the session after successful logging
    sid = session.get("sid")
    if sid and sid in _sessions:
        del _sessions[sid]
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

    # Invalidate cached context so next message picks up fresh data
    store["athlete_context"] = None

    return Response(status=302, headers={"Location": "/"})


@app.route("/review-plan", methods=["GET", "POST"])
def review_plan():
    store = _get_store()
    plan = store.get("pending_plan")
    if not plan:
        return Response(status=302, headers={"Location": "/"})
    return render_template_string(CONFIRM_PLAN_HTML, plan=plan)


@app.route("/confirm-plan", methods=["POST"])
def confirm_plan():
    store = _get_store()
    plan = store.pop("pending_plan", None)
    if not plan:
        return Response(status=302, headers={"Location": "/"})

    from garmin_mcp.client import GarminClient
    from garmin_mcp.config import Settings as GarminSettings
    from garmin_mcp.workout_builder import WORKOUT_TYPES

    garmin_settings = GarminSettings.from_env()
    garmin_client = GarminClient(garmin_settings)

    # Import builders locally
    from garmin_mcp.server import _build_workout

    results = []
    ok_count = 0
    fail_count = 0
    skip_count = 0

    for s in plan.get("sessions", []):
        workout_type = s.get("workout_type", "")
        name = s.get("name", "Workout")
        date = s.get("date", "")

        if workout_type == "rest":
            results.append(
                {
                    "date": date,
                    "name": name,
                    "status": "skipped (rest day)",
                    "css": "skip",
                }
            )
            skip_count += 1
            continue

        if workout_type not in WORKOUT_TYPES:
            results.append(
                {
                    "date": date,
                    "name": name,
                    "status": f"skipped (unknown type: {workout_type})",
                    "css": "skip",
                }
            )
            skip_count += 1
            continue

        # Build params from the session data — only pass what each builder accepts
        params = {}
        duration = s.get("duration_minutes")
        # Types that accept duration_minutes directly
        _DURATION_TYPES = {"easy_run", "run_walk", "tempo", "yoga", "cardio", "walking"}
        if duration and workout_type in _DURATION_TYPES:
            params["duration_minutes"] = duration

        try:
            description = s.get("description", "")
            # For types that need structured data (strength/mobility) but only got
            # a description from the plan, parse it into lap-button steps
            _STRUCTURED_TYPES = {"strength", "mobility"}
            if workout_type in _STRUCTURED_TYPES and "exercises" not in params:
                from garmin_mcp.workout_builder import custom_workout

                steps = _description_to_steps(description, duration)
                workout_json = custom_workout(
                    name, steps_json=steps, description=description
                )
            else:
                workout_json = _build_workout(workout_type, name, params)
                # Inject the plan description so it shows in Garmin Connect
                if description:
                    workout_json["description"] = description
            result = garmin_client.create_workout(workout_json)
            workout_id = result.get("workoutId") if isinstance(result, dict) else None
            if not workout_id:
                results.append(
                    {
                        "date": date,
                        "name": name,
                        "status": "created but no ID returned",
                        "css": "fail",
                    }
                )
                fail_count += 1
                continue
            garmin_client.schedule_workout(workout_id, date)
            results.append(
                {
                    "date": date,
                    "name": name,
                    "status": f"scheduled (ID {workout_id})",
                    "css": "ok",
                }
            )
            ok_count += 1
        except Exception as e:
            log.exception("Failed to create/schedule workout: %s", name)
            results.append(
                {"date": date, "name": name, "status": f"error: {e}", "css": "fail"}
            )
            fail_count += 1

    # Store confirmed plan for end-session summarisation
    store["confirmed_plan"] = plan

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


@app.route("/clear", methods=["POST"])
def clear():
    sid = session.get("sid")
    if sid and sid in _sessions:
        del _sessions[sid]
    session.clear()
    return Response(status=302, headers={"Location": "/"})


if __name__ == "__main__":
    import os
    import webbrowser

    # Only open browser in the reloader parent, not the child process
    if os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        webbrowser.open("http://localhost:5050")
    app.run(debug=True, port=5050)
