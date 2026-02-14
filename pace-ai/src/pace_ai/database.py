"""SQLite database for goals and athlete preferences."""

from __future__ import annotations

import json
import sqlite3
import time
from typing import Any


class GoalDB:
    """CRUD operations for training goals."""

    def __init__(self, db_path: str) -> None:
        self._db_path = db_path
        self._ensure_table()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_table(self) -> None:
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS goals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    race_type TEXT NOT NULL,
                    target_time_seconds INTEGER NOT NULL,
                    race_date TEXT,
                    notes TEXT,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL
                )
            """)

    def create(self, race_type: str, target_time_seconds: int, race_date: str | None = None, notes: str | None = None) -> dict[str, Any]:
        now = time.time()
        with self._connect() as conn:
            cursor = conn.execute(
                "INSERT INTO goals (race_type, target_time_seconds, race_date, notes, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                (race_type, target_time_seconds, race_date, notes, now, now),
            )
            goal_id = cursor.lastrowid
        return self.get(goal_id)

    def get(self, goal_id: int) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM goals WHERE id = ?", (goal_id,)).fetchone()
        if row is None:
            return None
        return dict(row)

    def list_all(self) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM goals ORDER BY created_at DESC").fetchall()
        return [dict(r) for r in rows]

    def update(self, goal_id: int, **fields: Any) -> dict[str, Any] | None:
        allowed = {"race_type", "target_time_seconds", "race_date", "notes"}
        updates = {k: v for k, v in fields.items() if k in allowed and v is not None}

        if not updates:
            return self.get(goal_id)

        updates["updated_at"] = time.time()
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = [*updates.values(), goal_id]

        with self._connect() as conn:
            conn.execute(f"UPDATE goals SET {set_clause} WHERE id = ?", values)  # noqa: S608

        return self.get(goal_id)

    def delete(self, goal_id: int) -> bool:
        with self._connect() as conn:
            cursor = conn.execute("DELETE FROM goals WHERE id = ?", (goal_id,))
            return cursor.rowcount > 0
