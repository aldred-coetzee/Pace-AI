"""HTML/CSS/JS template strings for the Pace-AI UI."""

from __future__ import annotations

HTML = """\
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="/static/favicon.ico" type="image/x-icon">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<title>Pace AI</title>
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
<style>
:root {
  color-scheme: dark;
  --bg-primary: #0A0A0A;
  --bg-secondary: #141414;
  --bg-tertiary: #1A1A1A;
  --text-primary: #ECECEC;
  --text-secondary: #888;
  --text-tertiary: #555;
  --border: #232323;
  --border-soft: #1C1C1C;
  --accent: #6E8EEF;
  --accent-hover: #8BA4F3;
  --accent-glow: rgba(110, 142, 239, 0.08);
  --success: #4ADE80;
  --warning: #FACC15;
  --danger: #F87171;
  --overlay: rgba(255, 255, 255, 0.04);
  --font: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  --mono: "SF Mono", Monaco, "Cascadia Code", "Roboto Mono", Menlo, monospace;
}
*, *::before, *::after { box-sizing: border-box; }
body { font: 14px/1.6 var(--font); letter-spacing: -0.011em; margin: 0; padding: 0;
       background: var(--bg-primary); color: var(--text-primary);
       -webkit-font-smoothing: antialiased; -moz-osx-font-smoothing: grayscale; }
a { color: var(--accent); text-decoration: none; }
a:hover { color: var(--accent-hover); }

/* ── Navbar ── */
.navbar { background: var(--bg-secondary); border-bottom: 1px solid var(--border);
          padding: 0 28px; display: flex; align-items: center; height: 44px; gap: 10px;
          position: sticky; top: 0; z-index: 100; }
.navbar-brand { font-weight: 600; font-size: 14px; color: var(--text-primary);
                letter-spacing: -0.03em; margin-right: 12px; }
.navbar-brand span { color: var(--text-secondary); font-weight: 400; }
.nav-group { display: flex; align-items: center; gap: 4px; }
.nav-spacer { flex: 1; }
.nav-sep { width: 1px; height: 16px; background: var(--border); margin: 0 6px; }

/* ── Buttons ── */
.btn { display: inline-flex; align-items: center; gap: 6px; padding: 5px 12px;
       border: 1px solid var(--border); border-radius: 4px; font: 13px/1 var(--font);
       font-weight: 500; cursor: pointer; transition: all 0.15s ease;
       background: transparent; color: var(--text-secondary); white-space: nowrap; }
.btn:hover { background: var(--overlay); border-color: var(--text-tertiary);
             color: var(--text-primary); }
.btn:disabled { opacity: 0.35; cursor: not-allowed; }
.btn-primary { background: var(--accent); border-color: var(--accent);
               color: #fff; font-weight: 500; }
.btn-primary:hover { background: var(--accent-hover); border-color: var(--accent-hover); }
.btn-danger { color: var(--text-secondary); }
.btn-danger:hover { background: rgba(248,113,113,0.08); color: var(--danger);
                    border-color: rgba(248,113,113,0.3); }
.btn-success { color: var(--text-secondary); }
.btn-success:hover { background: rgba(74,222,128,0.08); color: var(--success);
                     border-color: rgba(74,222,128,0.3); }

/* ── Layout ── */
.container { max-width: 1120px; margin: 0 auto; padding: 24px 32px 120px; }

/* ── Toolbar ── */
.toolbar { display: flex; align-items: center; gap: 8px; padding: 12px 0;
           border-bottom: 1px solid var(--border); margin-bottom: 16px; flex-wrap: wrap; }
.toolbar-group { display: flex; align-items: center; gap: 6px; }
.toolbar-sep { width: 1px; height: 20px; background: var(--border); margin: 0 4px; }
.toolbar input[type="date"] { padding: 5px 8px; font: 13px var(--font);
  background: var(--bg-tertiary); color: var(--text-primary);
  border: 1px solid var(--border); border-radius: 4px; color-scheme: dark; }
.toolbar label { font-size: 12px; color: var(--text-secondary); }
.toolbar-meta { display: flex; align-items: center; gap: 8px; margin-left: auto;
                font-size: 12px; color: var(--text-tertiary); }
.toolbar-dot { width: 3px; height: 3px; border-radius: 50%; background: var(--text-tertiary); }

/* ── Banners ── */
.banner { padding: 10px 16px; border-radius: 4px; font-size: 13px;
          margin-bottom: 12px; display: flex; align-items: center; gap: 10px;
          background: var(--overlay); border-left: 2px solid var(--border); }
.banner-info { border-left-color: var(--accent); color: #93C5FD; }
.banner-success { border-left-color: var(--success); color: #6EE7B7; }
.banner-warn { border-left-color: var(--warning); color: #FCD34D; }
.banner-crit { border-left-color: var(--danger); color: #FCA5A5; }

/* ── Session bar ── */
.session-bar { font-size: 12px; color: var(--text-tertiary); padding: 4px 0;
               display: flex; justify-content: space-between; margin-bottom: 12px; }

/* ── Messages ── */
.messages { display: flex; flex-direction: column; gap: 12px; margin-bottom: 24px; }
.msg { padding: 14px 18px; border-radius: 6px; word-wrap: break-word;
       line-height: 1.6; font-size: 14px; }
.msg.user { background: var(--bg-tertiary); border: 1px solid var(--border);
            white-space: pre-wrap; }
.msg.user .msg-label { font-size: 11px; font-weight: 500; letter-spacing: 0.04em;
                       color: var(--text-tertiary); margin-bottom: 4px; }
.msg.assistant { background: var(--bg-secondary); border: 1px solid var(--border-soft); }
.msg.assistant .msg-label { font-size: 11px; font-weight: 500; letter-spacing: 0.04em;
                            color: var(--text-secondary); margin-bottom: 4px; }
.msg.assistant table { border-collapse: collapse; margin: 12px 0; width: 100%;
                       font-size: 13px; }
.msg.assistant th, .msg.assistant td { border: 1px solid var(--border);
  padding: 8px 12px; text-align: left; }
.msg.assistant th { background: var(--bg-tertiary); font-size: 11px;
  text-transform: uppercase; letter-spacing: 0.04em; font-weight: 500;
  color: var(--text-tertiary); }
.msg.assistant td { color: var(--text-primary); }
.msg.assistant tbody tr:hover { background: var(--overlay); }
.msg.assistant blockquote { border-left: 3px solid var(--border); margin: 12px 0;
  padding: 8px 16px; color: var(--text-secondary); }
.msg.assistant code { background: var(--bg-tertiary); padding: 2px 5px;
  border-radius: 3px; font: 13px var(--mono); }
.msg.assistant pre { background: var(--bg-tertiary); border: 1px solid var(--border);
  padding: 14px; border-radius: 4px; overflow-x: auto; margin: 12px 0; }
.msg.assistant h2 { font-size: 16px; font-weight: 600; margin: 20px 0 8px;
  letter-spacing: -0.02em; }
.msg.assistant h3 { font-size: 14px; font-weight: 600; margin: 16px 0 6px;
  letter-spacing: -0.01em; }
.msg.assistant hr { border: none; border-top: 1px solid var(--border); margin: 16px 0; }
.msg.assistant ul, .msg.assistant ol { padding-left: 20px; margin: 8px 0; }
.msg.assistant li { margin: 4px 0; }
.msg.assistant strong { color: var(--text-primary); }
.msg.assistant .md-content > *:last-child { margin-bottom: 0; }
.msg.assistant p { margin: 8px 0; }
.msg.assistant .md-content > *:first-child { margin-top: 0; }

/* ── Status report ── */
.status-report { display: flex; flex-direction: column; gap: 2px; }
.status-report h2 { font-size: 11px; font-weight: 500; letter-spacing: 0.04em;
  text-transform: uppercase; color: var(--text-tertiary); margin: 0 0 8px; }
.status-section { padding: 14px 18px; border-left: 2px solid var(--border);
  background: var(--bg-tertiary); margin: 0; }
.status-section.status-ok { border-left-color: var(--success); }
.status-section.status-caution { border-left-color: var(--warning); }
.status-section.status-concern { border-left-color: var(--danger); }
.status-section.status-info { border-left-color: var(--accent); }
.status-header { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
.status-dot { width: 6px; height: 6px; border-radius: 50%; flex-shrink: 0; }
.status-ok .status-dot { background: var(--success); }
.status-caution .status-dot { background: var(--warning); }
.status-concern .status-dot { background: var(--danger); }
.status-info .status-dot { background: var(--accent); }
.status-title { font-size: 13px; font-weight: 600; color: var(--text-primary);
  letter-spacing: -0.01em; }
.status-body { font-size: 13px; line-height: 1.6; color: var(--text-secondary); }
.status-body p { margin: 4px 0; }
.status-body p:first-child { margin-top: 0; }
.status-body p:last-child { margin-bottom: 0; }
.status-body table { border-collapse: collapse; margin: 8px 0; width: 100%; font-size: 12px; }
.status-body th, .status-body td { border: 1px solid var(--border); padding: 6px 10px;
  text-align: left; }
.status-body th { background: var(--bg-secondary); font-size: 11px; font-weight: 500;
  text-transform: uppercase; letter-spacing: 0.04em; color: var(--text-tertiary); }
.status-body strong { color: var(--text-primary); }
.status-body ul, .status-body ol { padding-left: 18px; margin: 4px 0; }
.status-body li { margin: 2px 0; }
.status-verdict { padding: 14px 18px; background: var(--bg-tertiary);
  border-left: 2px solid var(--border); }
.status-verdict.status-ok { border-left-color: var(--success); }
.status-verdict.status-caution { border-left-color: var(--warning); }
.status-verdict.status-concern { border-left-color: var(--danger); }
.verdict-label { font-size: 14px; font-weight: 600; letter-spacing: -0.01em;
  margin-bottom: 6px; }
.status-ok .verdict-label { color: var(--success); }
.status-caution .verdict-label { color: var(--warning); }
.status-concern .verdict-label { color: var(--danger); }
.status-date { font-size: 12px; color: var(--text-tertiary); margin-bottom: 12px; }

/* ── Plan bar ── */
.plan-bar { padding: 12px 16px; border-radius: 4px; margin-bottom: 16px;
            display: flex; gap: 10px; align-items: center;
            background: rgba(110,142,239,0.06); border: 1px solid rgba(110,142,239,0.15); }
.plan-bar span { font-size: 13px; color: #93C5FD; flex: 1; }

/* ── Dropdown ── */
.dropdown { position: relative; }
.dropdown-menu { display: none; position: absolute; top: 100%; right: 0;
                 background: var(--bg-secondary); border: 1px solid var(--border);
                 border-radius: 4px; padding: 4px; min-width: 200px;
                 box-shadow: 0 4px 24px rgba(0,0,0,0.5); z-index: 200; }
.dropdown.open .dropdown-menu { display: block; }
.dropdown-label { font-size: 10px; text-transform: uppercase; letter-spacing: 0.5px;
                  color: var(--text-tertiary); padding: 6px 12px 2px; font-weight: 600; }
.dropdown-sep { height: 1px; background: var(--border); margin: 4px 0; }
.dropdown-item { display: block; width: 100%; padding: 8px 12px; border: none;
                 background: transparent; color: var(--text-primary);
                 font: 13px var(--font); text-align: left; cursor: pointer;
                 border-radius: 4px; }
.dropdown-item:hover:not(:disabled) { background: var(--overlay); }
.dropdown-item:disabled { opacity: 0.4; cursor: not-allowed; }

/* ── Spinner ── */
.spinner { display: none; padding: 12px 0; }
.spinner-inner { display: flex; align-items: center; gap: 10px;
                 font-size: 13px; color: var(--text-tertiary); }
.spinner-bar { width: 16px; height: 2px; background: var(--text-tertiary); border-radius: 1px;
               animation: shimmer 1.6s infinite ease-in-out; }
@keyframes shimmer { 0%, 100% { opacity: 0.2; width: 12px; }
                     50% { opacity: 0.6; width: 20px; } }

/* ── Chat input ── */
.chat-input { display: flex; gap: 8px; position: fixed; bottom: 0; left: 0; right: 0;
              padding: 16px 24px; background: var(--bg-primary);
              border-top: 1px solid var(--border); }
.chat-input-inner { max-width: 1120px; margin: 0 auto; width: 100%;
                    display: flex; gap: 8px; padding: 0 8px; }
.chat-input textarea { flex: 1; padding: 10px 14px; font: 14px/1.6 var(--font);
  background: var(--bg-secondary); color: var(--text-primary);
  border: 1px solid var(--border); border-radius: 4px; resize: none; min-height: 42px;
  max-height: 120px; transition: border-color 0.15s; }
.chat-input textarea:focus { outline: none; border-color: var(--text-tertiary); }
.chat-input textarea::placeholder { color: var(--text-tertiary); }
</style>
</head>
<body>
<nav class="navbar">
<div class="navbar-brand">Pace <span>AI</span></div>
<div class="nav-group">
<form method="POST" action="/sync" class="ctrl-form" id="sync-form">
<button type="submit" class="btn btn-success">Sync</button>
</form>
<form method="POST" action="/status" class="ctrl-form" id="status-form">
<button type="submit" class="btn">Status</button>
</form>
<div class="dropdown" id="nutrition-dropdown">
<button type="button" class="btn" onclick="this.parentElement.classList.toggle('open')">Nutrition</button>
<div class="dropdown-menu">
<form method="POST" action="/nutrition" class="ctrl-form">
<input type="hidden" name="mode" value="general">
<button type="submit" class="dropdown-item">General Advice</button>
</form>
<form method="POST" action="/nutrition" class="ctrl-form">
<input type="hidden" name="mode" value="plan">
<button type="submit" class="dropdown-item" {{ 'disabled' if not has_confirmed_plan }}>Plan-Paired</button>
</form>
<form method="POST" action="/nutrition" class="ctrl-form">
<input type="hidden" name="mode" value="race">
<button type="submit" class="dropdown-item" {{ 'disabled' if not has_race_goals }}>Race Fueling</button>
</form>
</div>
</div>
</div>
<div class="nav-spacer"></div>
<div class="nav-group">
<a href="/history" class="btn">History</a>
<div class="nav-sep"></div>
<form method="POST" action="/clear" class="ctrl-form">
<button type="submit" class="btn">Clear</button>
</form>
<form method="POST" action="/end-session" class="ctrl-form">
<button type="submit" class="btn btn-danger">End Session</button>
</form>
</div>
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
<div class="toolbar-meta">
{% if status_cached %}<span>Status cached {{ status_age }}</span><span class="toolbar-dot"></span>{% endif %}
<span>{{ message_count }} messages</span>
</div>
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
<div class="msg-label">you</div>
{{ msg.content }}
</div>
{% elif msg.get('agent') in ('status', 'nutrition', 'plan') %}
<div class="msg assistant">
<div class="msg-label">coach</div>
<div class="status-wrap">{{ msg.content | safe }}</div>
</div>
{% else %}
<div class="msg assistant">
<div class="msg-label">coach</div>
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
<div class="spinner-inner"><div class="spinner-bar"></div> <span>Thinking...</span></div>
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
// Close dropdown on outside click
document.addEventListener('click', function(e) {
    if (!e.target.closest('.dropdown')) {
        document.querySelectorAll('.dropdown.open').forEach(function(d) { d.classList.remove('open'); });
    }
});
// Show spinner for nutrition forms
document.querySelectorAll('[action="/nutrition"]').forEach(function(f) {
    f.addEventListener('submit', function() {
        document.querySelector('#spinner .spinner-inner span').textContent = 'Generating nutrition advice...';
        document.getElementById('spinner').style.display = 'block';
        disableAll();
    });
});
// Auto-grow textarea
var ta = document.querySelector('.chat-input textarea');
ta.addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = Math.min(this.scrollHeight, 120) + 'px';
});
// Enter to send, Shift+Enter for newline
ta.addEventListener('keydown', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        if (this.value.trim()) document.getElementById('chat-form').requestSubmit();
    }
});
window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
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
tr.rest td, tr.rest-row td { color: var(--text-tertiary); }
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
<div class="msg-label">you</div>
{{ msg.content }}
</div>
{% else %}
<div class="msg assistant">
<div class="msg-label">coach</div>
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
