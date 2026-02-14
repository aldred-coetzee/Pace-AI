"""SQLite-based activity cache to respect Strava rate limits."""

from __future__ import annotations

import json
import sqlite3
import time
from typing import Any


class ActivityCache:
    """Cache Strava activity data in SQLite."""

    DEFAULT_TTL = 3600  # 1 hour

    def __init__(self, db_path: str, ttl: int = DEFAULT_TTL) -> None:
        self._db_path = db_path
        self._ttl = ttl
        self._ensure_table()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self._db_path)

    def _ensure_table(self) -> None:
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS activity_cache (
                    cache_key TEXT PRIMARY KEY,
                    data TEXT NOT NULL,
                    cached_at REAL NOT NULL
                )
            """)

    def get(self, key: str) -> Any | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT data, cached_at FROM activity_cache WHERE cache_key = ?",
                (key,),
            ).fetchone()

        if row is None:
            return None

        cached_at = row[1]
        if time.time() - cached_at > self._ttl:
            self.delete(key)
            return None

        return json.loads(row[0])

    def set(self, key: str, data: Any) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO activity_cache (cache_key, data, cached_at) VALUES (?, ?, ?)",
                (key, json.dumps(data), time.time()),
            )

    def delete(self, key: str) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM activity_cache WHERE cache_key = ?", (key,))

    def clear(self) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM activity_cache")

    def clear_expired(self) -> int:
        cutoff = time.time() - self._ttl
        with self._connect() as conn:
            cursor = conn.execute("DELETE FROM activity_cache WHERE cached_at < ?", (cutoff,))
            return cursor.rowcount
