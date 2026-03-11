"""Minimal Flask chat UI for Pace-AI — step 1: prove the plumbing works."""

from __future__ import annotations

import subprocess
from pathlib import Path

from flask import Flask, Response, render_template_string, request, session

app = Flask(__name__)
app.secret_key = "pace-ai-dev-key"

PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)

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
form { display: flex; gap: 8px; }
textarea { flex: 1; padding: 8px; font-family: monospace; font-size: 14px; background: #222; color: #e0e0e0; border: 1px solid #444; border-radius: 4px; resize: vertical; min-height: 60px; }
button { padding: 8px 20px; background: #4a9eff; color: #fff; border: none; border-radius: 4px; cursor: pointer; font-family: monospace; }
button:hover { background: #3a8eef; }
.spinner { display: none; color: #888; margin: 10px 0; }
</style>
</head>
<body>
<h1>Pace-AI Chat (dev)</h1>
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
    document.querySelector('button').disabled = true;
});
</script>
</body>
</html>
"""


@app.route("/")
def index():
    messages = session.get("messages", [])
    return render_template_string(HTML, messages=messages)


@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.form.get("message", "").strip()
    if not user_message:
        return Response(status=302, headers={"Location": "/"})

    messages = session.get("messages", [])
    messages.append({"role": "user", "content": user_message})

    try:
        result = subprocess.run(
            CLAUDE_CMD,
            input=user_message,
            capture_output=True,
            text=True,
            timeout=120,
            cwd=PROJECT_ROOT,
        )
        reply = result.stdout.strip() or result.stderr.strip() or "(no response)"
    except subprocess.TimeoutExpired:
        reply = "(timeout — Claude took too long)"
    except Exception as e:
        reply = f"(error: {e})"

    messages.append({"role": "assistant", "content": reply})
    session["messages"] = messages

    return Response(status=302, headers={"Location": "/"})


@app.route("/clear", methods=["POST"])
def clear():
    session.pop("messages", None)
    return Response(status=302, headers={"Location": "/"})


if __name__ == "__main__":
    app.run(debug=True, port=5050)
