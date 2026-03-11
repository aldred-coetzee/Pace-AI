"""Flask chat UI for Pace-AI with athlete context injection."""

from __future__ import annotations

import json
import logging
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
    get_athlete_facts,
    get_coaching_context,
    get_recent_coaching_log,
)
from pace_ai.tools.profile import get_athlete_profile

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
<style>
body { font-family: monospace; max-width: 800px; margin: 40px auto; padding: 0 20px; background: #1a1a1a; color: #e0e0e0; }
h1 { font-size: 1.2em; color: #aaa; }
.messages { margin-bottom: 20px; }
.msg { padding: 8px 12px; margin: 6px 0; border-radius: 4px; white-space: pre-wrap; word-wrap: break-word; }
.user { background: #2a3a4a; border-left: 3px solid #4a9eff; }
.assistant { background: #2a2a2a; border-left: 3px solid #6c6; }
.ctx-banner { background: #1e2e1e; border: 1px solid #3a5a3a; padding: 6px 12px; border-radius: 4px; margin-bottom: 12px; font-size: 0.85em; color: #8a8; }
form { display: flex; gap: 8px; }
textarea { flex: 1; padding: 8px; font-family: monospace; font-size: 14px; background: #222; color: #e0e0e0; border: 1px solid #444; border-radius: 4px; resize: vertical; min-height: 60px; }
button { padding: 8px 20px; background: #4a9eff; color: #fff; border: none; border-radius: 4px; cursor: pointer; font-family: monospace; }
button:hover { background: #3a8eef; }
.clear-btn { background: #555; font-size: 0.85em; padding: 4px 12px; }
.clear-btn:hover { background: #666; }
.spinner { display: none; color: #888; margin: 10px 0; }
.controls { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
</style>
</head>
<body>
<div class="controls">
<h1>Pace-AI Chat (dev)</h1>
<form method="POST" action="/clear" style="display:inline;">
<button type="submit" class="clear-btn">Clear session</button>
</form>
</div>
{% if context_status %}
<div class="ctx-banner">{{ context_status }}</div>
{% endif %}
<div class="messages">
{% for msg in messages %}
<div class="msg {{ msg.role }}"><strong>{{ msg.role }}:</strong> {{ msg.content }}</div>
{% endfor %}
</div>
<div class="spinner" id="spinner">Thinking...</div>
<form method="POST" action="/chat" id="chat-form">
<textarea name="message" placeholder="Type a message..." autofocus></textarea>
<button type="submit">Send</button>
</form>
<script>
document.getElementById('chat-form').addEventListener('submit', function() {
    document.getElementById('spinner').style.display = 'block';
    document.querySelector('button[type=submit]').disabled = true;
});
</script>
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


@app.route("/clear", methods=["POST"])
def clear():
    sid = session.get("sid")
    if sid and sid in _sessions:
        del _sessions[sid]
    session.clear()
    return Response(status=302, headers={"Location": "/"})


if __name__ == "__main__":
    app.run(debug=True, port=5050)
