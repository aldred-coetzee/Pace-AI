"""SQLite database for goals, history, and athlete profile."""

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

    def create(
        self,
        race_type: str,
        target_time_seconds: int,
        race_date: str | None = None,
        notes: str | None = None,
    ) -> dict[str, Any]:
        now = time.time()
        with self._connect() as conn:
            cursor = conn.execute(
                "INSERT INTO goals (race_type, target_time_seconds, race_date, notes,"
                " created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
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
            conn.execute(f"UPDATE goals SET {set_clause} WHERE id = ?", values)

        return self.get(goal_id)

    def delete(self, goal_id: int) -> bool:
        with self._connect() as conn:
            cursor = conn.execute("DELETE FROM goals WHERE id = ?", (goal_id,))
            return cursor.rowcount > 0


class HistoryDB:
    """Central history store for activities, wellness, measurements, diary, workouts, races, and profile."""

    def __init__(self, db_path: str) -> None:
        self._db_path = db_path
        self._ensure_tables()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_tables(self) -> None:
        with self._connect() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS activities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    strava_id TEXT UNIQUE NOT NULL,
                    date TEXT NOT NULL,
                    sport_type TEXT NOT NULL,
                    name TEXT,
                    distance_m REAL,
                    moving_time_s INTEGER,
                    elapsed_time_s INTEGER,
                    elevation_gain_m REAL,
                    average_hr REAL,
                    max_hr REAL,
                    average_cadence REAL,
                    average_speed_ms REAL,
                    description TEXT,
                    garmin_workout_id TEXT,
                    perceived_effort INTEGER,
                    raw JSON
                );

                CREATE TABLE IF NOT EXISTS wellness_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT UNIQUE NOT NULL,
                    body_battery_max INTEGER,
                    body_battery_min INTEGER,
                    hrv_status TEXT,
                    hrv_value REAL,
                    sleep_score INTEGER,
                    sleep_duration_s INTEGER,
                    sleep_deep_s INTEGER,
                    sleep_rem_s INTEGER,
                    stress_avg INTEGER,
                    stress_max INTEGER,
                    training_readiness INTEGER,
                    resting_hr INTEGER,
                    respiration_avg REAL,
                    raw JSON
                );

                CREATE TABLE IF NOT EXISTS body_measurements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    weight_kg REAL,
                    bmi REAL,
                    body_fat_pct REAL,
                    muscle_mass_kg REAL,
                    bone_mass_kg REAL,
                    water_pct REAL,
                    systolic_bp INTEGER,
                    diastolic_bp INTEGER,
                    raw JSON,
                    UNIQUE(date, weight_kg)
                );

                CREATE TABLE IF NOT EXISTS diary_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT UNIQUE NOT NULL,
                    stress_1_5 INTEGER,
                    niggles TEXT,
                    notes TEXT
                );

                CREATE TABLE IF NOT EXISTS scheduled_workouts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    garmin_workout_id TEXT UNIQUE NOT NULL,
                    sport_type TEXT NOT NULL,
                    scheduled_date TEXT,
                    workout_name TEXT,
                    workout_detail TEXT,
                    created_at TEXT,
                    completed INTEGER DEFAULT 0,
                    strava_activity_id TEXT,
                    skipped_reason TEXT
                );

                CREATE TABLE IF NOT EXISTS race_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    distance_m REAL NOT NULL,
                    distance_label TEXT,
                    time_s INTEGER NOT NULL,
                    event_name TEXT,
                    course_type TEXT,
                    conditions TEXT,
                    vdot REAL,
                    source TEXT,
                    pb INTEGER DEFAULT 0,
                    UNIQUE(date, distance_m, time_s)
                );

                CREATE TABLE IF NOT EXISTS athlete_profile (
                    id INTEGER PRIMARY KEY DEFAULT 1,
                    updated_at TEXT NOT NULL,
                    estimated_vdot REAL,
                    vdot_peak REAL,
                    vdot_peak_date TEXT,
                    vdot_current REAL,
                    typical_weekly_km REAL,
                    typical_long_run_km REAL,
                    typical_easy_pace_min_per_km REAL,
                    max_weekly_km_ever REAL,
                    current_weekly_km REAL,
                    training_age_years REAL,
                    weight_kg_current REAL,
                    weight_kg_trend TEXT,
                    resting_hr_baseline REAL,
                    hrv_baseline REAL,
                    date_of_birth TEXT,
                    gender TEXT,
                    experience_level TEXT,
                    injury_history TEXT,
                    preferred_long_run_day TEXT,
                    available_days_per_week INTEGER,
                    notes TEXT
                );

                CREATE TABLE IF NOT EXISTS sync_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT NOT NULL,
                    synced_at TEXT NOT NULL,
                    records_added INTEGER,
                    earliest_date TEXT,
                    latest_date TEXT,
                    status TEXT,
                    error TEXT
                );

                CREATE TABLE IF NOT EXISTS coaching_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    summary TEXT NOT NULL,
                    prescriptions TEXT,
                    workout_ids TEXT,
                    acwr REAL,
                    weekly_km REAL,
                    body_battery INTEGER,
                    stress_level INTEGER,
                    notion_stress INTEGER,
                    notion_niggles TEXT,
                    follow_up TEXT
                );

                CREATE TABLE IF NOT EXISTS coaching_context (
                    id INTEGER PRIMARY KEY DEFAULT 1,
                    updated_at TIMESTAMP NOT NULL,
                    content TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS athlete_facts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NOT NULL,
                    category TEXT NOT NULL,
                    fact TEXT NOT NULL,
                    active INTEGER DEFAULT 1,
                    source TEXT
                );
            """)

    # ── Activities ─────────────────────────────────────────────────────

    def upsert_activities(self, activities: list[dict[str, Any]]) -> int:
        """Insert or update activities by strava_id. Returns count of rows affected."""
        count = 0
        with self._connect() as conn:
            for a in activities:
                conn.execute(
                    """INSERT INTO activities
                       (strava_id, date, sport_type, name, distance_m, moving_time_s,
                        elapsed_time_s, elevation_gain_m, average_hr, max_hr,
                        average_cadence, average_speed_ms, description, garmin_workout_id,
                        perceived_effort, raw)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                       ON CONFLICT(strava_id) DO UPDATE SET
                        date=excluded.date, sport_type=excluded.sport_type, name=excluded.name,
                        distance_m=excluded.distance_m, moving_time_s=excluded.moving_time_s,
                        elapsed_time_s=excluded.elapsed_time_s, elevation_gain_m=excluded.elevation_gain_m,
                        average_hr=excluded.average_hr, max_hr=excluded.max_hr,
                        average_cadence=excluded.average_cadence, average_speed_ms=excluded.average_speed_ms,
                        description=excluded.description, garmin_workout_id=excluded.garmin_workout_id,
                        perceived_effort=excluded.perceived_effort, raw=excluded.raw
                    """,
                    (
                        str(a["strava_id"]),
                        a["date"],
                        a["sport_type"],
                        a.get("name"),
                        a.get("distance_m"),
                        a.get("moving_time_s"),
                        a.get("elapsed_time_s"),
                        a.get("elevation_gain_m"),
                        a.get("average_hr"),
                        a.get("max_hr"),
                        a.get("average_cadence"),
                        a.get("average_speed_ms"),
                        a.get("description"),
                        a.get("garmin_workout_id"),
                        a.get("perceived_effort"),
                        json.dumps(a.get("raw")) if a.get("raw") else None,
                    ),
                )
                count += 1
        return count

    def get_activities(
        self,
        days: int | None = None,
        sport_type: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Query activities with optional filters."""
        clauses: list[str] = []
        params: list[Any] = []
        if days is not None:
            clauses.append("date >= date('now', ?)")
            params.append(f"-{days} days")
        if sport_type is not None:
            clauses.append("LOWER(sport_type) LIKE ?")
            params.append(f"%{sport_type.lower()}%")
        where = "WHERE " + " AND ".join(clauses) if clauses else ""
        params.append(limit)
        with self._connect() as conn:
            rows = conn.execute(
                f"SELECT * FROM activities {where} ORDER BY date DESC LIMIT ?",
                params,
            ).fetchall()
        return [dict(r) for r in rows]

    def get_weekly_distances(
        self,
        weeks: int = 12,
        sport_type: str = "run",
    ) -> list[dict[str, Any]]:
        """Return weekly distance totals, oldest first."""
        with self._connect() as conn:
            rows = conn.execute(
                """SELECT
                     strftime('%Y-W%W', date) AS week,
                     MIN(date) AS week_start,
                     SUM(distance_m) / 1000.0 AS distance_km,
                     COUNT(*) AS activity_count
                   FROM activities
                   WHERE LOWER(sport_type) LIKE ?
                     AND date >= date('now', ?)
                   GROUP BY week
                   ORDER BY week ASC
                """,
                (f"%{sport_type.lower()}%", f"-{weeks * 7} days"),
            ).fetchall()
        return [dict(r) for r in rows]

    # ── Wellness ───────────────────────────────────────────────────────

    def upsert_wellness(self, snapshots: list[dict[str, Any]]) -> int:
        """Insert or update wellness snapshots by date. Returns count."""
        count = 0
        with self._connect() as conn:
            for s in snapshots:
                conn.execute(
                    """INSERT INTO wellness_snapshots
                       (date, body_battery_max, body_battery_min, hrv_status, hrv_value,
                        sleep_score, sleep_duration_s, sleep_deep_s, sleep_rem_s,
                        stress_avg, stress_max, training_readiness, resting_hr,
                        respiration_avg, raw)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                       ON CONFLICT(date) DO UPDATE SET
                        body_battery_max=excluded.body_battery_max, body_battery_min=excluded.body_battery_min,
                        hrv_status=excluded.hrv_status, hrv_value=excluded.hrv_value,
                        sleep_score=excluded.sleep_score, sleep_duration_s=excluded.sleep_duration_s,
                        sleep_deep_s=excluded.sleep_deep_s, sleep_rem_s=excluded.sleep_rem_s,
                        stress_avg=excluded.stress_avg, stress_max=excluded.stress_max,
                        training_readiness=excluded.training_readiness, resting_hr=excluded.resting_hr,
                        respiration_avg=excluded.respiration_avg, raw=excluded.raw
                    """,
                    (
                        s["date"],
                        s.get("body_battery_max"),
                        s.get("body_battery_min"),
                        s.get("hrv_status"),
                        s.get("hrv_value"),
                        s.get("sleep_score"),
                        s.get("sleep_duration_s"),
                        s.get("sleep_deep_s"),
                        s.get("sleep_rem_s"),
                        s.get("stress_avg"),
                        s.get("stress_max"),
                        s.get("training_readiness"),
                        s.get("resting_hr"),
                        s.get("respiration_avg"),
                        json.dumps(s.get("raw")) if s.get("raw") else None,
                    ),
                )
                count += 1
        return count

    def get_wellness(self, days: int = 14) -> list[dict[str, Any]]:
        """Query recent wellness snapshots."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM wellness_snapshots WHERE date >= date('now', ?) ORDER BY date DESC",
                (f"-{days} days",),
            ).fetchall()
        return [dict(r) for r in rows]

    # ── Body Measurements ──────────────────────────────────────────────

    def upsert_body_measurements(self, measurements: list[dict[str, Any]]) -> int:
        """Insert or update body measurements. Returns count."""
        count = 0
        with self._connect() as conn:
            for m in measurements:
                conn.execute(
                    """INSERT INTO body_measurements
                       (date, weight_kg, bmi, body_fat_pct, muscle_mass_kg,
                        bone_mass_kg, water_pct, systolic_bp, diastolic_bp, raw)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                       ON CONFLICT(date, weight_kg) DO UPDATE SET
                        bmi=excluded.bmi, body_fat_pct=excluded.body_fat_pct,
                        muscle_mass_kg=excluded.muscle_mass_kg, bone_mass_kg=excluded.bone_mass_kg,
                        water_pct=excluded.water_pct, systolic_bp=excluded.systolic_bp,
                        diastolic_bp=excluded.diastolic_bp, raw=excluded.raw
                    """,
                    (
                        m["date"],
                        m.get("weight_kg"),
                        m.get("bmi"),
                        m.get("body_fat_pct"),
                        m.get("muscle_mass_kg"),
                        m.get("bone_mass_kg"),
                        m.get("water_pct"),
                        m.get("systolic_bp"),
                        m.get("diastolic_bp"),
                        json.dumps(m.get("raw")) if m.get("raw") else None,
                    ),
                )
                count += 1
        return count

    def get_body_measurements(self, days: int = 90) -> list[dict[str, Any]]:
        """Query recent body measurements."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM body_measurements WHERE date >= date('now', ?) ORDER BY date DESC",
                (f"-{days} days",),
            ).fetchall()
        return [dict(r) for r in rows]

    # ── Diary Entries ──────────────────────────────────────────────────

    def upsert_diary_entries(self, entries: list[dict[str, Any]]) -> int:
        """Insert or update diary entries by date. Returns count."""
        count = 0
        with self._connect() as conn:
            for e in entries:
                conn.execute(
                    """INSERT INTO diary_entries (date, stress_1_5, niggles, notes)
                       VALUES (?, ?, ?, ?)
                       ON CONFLICT(date) DO UPDATE SET
                        stress_1_5=excluded.stress_1_5, niggles=excluded.niggles, notes=excluded.notes
                    """,
                    (e["date"], e.get("stress_1_5"), e.get("niggles"), e.get("notes")),
                )
                count += 1
        return count

    def get_diary_entries(self, days: int = 28) -> list[dict[str, Any]]:
        """Query recent diary entries."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM diary_entries WHERE date >= date('now', ?) ORDER BY date DESC",
                (f"-{days} days",),
            ).fetchall()
        return [dict(r) for r in rows]

    # ── Scheduled Workouts ─────────────────────────────────────────────

    def upsert_scheduled_workouts(self, workouts: list[dict[str, Any]]) -> int:
        """Insert or update scheduled workouts. Returns count."""
        count = 0
        with self._connect() as conn:
            for w in workouts:
                conn.execute(
                    """INSERT INTO scheduled_workouts
                       (garmin_workout_id, sport_type, scheduled_date, workout_name,
                        workout_detail, created_at, completed, strava_activity_id, skipped_reason)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                       ON CONFLICT(garmin_workout_id) DO UPDATE SET
                        sport_type=excluded.sport_type, scheduled_date=excluded.scheduled_date,
                        workout_name=excluded.workout_name, workout_detail=excluded.workout_detail,
                        completed=excluded.completed, strava_activity_id=excluded.strava_activity_id,
                        skipped_reason=excluded.skipped_reason
                    """,
                    (
                        str(w["garmin_workout_id"]),
                        w["sport_type"],
                        w.get("scheduled_date"),
                        w.get("workout_name"),
                        json.dumps(w.get("workout_detail")) if w.get("workout_detail") else None,
                        w.get("created_at"),
                        w.get("completed", 0),
                        w.get("strava_activity_id"),
                        w.get("skipped_reason"),
                    ),
                )
                count += 1
        return count

    def get_scheduled_workouts(self, days: int = 28) -> list[dict[str, Any]]:
        """Query recent scheduled workouts."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM scheduled_workouts WHERE scheduled_date >= date('now', ?) ORDER BY scheduled_date DESC",
                (f"-{days} days",),
            ).fetchall()
        return [dict(r) for r in rows]

    # ── Race Results ───────────────────────────────────────────────────

    def upsert_race_result(self, result: dict[str, Any]) -> dict[str, Any]:
        """Insert or update a race result. Returns the stored row."""
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO race_results
                   (date, distance_m, distance_label, time_s, event_name,
                    course_type, conditions, vdot, source, pb)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(date, distance_m, time_s) DO UPDATE SET
                    distance_label=excluded.distance_label, event_name=excluded.event_name,
                    course_type=excluded.course_type, conditions=excluded.conditions,
                    vdot=excluded.vdot, source=excluded.source, pb=excluded.pb
                """,
                (
                    result["date"],
                    result["distance_m"],
                    result.get("distance_label"),
                    result["time_s"],
                    result.get("event_name"),
                    result.get("course_type"),
                    result.get("conditions"),
                    result.get("vdot"),
                    result.get("source"),
                    result.get("pb", 0),
                ),
            )
            row = conn.execute(
                "SELECT * FROM race_results WHERE date = ? AND distance_m = ? AND time_s = ?",
                (result["date"], result["distance_m"], result["time_s"]),
            ).fetchone()
        return dict(row)

    def get_race_results(self, limit: int = 10) -> list[dict[str, Any]]:
        """Query race results ordered by date desc."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM race_results ORDER BY date DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(r) for r in rows]

    def get_pbs(self) -> list[dict[str, Any]]:
        """Return best time per distance label."""
        with self._connect() as conn:
            rows = conn.execute(
                """SELECT distance_label, MIN(time_s) AS best_time_s, date, event_name, vdot
                   FROM race_results
                   WHERE distance_label IS NOT NULL
                   GROUP BY distance_label
                   ORDER BY distance_m ASC
                """,
            ).fetchall()
        return [dict(r) for r in rows]

    def mark_pbs(self) -> None:
        """Recalculate PB flags across all race results."""
        with self._connect() as conn:
            conn.execute("UPDATE race_results SET pb = 0")
            conn.execute(
                """UPDATE race_results SET pb = 1
                   WHERE id IN (
                     SELECT id FROM (
                       SELECT id, ROW_NUMBER() OVER (
                         PARTITION BY distance_label ORDER BY time_s ASC
                       ) AS rn
                       FROM race_results
                       WHERE distance_label IS NOT NULL
                     ) WHERE rn = 1
                   )
                """,
            )

    # ── Athlete Profile ────────────────────────────────────────────────

    def get_athlete_profile(self) -> dict[str, Any] | None:
        """Return the singleton athlete profile, or None if not yet created."""
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM athlete_profile WHERE id = 1").fetchone()
        return dict(row) if row else None

    def upsert_athlete_profile(self, fields: dict[str, Any]) -> dict[str, Any]:
        """Create or update the athlete profile (always id=1)."""
        fields["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ")
        existing = self.get_athlete_profile()
        if existing is None:
            cols = ["id", *list(fields.keys())]
            placeholders = ", ".join("?" for _ in cols)
            vals = [1, *fields.values()]
            with self._connect() as conn:
                conn.execute(
                    f"INSERT INTO athlete_profile ({', '.join(cols)}) VALUES ({placeholders})",
                    vals,
                )
        else:
            set_clause = ", ".join(f"{k} = ?" for k in fields)
            vals = [*fields.values(), 1]
            with self._connect() as conn:
                conn.execute(f"UPDATE athlete_profile SET {set_clause} WHERE id = ?", vals)
        return self.get_athlete_profile()

    # ── Sync Log ───────────────────────────────────────────────────────

    def log_sync(
        self,
        source: str,
        records_added: int,
        status: str,
        earliest_date: str | None = None,
        latest_date: str | None = None,
        error: str | None = None,
    ) -> None:
        """Record a sync event."""
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO sync_log (source, synced_at, records_added, earliest_date, latest_date, status, error)
                   VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    source,
                    time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    records_added,
                    earliest_date,
                    latest_date,
                    status,
                    error,
                ),
            )

    def get_sync_status(self) -> list[dict[str, Any]]:
        """Return most recent sync per source."""
        with self._connect() as conn:
            rows = conn.execute(
                """SELECT source, synced_at, records_added, earliest_date, latest_date, status, error
                   FROM sync_log
                   WHERE id IN (
                     SELECT MAX(id) FROM sync_log GROUP BY source
                   )
                   ORDER BY source
                """,
            ).fetchall()
        return [dict(r) for r in rows]

    # ── Coaching Log ─────────────────────────────────────────────────

    def append_coaching_log(self, entry: dict[str, Any]) -> dict[str, Any]:
        """Append a coaching log entry. Returns the new entry with id and created_at."""
        prescriptions = json.dumps(entry.get("prescriptions")) if entry.get("prescriptions") else None
        workout_ids = json.dumps(entry.get("workout_ids")) if entry.get("workout_ids") else None
        with self._connect() as conn:
            cur = conn.execute(
                """INSERT INTO coaching_log
                   (summary, prescriptions, workout_ids, acwr, weekly_km,
                    body_battery, stress_level, notion_stress, notion_niggles, follow_up)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    entry["summary"],
                    prescriptions,
                    workout_ids,
                    entry.get("acwr"),
                    entry.get("weekly_km"),
                    entry.get("body_battery"),
                    entry.get("stress_level"),
                    entry.get("notion_stress"),
                    entry.get("notion_niggles"),
                    entry.get("follow_up"),
                ),
            )
            row = conn.execute("SELECT * FROM coaching_log WHERE id = ?", (cur.lastrowid,)).fetchone()
        return dict(row)

    def get_recent_coaching_log(self, limit: int = 5) -> list[dict[str, Any]]:
        """Return last N coaching log entries ordered by date desc."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM coaching_log ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(r) for r in rows]

    def search_coaching_log(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        """Search coaching log by text match across summary and prescriptions."""
        pattern = f"%{query}%"
        with self._connect() as conn:
            rows = conn.execute(
                """SELECT * FROM coaching_log
                   WHERE summary LIKE ? OR prescriptions LIKE ?
                   ORDER BY id DESC LIMIT ?""",
                (pattern, pattern, limit),
            ).fetchall()
        return [dict(r) for r in rows]

    # ── Coaching Context ─────────────────────────────────────────────

    def get_coaching_context(self) -> dict[str, Any] | None:
        """Return current coaching context, or None if not yet set."""
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM coaching_context WHERE id = 1").fetchone()
        return dict(row) if row else None

    def update_coaching_context(self, content: str) -> dict[str, Any]:
        """Rewrite the single coaching context row. Returns the updated row."""
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ")
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO coaching_context (id, updated_at, content)
                   VALUES (1, ?, ?)
                   ON CONFLICT(id) DO UPDATE SET updated_at=excluded.updated_at, content=excluded.content""",
                (now, content),
            )
            row = conn.execute("SELECT * FROM coaching_context WHERE id = 1").fetchone()
        return dict(row)

    # ── Athlete Facts ────────────────────────────────────────────────

    def add_athlete_fact(self, category: str, fact: str, source: str | None = None) -> dict[str, Any]:
        """Add a permanent athlete fact. Returns the new fact row."""
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ")
        with self._connect() as conn:
            cur = conn.execute(
                """INSERT INTO athlete_facts (updated_at, category, fact, source)
                   VALUES (?, ?, ?, ?)""",
                (now, category, fact, source),
            )
            row = conn.execute("SELECT * FROM athlete_facts WHERE id = ?", (cur.lastrowid,)).fetchone()
        return dict(row)

    def get_athlete_facts(self, category: str | None = None) -> list[dict[str, Any]]:
        """Return all active athlete facts, optionally filtered by category."""
        with self._connect() as conn:
            if category:
                rows = conn.execute(
                    "SELECT * FROM athlete_facts WHERE active = 1 AND category = ? ORDER BY category, created_at",
                    (category,),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM athlete_facts WHERE active = 1 ORDER BY category, created_at",
                ).fetchall()
        return [dict(r) for r in rows]

    def update_athlete_fact(self, fact_id: int, fact: str) -> dict[str, Any] | None:
        """Update an athlete fact's text. Returns updated row or None if not found."""
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ")
        with self._connect() as conn:
            conn.execute(
                "UPDATE athlete_facts SET fact = ?, updated_at = ? WHERE id = ?",
                (fact, now, fact_id),
            )
            row = conn.execute("SELECT * FROM athlete_facts WHERE id = ?", (fact_id,)).fetchone()
        return dict(row) if row else None

    def deactivate_athlete_fact(self, fact_id: int) -> dict[str, Any] | None:
        """Mark a fact as inactive (historical). Returns updated row or None."""
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ")
        with self._connect() as conn:
            conn.execute(
                "UPDATE athlete_facts SET active = 0, updated_at = ? WHERE id = ?",
                (now, fact_id),
            )
            row = conn.execute("SELECT * FROM athlete_facts WHERE id = ?", (fact_id,)).fetchone()
        return dict(row) if row else None
