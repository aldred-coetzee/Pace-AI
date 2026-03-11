# Sync Architecture

## Overview

`sync_all` is a single MCP tool on pace-ai that performs incremental sync from all 5 data sources into the central `pace_ai.db` history store. Call it at the start of each coaching session.

```
claude -p "call sync_all" --allowedTools "mcp__pace-ai__sync_all"
```

## Sources and Incremental Strategy

Each source uses `synced_at` (the exact UTC timestamp of the last successful sync) to determine what to fetch. All writes use upsert (INSERT OR REPLACE) so duplicates are harmless.

### 1. Strava (activities, race detection)

| Detail | Value |
|--------|-------|
| Incremental method | API-level: `get_all_activities(after=<synced_at epoch>)` |
| Pagination | Automatic, 200/page |
| Race detection | `workout_type == 1` or name pattern match (parkrun, marathon, etc.) |
| VDOT | Calculated for every detected race using Daniels formula |
| PBs | Recalculated per distance after each sync |

### 2. Garmin Wellness (body battery, stress, sleep, resting HR)

| Detail | Value |
|--------|-------|
| Incremental method | Day-by-day API calls from `synced_at` date |
| Always re-syncs | Yesterday + today (see data availability below) |
| Metrics fetched | body_battery, sleep, stress, resting_hr |
| Per-metric failure | Caught individually; other metrics still sync for that day |

#### Why yesterday is always re-synced

Garmin wellness metrics have different availability windows:

| Metric | When available | Source |
|--------|---------------|--------|
| Body battery | Intraday | Continuous HRV-based calculation, partial data up to last watch sync |
| Stress | Intraday | All-day stress sampling during inactivity |
| Sleep | After morning sync | Processed after wake detection; may be re-evaluated later in the day |
| Resting HR | After morning sync | Lowest 30-min average from overnight — requires sleep data |
| HRV | After morning sync | First 5 hours of sleep (FR245 does not support this) |

If `sync_all` runs in the afternoon, today's sleep/resting HR should be available. But if the previous sync ran *before* the morning watch sync, yesterday's sleep and resting HR would have been null. Re-syncing yesterday ensures those values get backfilled.

### 3. Garmin Workouts

| Detail | Value |
|--------|-------|
| Incremental method | Client-side filter: `updatedDate > synced_at` |
| API limitation | `get_workouts(start, limit)` has no date parameter — fetches all, filters locally |
| Auto-matching | Unmatched workouts are matched to activities by date + sport type |

### 4. Withings (weight, body composition, blood pressure)

| Detail | Value |
|--------|-------|
| Incremental method | API-level: `get_measurements(startdate=<synced_at epoch>, enddate=now)` |
| Date handling | Raw measurements use Unix timestamps; converted to YYYY-MM-DD during sync |
| Field mapping | Accepts both `systolic_mmhg`/`diastolic_mmhg` and `systolic_bp`/`diastolic_bp` |

### 5. Notion (running diary)

| Detail | Value |
|--------|-------|
| Incremental method | Client-side filter: `last_edited_time > synced_at` |
| API limitation | `fetch_all_entries()` paginates through all pages — no date filter in Notion API |
| Fields synced | date, stress (1-5), niggles, notes |

## Error Handling

Each source is wrapped in its own try/except. If one source fails, the others continue. The return value reports both results and errors:

```json
{
  "results": {
    "strava": {"source": "strava", "activities_synced": 1, "races_detected": 0},
    "garmin_wellness": {"source": "garmin_wellness", "records_synced": 2},
    "garmin_workouts": {"source": "garmin_workouts", "records_synced": 0, "message": "up to date"},
    "withings": {"source": "withings", "records_synced": 0},
    "notion": {"source": "notion", "records_synced": 0}
  },
  "sources_synced": 5,
  "sources_failed": 0
}
```

Failed sources are logged to `sync_log` with `status='error'` and the error message.

## Infrastructure

### Python Environment

pace-ai's venv (`pace-ai/.venv/`) has all 5 server packages installed as editable dependencies. This allows `sync_all` to import the client libraries directly rather than making HTTP calls between MCP servers.

```
pace-ai/.venv/
  ├── pace-ai (editable)
  ├── strava-mcp (editable)
  ├── garmin-mcp (editable)
  ├── withings-mcp (editable)
  └── notion-mcp (editable)
```

Each other MCP server still has its own independent venv for running as a standalone server.

### Database Path

`.mcp.json` sets pace-ai's CWD to the project root (`/home/aldred/projects/Pace-AI/`) so `pace_ai.db` resolves correctly. The DB path defaults to the relative `pace_ai.db` via the `PACE_AI_DB` env var.

### Sync Log

Every sync (success or failure) is recorded in the `sync_log` table:

```sql
CREATE TABLE sync_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,        -- strava, garmin_wellness, garmin_workouts, withings, notion
    synced_at TEXT NOT NULL,     -- UTC timestamp: 2026-03-11T17:52:59Z
    records_added INTEGER,      -- upsert count (may include unchanged records)
    earliest_date TEXT,          -- earliest date in synced batch
    latest_date TEXT,            -- latest date in synced batch
    status TEXT,                -- success or error
    error TEXT                  -- error message if failed
);
```

`synced_at` is the authoritative timestamp for incremental sync — not `latest_date`.
