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
from pace_ai.tools.history import get_recent_activities, get_weekly_distances
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

# Server-side session store — persisted to SQLite so sessions survive restarts
_SESSION_DB = str(PROJECT_ROOT / "ui_sessions.db")


def _init_session_db() -> None:
    """Create the sessions and conversations tables if they don't exist."""
    import sqlite3

    conn = sqlite3.connect(_SESSION_DB)
    conn.execute(
        """CREATE TABLE IF NOT EXISTS sessions (
            sid TEXT PRIMARY KEY,
            data TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )"""
    )
    conn.execute(
        """CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            messages TEXT NOT NULL,
            summary TEXT,
            plan TEXT
        )"""
    )
    conn.commit()
    conn.close()


_init_session_db()

# In-memory cache backed by SQLite
_sessions: dict[str, dict] = {}


def _load_session(sid: str) -> dict | None:
    """Load a session from SQLite."""
    import sqlite3

    conn = sqlite3.connect(_SESSION_DB)
    row = conn.execute("SELECT data FROM sessions WHERE sid = ?", (sid,)).fetchone()
    conn.close()
    if row:
        return json.loads(row[0])
    return None


def _save_session(sid: str, data: dict) -> None:
    """Persist a session to SQLite."""
    import sqlite3

    conn = sqlite3.connect(_SESSION_DB)
    conn.execute(
        "INSERT OR REPLACE INTO sessions (sid, data, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)",
        (sid, json.dumps(data, default=str)),
    )
    conn.commit()
    conn.close()


def _delete_session(sid: str) -> None:
    """Remove a session from SQLite."""
    import sqlite3

    conn = sqlite3.connect(_SESSION_DB)
    conn.execute("DELETE FROM sessions WHERE sid = ?", (sid,))
    conn.commit()
    conn.close()


def _get_store() -> dict:
    """Get or create server-side session store for the current request."""
    sid = session.get("sid")
    if sid is not None and sid not in _sessions:
        # Try to recover from SQLite (e.g. after server restart)
        stored = _load_session(sid)
        if stored:
            _sessions[sid] = stored
    if sid is None or sid not in _sessions:
        sid = uuid.uuid4().hex
        session["sid"] = sid
        _sessions[sid] = {"messages": []}
    return _sessions[sid]


def _persist_store() -> None:
    """Save the current session to SQLite. Call after any mutation."""
    sid = session.get("sid")
    if sid and sid in _sessions:
        _save_session(sid, _sessions[sid])


@app.after_request
def _auto_persist_session(response):
    """Persist session to SQLite after every request."""
    _persist_store()
    return response


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
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="/static/favicon.ico" type="image/x-icon">
<title>Pace AI</title>
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
<style>
:root {
  color-scheme: dark;
  --bg-primary: #0F0F0F;
  --bg-secondary: #161616;
  --bg-tertiary: #1C1C1E;
  --text-primary: #FAFAFA;
  --text-secondary: #A1A1A1;
  --text-tertiary: #666;
  --border: #262626;
  --border-soft: #1F1F1F;
  --accent: #3B82F6;
  --accent-hover: #60A5FA;
  --accent-glow: rgba(59, 130, 246, 0.1);
  --success: #10B981;
  --warning: #F59E0B;
  --danger: #EF4444;
  --overlay: rgba(255, 255, 255, 0.05);
  --font: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  --mono: "SF Mono", Monaco, "Cascadia Code", "Roboto Mono", Menlo, monospace;
}
*, *::before, *::after { box-sizing: border-box; }
body { font: 14px/1.5 var(--font); letter-spacing: -0.01em; margin: 0; padding: 0;
       background: var(--bg-primary); color: var(--text-primary); }
a { color: var(--accent); text-decoration: none; }
a:hover { color: var(--accent-hover); }

/* ── Navbar ── */
.navbar { background: var(--bg-secondary); border-bottom: 1px solid var(--border);
          padding: 0 24px; display: flex; align-items: center; height: 48px; gap: 16px;
          position: sticky; top: 0; z-index: 100; }
.navbar-brand { font-weight: 600; font-size: 15px; color: var(--text-primary);
                margin-right: auto; letter-spacing: -0.02em; }
.navbar-brand span { color: var(--accent); }

/* ── Buttons ── */
.btn { display: inline-flex; align-items: center; gap: 6px; padding: 6px 14px;
       border: 1px solid var(--border); border-radius: 6px; font: 13px/1 var(--font);
       font-weight: 500; cursor: pointer; transition: all 0.15s ease;
       background: transparent; color: var(--text-primary); white-space: nowrap; }
.btn:hover { background: var(--overlay); border-color: var(--text-tertiary); }
.btn:disabled { opacity: 0.4; cursor: not-allowed; }
.btn-primary { background: var(--accent); border-color: var(--accent); color: #fff; }
.btn-primary:hover { background: var(--accent-hover); border-color: var(--accent-hover);
                     box-shadow: 0 0 0 3px var(--accent-glow); }
.btn-danger { border-color: rgba(239,68,68,0.3); color: #FCA5A5; }
.btn-danger:hover { background: rgba(239,68,68,0.1); border-color: rgba(239,68,68,0.5); }
.btn-success { border-color: rgba(16,185,129,0.3); color: #6EE7B7; }
.btn-success:hover { background: rgba(16,185,129,0.1); border-color: rgba(16,185,129,0.5); }

/* ── Layout ── */
.container { max-width: 960px; margin: 0 auto; padding: 24px 24px 120px; }

/* ── Toolbar ── */
.toolbar { display: flex; align-items: center; gap: 8px; padding: 12px 0;
           border-bottom: 1px solid var(--border); margin-bottom: 16px; flex-wrap: wrap; }
.toolbar-group { display: flex; align-items: center; gap: 6px; }
.toolbar-sep { width: 1px; height: 20px; background: var(--border); margin: 0 4px; }
.toolbar input[type="date"] { padding: 5px 8px; font: 13px var(--font);
  background: var(--bg-tertiary); color: var(--text-primary);
  border: 1px solid var(--border); border-radius: 6px; color-scheme: dark; }
.toolbar label { font-size: 12px; color: var(--text-secondary); }
.toolbar .meta { font-size: 12px; color: var(--text-tertiary); margin-left: auto; }

/* ── Banners ── */
.banner { padding: 10px 16px; border-radius: 8px; font-size: 13px;
          margin-bottom: 12px; display: flex; align-items: center; gap: 10px;
          background: var(--overlay); border-left: 3px solid var(--border); }
.banner-info { border-left-color: var(--accent); color: #93C5FD; }
.banner-success { border-left-color: var(--success); color: #6EE7B7; }
.banner-warn { border-left-color: var(--warning); color: #FCD34D; }
.banner-crit { border-left-color: var(--danger); color: #FCA5A5; }

/* ── Session bar ── */
.session-bar { font-size: 12px; color: var(--text-tertiary); padding: 4px 0;
               display: flex; justify-content: space-between; margin-bottom: 12px; }

/* ── Messages ── */
.messages { display: flex; flex-direction: column; gap: 16px; margin-bottom: 24px; }
.msg { padding: 14px 18px; border-radius: 8px; word-wrap: break-word;
       line-height: 1.6; font-size: 14px; }
.msg.user { background: var(--bg-tertiary); border: 1px solid var(--border);
            white-space: pre-wrap; }
.msg.user .msg-label { font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px;
                       color: var(--text-tertiary); margin-bottom: 6px; }
.msg.assistant { background: var(--bg-secondary); border: 1px solid var(--border-soft); }
.msg.assistant .msg-label { font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px;
                            color: var(--success); margin-bottom: 6px; }
.msg.assistant table { border-collapse: collapse; margin: 12px 0; width: 100%;
                       font-size: 13px; }
.msg.assistant th, .msg.assistant td { border: 1px solid var(--border);
  padding: 8px 12px; text-align: left; }
.msg.assistant th { background: var(--bg-tertiary); font-size: 11px;
  text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600;
  color: var(--text-secondary); }
.msg.assistant td { color: var(--text-primary); }
.msg.assistant tbody tr:hover { background: var(--overlay); }
.msg.assistant blockquote { border-left: 3px solid var(--border); margin: 12px 0;
  padding: 8px 16px; color: var(--text-secondary); }
.msg.assistant code { background: var(--bg-tertiary); padding: 2px 6px;
  border-radius: 4px; font: 13px var(--mono); }
.msg.assistant pre { background: var(--bg-tertiary); border: 1px solid var(--border);
  padding: 14px; border-radius: 6px; overflow-x: auto; margin: 12px 0; }
.msg.assistant h2 { font-size: 16px; font-weight: 600; margin: 20px 0 8px;
  letter-spacing: -0.02em; }
.msg.assistant h3 { font-size: 14px; font-weight: 600; margin: 16px 0 6px;
  letter-spacing: -0.01em; }
.msg.assistant hr { border: none; border-top: 1px solid var(--border); margin: 16px 0; }
.msg.assistant ul, .msg.assistant ol { padding-left: 20px; margin: 8px 0; }
.msg.assistant li { margin: 4px 0; }
.msg.assistant strong { color: var(--text-primary); }

/* ── Plan bar ── */
.plan-bar { padding: 12px 16px; border-radius: 8px; margin-bottom: 16px;
            display: flex; gap: 10px; align-items: center;
            background: rgba(59,130,246,0.08); border: 1px solid rgba(59,130,246,0.2); }
.plan-bar span { font-size: 13px; color: #93C5FD; flex: 1; }

/* ── Spinner ── */
.spinner { display: none; padding: 12px 0; }
.spinner-inner { display: flex; align-items: center; gap: 10px;
                 font-size: 13px; color: var(--text-secondary); }
.spinner-dot { width: 8px; height: 8px; border-radius: 50%;
               background: var(--accent); animation: pulse 1.4s infinite ease-in-out; }
@keyframes pulse { 0%, 100% { opacity: 0.3; transform: scale(0.8); }
                   50% { opacity: 1; transform: scale(1); } }

/* ── Chat input ── */
.chat-input { display: flex; gap: 8px; position: fixed; bottom: 0; left: 0; right: 0;
              padding: 16px 24px; background: var(--bg-primary);
              border-top: 1px solid var(--border); }
.chat-input-inner { max-width: 960px; margin: 0 auto; width: 100%;
                    display: flex; gap: 8px; }
.chat-input textarea { flex: 1; padding: 10px 14px; font: 14px/1.5 var(--font);
  background: var(--bg-secondary); color: var(--text-primary);
  border: 1px solid var(--border); border-radius: 8px; resize: none; min-height: 44px;
  max-height: 120px; transition: border-color 0.15s; }
.chat-input textarea:focus { outline: none; border-color: var(--accent);
  box-shadow: 0 0 0 3px var(--accent-glow); }
.chat-input textarea::placeholder { color: var(--text-tertiary); }
</style>
</head>
<body>
<nav class="navbar">
<div class="navbar-brand">Pace <span>AI</span></div>
<form method="POST" action="/sync" class="ctrl-form" id="sync-form">
<button type="submit" class="btn btn-success">Sync</button>
</form>
<form method="POST" action="/status" class="ctrl-form" id="status-form">
<button type="submit" class="btn">Status</button>
</form>
<a href="/history" class="btn">History</a>
<form method="POST" action="/clear" class="ctrl-form">
<button type="submit" class="btn">Clear</button>
</form>
<form method="POST" action="/end-session" class="ctrl-form">
<button type="submit" class="btn btn-danger">End Session</button>
</form>
</nav>
<div class="container">
<div class="toolbar">
<form method="POST" action="/plan" class="ctrl-form toolbar-group" id="plan-form">
<label>From</label>
<input type="date" name="date_from" value="{{ default_date_from }}">
<label>To</label>
<input type="date" name="date_to" value="{{ default_date_to }}">
<button type="submit" class="btn btn-primary">Generate Plan</button>
</form>
{% if status_cached %}
<span class="meta">Status cached {{ status_age }}</span>
{% endif %}
<span class="meta">{{ message_count }} messages</span>
</div>
{% if sync_status %}
<div class="banner banner-info">{{ sync_status }}</div>
{% endif %}
{% if session_tokens > 80 %}
<div class="banner banner-crit">Session very large — consider ending and starting fresh</div>
{% elif session_tokens > 40 %}
<div class="banner banner-warn">Session getting large — end session soon</div>
{% endif %}
<div class="messages">
{% for msg in messages %}
{% if msg.role == 'user' %}
<div class="msg user">
<div class="msg-label">You</div>
{{ msg.content }}
</div>
{% else %}
<div class="msg assistant">
<div class="msg-label">Coach</div>
<div class="md-content">{{ msg.content }}</div>
</div>
{% endif %}
{% endfor %}
</div>
{% if has_pending_plan %}
<div class="plan-bar">
<span>Plan ready to schedule</span>
<form method="POST" action="/review-plan"><button type="submit" class="btn btn-primary">Schedule</button></form>
<form method="POST" action="/cancel-plan"><button type="submit" class="btn">Discard</button></form>
</div>
{% endif %}
<div class="spinner" id="spinner">
<div class="spinner-inner"><div class="spinner-dot"></div> <span>Thinking...</span></div>
</div>
</div>
<div class="chat-input">
<div class="chat-input-inner">
<form method="POST" action="/chat" id="chat-form" style="display:flex;gap:8px;width:100%;">
<textarea name="message" placeholder="Ask your coach..." autofocus rows="1"></textarea>
<button type="submit" class="btn btn-primary" id="send-btn">Send</button>
</form>
</div>
</div>
<script>
document.querySelectorAll('.md-content').forEach(function(el) {
    el.innerHTML = marked.parse(el.textContent);
});
function disableAll() {
    document.querySelectorAll('button').forEach(function(b) { b.disabled = true; });
}
document.getElementById('chat-form').addEventListener('submit', function() {
    document.getElementById('spinner').style.display = 'block';
    disableAll();
});
document.querySelectorAll('.ctrl-form').forEach(function(f) {
    f.addEventListener('submit', function() { disableAll(); });
});
document.getElementById('sync-form').addEventListener('submit', function() {
    document.querySelector('#spinner .spinner-inner span').textContent = 'Syncing...';
    document.getElementById('spinner').style.display = 'block';
});
document.getElementById('status-form').addEventListener('submit', function() {
    document.querySelector('#spinner .spinner-inner span').textContent = 'Checking status...';
    document.getElementById('spinner').style.display = 'block';
    disableAll();
});
document.getElementById('plan-form').addEventListener('submit', function() {
    document.querySelector('#spinner .spinner-inner span').textContent = 'Generating plan...';
    document.getElementById('spinner').style.display = 'block';
    disableAll();
});
// Auto-grow textarea
var ta = document.querySelector('.chat-input textarea');
ta.addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = Math.min(this.scrollHeight, 120) + 'px';
});
window.scrollTo(0, document.body.scrollHeight);
</script>
</body>
</html>
"""


END_SESSION_HTML = """\
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="/static/favicon.ico" type="image/x-icon">
<title>Pace AI — Session Logged</title>
<style>
:root { color-scheme: dark;
  --bg-primary: #0F0F0F; --bg-secondary: #161616; --bg-tertiary: #1C1C1E;
  --text-primary: #FAFAFA; --text-secondary: #A1A1A1; --border: #262626;
  --accent: #3B82F6; --danger: #EF4444; --success: #10B981;
  --font: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
*, *::before, *::after { box-sizing: border-box; }
body { font: 14px/1.6 var(--font); margin: 0; padding: 0;
       background: var(--bg-primary); color: var(--text-primary); }
a { color: var(--accent); text-decoration: none; }
.container { max-width: 960px; margin: 0 auto; padding: 32px 24px; }
h1 { font-size: 20px; font-weight: 600; letter-spacing: -0.02em; margin-bottom: 24px; }
h2 { font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px;
     color: var(--text-secondary); font-weight: 600; margin: 24px 0 8px; }
.section { background: var(--bg-secondary); border: 1px solid var(--border);
           padding: 14px 18px; border-radius: 8px; margin: 8px 0;
           white-space: pre-wrap; word-wrap: break-word; line-height: 1.6; }
.error { background: rgba(239,68,68,0.08); border: 1px solid rgba(239,68,68,0.2);
         padding: 14px 18px; border-radius: 8px; margin: 8px 0;
         white-space: pre-wrap; word-wrap: break-word; color: #FCA5A5; }
ul { margin: 4px 0; padding-left: 20px; }
li { margin: 4px 0; }
.back { display: inline-flex; align-items: center; gap: 6px; margin-top: 24px;
        font-size: 13px; color: var(--text-secondary); }
.back:hover { color: var(--accent); }
</style>
</head>
<body>
<div class="container">
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
<a href="/" class="back">Back to chat</a>
</div>
</body>
</html>
"""


CONFIRM_PLAN_HTML = """\
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="/static/favicon.ico" type="image/x-icon">
<title>Pace AI — Confirm Plan</title>
<style>
:root { color-scheme: dark;
  --bg-primary: #0F0F0F; --bg-secondary: #161616; --bg-tertiary: #1C1C1E;
  --text-primary: #FAFAFA; --text-secondary: #A1A1A1; --text-tertiary: #666;
  --border: #262626; --accent: #3B82F6; --accent-hover: #60A5FA;
  --accent-glow: rgba(59,130,246,0.1); --overlay: rgba(255,255,255,0.05);
  --font: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
*, *::before, *::after { box-sizing: border-box; }
body { font: 14px/1.5 var(--font); margin: 0; padding: 0;
       background: var(--bg-primary); color: var(--text-primary); }
a { color: var(--accent); text-decoration: none; }
.container { max-width: 960px; margin: 0 auto; padding: 32px 24px; }
h1 { font-size: 20px; font-weight: 600; letter-spacing: -0.02em; margin-bottom: 4px; }
h2 { font-size: 13px; color: var(--text-secondary); font-weight: 400; margin-bottom: 20px; }
.table-wrap { border: 1px solid var(--border); border-radius: 8px; overflow: hidden;
              background: var(--bg-secondary); }
table { border-collapse: collapse; width: 100%; font-size: 13px; }
th { padding: 10px 14px; text-align: left; font-size: 11px; text-transform: uppercase;
     letter-spacing: 0.5px; font-weight: 600; color: var(--text-secondary);
     background: var(--bg-tertiary); border-bottom: 1px solid var(--border); }
td { padding: 10px 14px; border-bottom: 1px solid var(--border); }
tr:last-child td { border-bottom: none; }
tr:hover { background: var(--overlay); }
tr.rest td { color: var(--text-tertiary); }
p { font-size: 13px; color: var(--text-secondary); margin: 16px 0; }
.btn-row { display: flex; gap: 8px; margin-top: 20px; align-items: center; }
.btn { display: inline-flex; align-items: center; padding: 8px 18px;
       border: 1px solid var(--border); border-radius: 6px;
       font: 13px/1 var(--font); font-weight: 500; cursor: pointer;
       transition: all 0.15s; background: transparent; color: var(--text-primary); }
.btn:hover { background: var(--overlay); }
.btn-primary { background: var(--accent); border-color: var(--accent); color: #fff; }
.btn-primary:hover { background: var(--accent-hover); border-color: var(--accent-hover);
                     box-shadow: 0 0 0 3px var(--accent-glow); }
.back { font-size: 13px; color: var(--text-tertiary); margin-left: 8px; }
.back:hover { color: var(--accent); }
</style>
</head>
<body>
<div class="container">
<h1>Confirm Plan</h1>
<h2>Week starting {{ plan.week_starting }}</h2>
<div class="table-wrap">
<table>
<thead><tr><th>Date</th><th>Session</th><th>Type</th><th>Duration</th><th>Description</th></tr></thead>
<tbody>
{% for s in plan.sessions %}
<tr class="{{ 'rest' if s.workout_type == 'rest' else '' }}">
<td>{{ s.date }}</td>
<td>{{ s.name }}</td>
<td>{{ s.workout_type }}</td>
<td>{{ s.duration_minutes }}min</td>
<td>{{ s.description or '' }}</td>
</tr>
{% endfor %}
</tbody>
</table>
</div>
<p>{{ plan.sessions | selectattr('workout_type', 'ne', 'rest') | list | length }} sessions will be created and scheduled in Garmin Connect. Rest days are skipped.</p>
<div class="btn-row">
<form method="POST" action="/confirm-plan">
<button type="submit" class="btn btn-primary">Confirm &amp; Schedule</button>
</form>
<form method="POST" action="/cancel-plan">
<button type="submit" class="btn">Cancel</button>
</form>
<a href="/" class="back">Back to chat</a>
</div>
</div>
</body>
</html>
"""


HISTORY_HTML = """\
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="/static/favicon.ico" type="image/x-icon">
<title>Pace AI — History</title>
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
<style>
:root { color-scheme: dark;
  --bg-primary: #0F0F0F; --bg-secondary: #161616; --bg-tertiary: #1C1C1E;
  --text-primary: #FAFAFA; --text-secondary: #A1A1A1; --text-tertiary: #666;
  --border: #262626; --accent: #3B82F6; --success: #10B981;
  --overlay: rgba(255,255,255,0.05);
  --font: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
*, *::before, *::after { box-sizing: border-box; }
body { font: 14px/1.5 var(--font); margin: 0; padding: 0;
       background: var(--bg-primary); color: var(--text-primary); }
a { color: var(--accent); text-decoration: none; }
.container { max-width: 960px; margin: 0 auto; padding: 32px 24px; }
.header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 24px; }
h1 { font-size: 20px; font-weight: 600; letter-spacing: -0.02em; margin: 0; }
.back { font-size: 13px; color: var(--text-secondary); }
.back:hover { color: var(--accent); }
.session { background: var(--bg-secondary); border: 1px solid var(--border);
           border-radius: 8px; margin: 10px 0; overflow: hidden; }
.session-header { padding: 14px 18px; cursor: pointer; display: flex;
                  justify-content: space-between; align-items: center;
                  transition: background 0.15s; }
.session-header:hover { background: var(--overlay); }
.session-date { font-weight: 500; font-size: 13px; }
.session-summary { color: var(--text-secondary); font-size: 13px; margin-left: 12px; }
.session-meta { font-size: 12px; color: var(--text-tertiary); }
.session-body { display: none; padding: 0 18px 18px; border-top: 1px solid var(--border); }
.session-body.open { display: block; }
.msg { padding: 10px 14px; margin: 6px 0; border-radius: 6px; word-wrap: break-word;
       font-size: 13px; line-height: 1.5; }
.msg.user { background: var(--bg-tertiary); border: 1px solid var(--border);
            white-space: pre-wrap; }
.msg.user .msg-label { font-size: 10px; text-transform: uppercase; letter-spacing: 0.5px;
                       color: var(--text-tertiary); margin-bottom: 4px; }
.msg.assistant { background: var(--bg-primary); border: 1px solid var(--border); }
.msg.assistant .msg-label { font-size: 10px; text-transform: uppercase; letter-spacing: 0.5px;
                            color: var(--success); margin-bottom: 4px; }
.no-history { color: var(--text-tertiary); padding: 40px; text-align: center;
              font-size: 13px; }
</style>
</head>
<body>
<div class="container">
<div class="header">
<h1>Session History</h1>
<a href="/" class="back">Back to chat</a>
</div>
{% if sessions %}
{% for s in sessions %}
<div class="session">
<div class="session-header" onclick="this.nextElementSibling.classList.toggle('open')">
<span>
<span class="session-date">{{ s.date }}</span>
<span class="session-summary">{{ s.summary or '(no summary)' }}</span>
</span>
<span class="session-meta">{{ s.message_count }} messages</span>
</div>
<div class="session-body">
{% for msg in s.messages %}
{% if msg.role == 'user' %}
<div class="msg user">
<div class="msg-label">You</div>
{{ msg.content }}
</div>
{% else %}
<div class="msg assistant">
<div class="msg-label">Coach</div>
<div class="md-content">{{ msg.content }}</div>
</div>
{% endif %}
{% endfor %}
</div>
</div>
{% endfor %}
{% else %}
<div class="no-history">No sessions yet. End a coaching session to save it here.</div>
{% endif %}
<script>
document.querySelectorAll('.md-content').forEach(function(el) {
    el.innerHTML = marked.parse(el.textContent);
});
</script>
</div>
</body>
</html>
"""


def _extract_weekly_plan(text: str) -> dict | None:
    """Try to extract a weekly plan JSON block from Claude's response.

    Looks for a JSON object with 'week_starting' and 'sessions' keys,
    either bare or inside markdown code fences.
    """
    # Try to find JSON in code fences first (greedy — capture full nested JSON)
    fence_match = re.search(r"```(?:json)?\s*\n(\{.+\})\s*\n```", text, re.DOTALL)
    if fence_match:
        candidate = fence_match.group(1)
        try:
            data = json.loads(candidate)
            if "week_starting" in data and "sessions" in data:
                return data
        except json.JSONDecodeError:
            pass

    # Try to find bare JSON by locating "week_starting" and finding the enclosing {}
    if '"week_starting"' not in text:
        return None
    # Find all top-level { that could start a plan JSON
    for match in re.finditer(r"\{", text):
        start = match.start()
        # Try progressively longer substrings to find valid JSON
        depth = 0
        for i in range(start, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    candidate = text[start : i + 1]
                    try:
                        data = json.loads(candidate)
                        if "week_starting" in data and "sessions" in data:
                            return data
                    except json.JSONDecodeError:
                        pass
                    break

    return None


def _strip_plan_json(text: str) -> str:
    """Remove bare JSON plan blocks (containing week_starting) from text."""
    if '"week_starting"' not in text:
        return text
    result = text
    for match in re.finditer(r"\{", text):
        start = match.start()
        depth = 0
        for i in range(start, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    candidate = text[start : i + 1]
                    if '"week_starting"' in candidate and '"sessions"' in candidate:
                        try:
                            json.loads(candidate)
                            result = result.replace(candidate, "")
                        except json.JSONDecodeError:
                            pass
                    break
    return result


def _exercises_to_steps(exercises: list[dict]) -> list[dict]:
    """Convert structured exercises array into Garmin workout steps.

    Each exercise dict has 'name' and either 'sets'+'reps' or 'duration_s'.
    """
    _STEP_INTERVAL = {"stepTypeId": 3, "stepTypeKey": "interval"}
    _CONDITION_LAP = {"conditionTypeId": 1, "conditionTypeKey": "lap.button"}
    _CONDITION_TIME = {"conditionTypeId": 2, "conditionTypeKey": "time"}
    _TARGET_NONE = {"workoutTargetTypeId": 1, "workoutTargetTypeKey": "no.target"}

    steps: list[dict] = []
    for i, ex in enumerate(exercises, 1):
        name = ex.get("name", "Exercise")
        sets = ex.get("sets")
        reps = ex.get("reps")
        duration_s = ex.get("duration_s")

        if sets and reps:
            label = f"{sets}x{reps} {name}"
        elif duration_s:
            label = f"{name} ({duration_s}s)"
        else:
            label = name

        if len(label) > 50:
            label = label[:47] + "..."

        # Use timed step if duration_s given, lap-button otherwise
        if duration_s:
            steps.append(
                {
                    "type": "ExecutableStepDTO",
                    "stepId": None,
                    "stepOrder": i,
                    "stepType": _STEP_INTERVAL,
                    "endCondition": _CONDITION_TIME,
                    "endConditionValue": float(duration_s),
                    "targetType": _TARGET_NONE,
                    "description": label,
                }
            )
        else:
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


def _description_to_steps(description: str, duration_minutes: int | None) -> list[dict]:
    """Parse a workout description into Garmin custom workout steps.

    Extracts exercises in various formats:
    - "3x15 heel drops" or "heel drops 3x15"
    - "calves 60s/side" or "foam roll calves 60 sec"
    Creates a lap-button step per exercise. Falls back to a single timed step
    if no exercises are found.

    Returns raw Garmin ExecutableStepDTO dicts.
    """
    _STEP_INTERVAL = {"stepTypeId": 3, "stepTypeKey": "interval"}
    _CONDITION_LAP = {"conditionTypeId": 1, "conditionTypeKey": "lap.button"}
    _CONDITION_TIME = {"conditionTypeId": 2, "conditionTypeKey": "time"}
    _TARGET_NONE = {"workoutTargetTypeId": 1, "workoutTargetTypeKey": "no.target"}

    # Each item is (label, duration_s or None)
    items: list[tuple[str, int | None]] = []

    # Pattern 1: "3x15 exercise name" (sets before name)
    for m in re.finditer(
        r"(\d+)\s*x\s*(\d+)\s+([a-zA-Z][\w\s\-()]+?)(?:\.|,|$)", description
    ):
        sets, reps, name = m.group(1), m.group(2), m.group(3).strip().rstrip(")")
        items.append((f"{sets}x{reps} {name}", None))

    # Pattern 2: "exercise name (qualifier) 3x15" (sets after name)
    for m in re.finditer(
        r"([a-zA-Z][\w\s\-]+(?:\([^)]*\))?)\s+(\d+)\s*x\s*(\d+)(?:\s|,|\.|$)",
        description,
    ):
        name, sets, reps = m.group(1).strip(), m.group(2), m.group(3)
        label = f"{sets}x{reps} {name}"
        if not any(label == it[0] for it in items):
            items.append((label, None))

    # Pattern 3: timed items — "calves 60s/side", "foam roll quads 60 sec each"
    for m in re.finditer(
        r"([a-zA-Z][\w\s\-]+?)\s+(\d+)\s*s(?:ec)?(?:\s+each|/side)?(?:\.|,|$)",
        description,
    ):
        name, secs = m.group(1).strip(), int(m.group(2))
        # Split compound items like "Foam roll calves and quads" into separate steps
        if " and " in name:
            prefix = ""
            parts = name.split(" and ")
            words = parts[0].split()
            if len(words) > 1 and not words[-1][0].isupper():
                prefix = " ".join(words[:-1]) + " "
                parts[0] = words[-1]
            for part in parts:
                part_label = f"{prefix}{part.strip()} ({secs}s)"
                if not any(
                    part.strip().lower() in existing[0].lower() for existing in items
                ):
                    items.append((part_label, secs))
        else:
            label = f"{name} ({secs}s)"
            if not any(name.lower() in existing[0].lower() for existing in items):
                items.append((label, secs))

    if not items:
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
    for i, (label, dur_s) in enumerate(items, 1):
        if len(label) > 50:
            label = label[:47] + "..."
        step: dict = {
            "type": "ExecutableStepDTO",
            "stepId": None,
            "stepOrder": i,
            "stepType": _STEP_INTERVAL,
            "targetType": _TARGET_NONE,
            "description": label,
        }
        if dur_s:
            step["endCondition"] = _CONDITION_TIME
            step["endConditionValue"] = float(dur_s)
        else:
            step["endCondition"] = _CONDITION_LAP
        steps.append(step)

    return steps


def _enrich_plan_with_exercises(plan: dict) -> dict | None:
    """Send a focused claude -p call to generate exercises for strength/mobility sessions.

    Returns the enriched plan with exercises arrays, or None on failure.
    """
    prompt = (
        "Convert this training plan to JSON with exercises arrays for every "
        "strength, mobility, and yoga session.\n\n"
        "Input plan:\n" + json.dumps(plan, indent=2) + "\n\n"
        "Rules:\n"
        "- Add an exercises array to every strength/mobility/yoga session\n"
        '- Each exercise: {"name": "...", "sets": N, "reps": N} or '
        '{"name": "...", "duration_s": N}\n'
        "- Include foam rolling exercises with duration_s (e.g. 60 or 120)\n"
        "- Include Achilles-specific exercises (heel drops, calf raises) if relevant\n"
        "- Keep all other fields exactly as they are\n"
        "- Output ONLY the JSON, no commentary\n"
    )
    try:
        result = subprocess.run(
            CLAUDE_CMD,
            input=prompt,
            capture_output=True,
            text=True,
            timeout=120,
            cwd=str(PROJECT_ROOT),
        )
        enriched = _extract_weekly_plan(result.stdout.strip())
        if enriched and enriched.get("sessions"):
            # Verify exercises were actually added
            has_exercises = any(
                s.get("exercises")
                for s in enriched.get("sessions", [])
                if s.get("workout_type") in ("strength", "mobility", "yoga")
            )
            if has_exercises:
                log.info("Exercise enrichment succeeded")
                return enriched
            log.warning("Exercise enrichment returned no exercises")
        else:
            log.warning("Exercise enrichment failed to parse plan")
    except Exception:
        log.exception("Exercise enrichment call failed")
    return None


def _get_relevant_claims(
    db: HistoryDB, profile: dict | None, facts: list[dict]
) -> str | None:
    """Derive relevant research categories from athlete profile/facts and query claims.

    Returns a formatted section string, or None if no claims found.
    """
    from pace_ai.resources.claim_store import query_claims

    categories: set[str] = set()

    # Always include these for any runner
    categories.add("foam_rolling_mobility")
    categories.add("recovery_modalities")
    categories.add("easy_recovery_running")
    categories.add("strength_training_runners")
    categories.add("warmup_cooldown")

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


def _format_plan_table(plan: dict) -> str:
    """Build a markdown table of a weekly plan for display in chat."""
    table = f"\n\n**Proposed plan — week of {plan.get('week_starting', '?')}:**\n\n"
    table += (
        "| Date | Session | Type | Duration |\n|------|---------|------|----------|\n"
    )
    for s in plan.get("sessions", []):
        table += (
            f"| {s.get('date', '')} | {s.get('name', '')} "
            f"| {s.get('workout_type', '')} | {s.get('duration_minutes', '')}min |\n"
        )
    table += "\nSuggest changes, or click **Schedule** when ready."
    return table


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


STATUS_SYSTEM_PROMPT = """\
You are a running coach reviewing an athlete's current status.
All paces in minutes per mile. Distances in miles.
Produce a concise status report: training load trends, recent run quality, \
recovery indicators, body composition, injury/niggle status, overall readiness.
Be specific with numbers. Keep under 500 words. Markdown format."""

PLAN_SYSTEM_PROMPT = """\
You are a running coach creating a training plan.
All paces in minutes per mile. Saturday is ALWAYS the long run day.
Coaching must cite the research evidence provided.
Every mobility/recovery session MUST include foam rolling.
Output plan as JSON (schema provided). Do NOT include exercises array.
The description field MUST contain full exercise details for strength/mobility sessions.
Include coaching rationale before the JSON."""

CHAT_SYSTEM_PROMPT = """\
You are a running coach in a conversation with your athlete.
All paces in minutes per mile. Distances in miles.
{plan_instruction}\
Keep responses concise and practical."""

PLAN_JSON_SCHEMA = """\
## Plan JSON Schema

Output the plan as a JSON block inside ```json code fences:

```json
{
  "week_starting": "YYYY-MM-DD",
  "sessions": [
    {
      "date": "YYYY-MM-DD",
      "workout_type": "easy_run|run_walk|tempo|intervals|strides|strength|mobility|yoga|cardio|hiit|walking|rest",
      "name": "Short name shown on watch",
      "duration_minutes": 30,
      "description": "Full exercise details for strength/mobility — sets, reps, duration"
    }
  ]
}
```

Do NOT include an exercises array — exercises are added automatically at scheduling time.
week_starting is the date of the FIRST session in the plan.
Include an entry for every day in the requested range (rest days use workout_type "rest").
Saturday is ALWAYS the long run day. Never schedule strength or rest on Saturday."""


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


def _default_date_range() -> tuple[str, str]:
    """Return (next_monday, next_sunday) as ISO strings."""
    from datetime import date, timedelta

    today = date.today()
    days_ahead = (7 - today.weekday()) % 7
    if days_ahead == 0:
        days_ahead = 7
    monday = today + timedelta(days=days_ahead)
    sunday = monday + timedelta(days=6)
    return monday.isoformat(), sunday.isoformat()


@app.route("/")
def index():
    store = _get_store()
    messages = store.get("messages", [])
    has_pending_plan = "pending_plan" in store

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

    # Ensure strength/mobility sessions have exercises arrays
    needs_exercises = [
        s
        for s in plan.get("sessions", [])
        if s.get("workout_type") in ("strength", "mobility", "yoga")
        and not s.get("exercises")
    ]
    if needs_exercises:
        log.info(
            "Generating exercises for %d sessions via focused prompt",
            len(needs_exercises),
        )
        enriched = _enrich_plan_with_exercises(plan)
        if enriched:
            plan = enriched

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
            exercises = s.get("exercises")
            _STRUCTURED_TYPES = {"strength", "mobility", "yoga"}
            if workout_type in _STRUCTURED_TYPES:
                from garmin_mcp.workout_builder import (
                    SPORT_TYPE_MOBILITY,
                    SPORT_TYPE_STRENGTH,
                    SPORT_TYPE_YOGA,
                    custom_workout,
                )

                _SPORT_TYPE_MAP = {
                    "strength": SPORT_TYPE_STRENGTH,
                    "mobility": SPORT_TYPE_MOBILITY,
                    "yoga": SPORT_TYPE_YOGA,
                }

                if exercises and isinstance(exercises, list):
                    # Structured exercises from JSON — reliable
                    steps = _exercises_to_steps(exercises)
                else:
                    # Fallback: parse from description text
                    steps = _description_to_steps(description, duration)
                workout_json = custom_workout(
                    name,
                    steps_json=steps,
                    description=description,
                    sport_type=_SPORT_TYPE_MAP.get(workout_type),
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
