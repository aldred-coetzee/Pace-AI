"""SQLite cache for Notion diary entries."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Any


def init_db(db_path: str) -> sqlite3.Connection:
    """Create the diary cache table if it doesn't exist."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS diary_entries (
            page_id TEXT PRIMARY KEY,
            last_edited TEXT NOT NULL,
            date TEXT NOT NULL,
            stress INTEGER,
            niggles TEXT,
            notes TEXT
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_diary_date ON diary_entries (date)
    """)
    conn.commit()
    return conn


def upsert_entry(conn: sqlite3.Connection, entry: dict[str, Any]) -> None:
    """Insert or update a diary entry."""
    conn.execute(
        """
        INSERT INTO diary_entries (page_id, last_edited, date, stress, niggles, notes)
        VALUES (:page_id, :last_edited, :date, :stress, :niggles, :notes)
        ON CONFLICT(page_id) DO UPDATE SET
            last_edited = excluded.last_edited,
            date = excluded.date,
            stress = excluded.stress,
            niggles = excluded.niggles,
            notes = excluded.notes
        """,
        entry,
    )


def upsert_entries(conn: sqlite3.Connection, entries: list[dict[str, Any]]) -> int:
    """Upsert a batch of diary entries. Returns count upserted."""
    for entry in entries:
        upsert_entry(conn, entry)
    conn.commit()
    return len(entries)


def get_recent_entries(conn: sqlite3.Connection, days: int = 28) -> list[dict[str, Any]]:
    """Get diary entries from the last N days, ordered by date descending."""
    cutoff = (datetime.now(tz=timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
    rows = conn.execute(
        "SELECT date, stress, niggles, notes FROM diary_entries WHERE date >= ? ORDER BY date DESC",
        (cutoff,),
    ).fetchall()
    return [dict(row) for row in rows]
