"""Server-side session store — persisted to SQLite so sessions survive restarts."""

from __future__ import annotations

import json
import uuid

from flask import session

from ui.config import _SESSION_DB


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
