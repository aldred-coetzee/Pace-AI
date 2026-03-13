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


def _build_context() -> str:
    """Assemble athlete context from pace-ai database."""
    db = HistoryDB(DB_PATH)
    sections: list[str] = []

    try:
        profile = get_athlete_profile(db)
        if profile:
            sections.append(
                f"## Athlete Profile\n{json.dumps(profile, indent=2, default=str)}"
            )
    except Exception:
        log.exception("Failed to load athlete profile")

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
    return render_template_string(
        HTML, messages=messages, context_status=context_status
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

    prompt = (
        "Here is a coaching conversation and the current coaching context.\n\n"
        f"EXISTING COACHING CONTEXT:\n{existing_content}\n\n"
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


@app.route("/clear", methods=["POST"])
def clear():
    sid = session.get("sid")
    if sid and sid in _sessions:
        del _sessions[sid]
    session.clear()
    return Response(status=302, headers={"Location": "/"})


if __name__ == "__main__":
    import webbrowser

    webbrowser.open("http://localhost:5050")
    app.run(debug=True, port=5050)
