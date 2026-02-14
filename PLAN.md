# Pace-AI: MCP Server Plan

## Overview

A Python MCP server that connects Claude to your Strava data and provides structured coaching guidance. Runs locally via stdio transport (never exposed publicly). Designed for registration on the MCP registry.

## Architecture

```
Claude Desktop / Claude Code
        │
        │ stdio (JSON-RPC)
        │
   ┌────▼─────────────────────┐
   │   Pace-AI MCP Server     │
   │                          │
   │  Tools:                  │
   │   - Strava data access   │
   │   - Goal management      │
   │   - Training analysis    │
   │                          │
   │  Prompts:                │
   │   - Coaching templates   │
   │   - Analysis frameworks  │
   │                          │
   │  Resources:              │
   │   - Coaching methodology │
   │   - Training principles  │
   ├──────────────────────────┤
   │  Local Storage (SQLite)  │
   │   - Cached activities    │
   │   - Goals & preferences  │
   │   - Strava tokens        │
   ├──────────────────────────┤
   │  Strava API (OAuth2)     │
   └──────────────────────────┘
```

**Security model:** stdio transport only. No HTTP server runs except a one-time localhost callback during Strava OAuth. Strava tokens stored in local encrypted SQLite. Client credentials in `.env` (never committed).

## Project Structure

```
Pace-AI/
├── pyproject.toml              # Package config (for PyPI + MCP registry)
├── README.md
├── .env.example
├── .gitignore
├── src/
│   └── pace_ai/
│       ├── __init__.py
│       ├── server.py           # MCP server definition (entry point)
│       ├── config.py           # Settings from env vars
│       ├── database.py         # SQLite setup + models
│       ├── strava/
│       │   ├── __init__.py
│       │   ├── auth.py         # OAuth2 flow (local browser + localhost callback)
│       │   └── client.py       # Strava data fetching + caching
│       ├── tools/
│       │   ├── __init__.py
│       │   ├── activities.py   # Activity-related tools
│       │   ├── goals.py        # Goal management tools
│       │   └── analysis.py     # Training analysis tools
│       ├── prompts/
│       │   ├── __init__.py
│       │   └── coaching.py     # Coaching prompt templates
│       └── resources/
│           ├── __init__.py
│           └── methodology.py  # Coaching methodology resources
├── server.json                 # MCP registry manifest
└── tests/
    ├── __init__.py
    ├── test_tools.py
    └── test_coaching.py
```

## Phase 1: Core MCP Server + Strava Auth

### 1.1 Project setup
- `pyproject.toml` with `mcp[cli]`, `stravalib`, `httpx`, `sqlalchemy` dependencies
- `.gitignore`, `.env.example`
- Basic `src/pace_ai/server.py` with FastMCP instance

### 1.2 Strava OAuth
- One-time auth flow: opens browser, runs localhost:8080 callback, exchanges code
- Token storage in local SQLite (encrypted at rest using a local key)
- Auto-refresh on expiry (stravalib handles this)
- MCP tool: `strava_authenticate` - triggers the OAuth flow if not yet authenticated

### 1.3 Database
- SQLite via SQLAlchemy
- Tables: `tokens`, `activities` (cache), `goals`, `athlete_profile`
- DB file stored in `~/.pace-ai/pace_ai.db` (user's home dir, not in project)

## Phase 2: Strava Data Tools

### 2.1 Activity tools
- `get_recent_activities(days: int = 30)` - List recent runs with summary stats
- `get_activity_details(activity_id: int)` - Full detail: splits, laps, HR, pace
- `get_activity_streams(activity_id: int)` - Raw time-series (HR, pace, elevation)
- `sync_activities(days: int = 90)` - Fetch and cache activities from Strava

### 2.2 Analysis tools
- `get_training_summary(weeks: int = 4)` - Weekly volume, avg pace, distance trends
- `get_personal_records()` - Best efforts across distances (1K, 5K, 10K, HM, M)
- `get_heart_rate_zones()` - Athlete's HR zone definitions + time-in-zone trends
- `get_fitness_trend(weeks: int = 12)` - Volume and intensity progression

## Phase 3: Goals & Coaching

### 3.1 Goal tools
- `set_goal(race_type, target_time, race_date, notes)` - Store a training goal
- `get_goals()` - List current goals
- `update_goal(goal_id, ...)` - Modify a goal
- `delete_goal(goal_id)` - Remove a goal

### 3.2 Coaching prompts (MCP prompts for repeatable advice)

These are predefined prompt templates that structure how Claude reasons about coaching. They ensure advice is grounded in running science and consistent across sessions.

- **`weekly_plan`** - "Generate a training plan for the upcoming week"
  - Injects: current goals, last 4 weeks of training data, recent personal records
  - Framework: progressive overload, 80/20 polarised training, adequate recovery

- **`run_analysis`** - "Analyze my most recent run"
  - Injects: activity details, splits, HR data, comparison to recent averages
  - Framework: pace consistency, HR drift, effort distribution

- **`race_readiness`** - "Am I ready for my upcoming race?"
  - Injects: goal details, training volume trend, recent performances, time to race
  - Framework: taper timing, volume benchmarks, pace predictors (Riegel formula, VDOT)

- **`injury_risk`** - "Check my training load for injury risk"
  - Injects: weekly mileage progression, acute:chronic workload ratio
  - Framework: 10% rule, ACWR (0.8-1.3 optimal), monotony/strain indices

### 3.3 Coaching methodology resource

A static MCP resource (`coaching://methodology`) that Claude can reference. Contains:
- Core principles: progressive overload, specificity, recovery, individualisation
- Training zones: easy, tempo, threshold, interval, repetition (Daniels' model)
- Race time predictors: VDOT tables, Riegel formula
- Weekly structure guidelines: long run, speed work, easy days, rest
- Red flags: sudden mileage jumps, persistent fatigue, HR anomalies

This ensures Claude gives evidence-based advice, not generic platitudes.

## Phase 4: Packaging & Registry

### 4.1 PyPI packaging
- `pyproject.toml` with proper metadata, entry points
- Entry point: `pace-ai = pace_ai.server:main`
- Users install with: `pip install pace-ai` or `uv add pace-ai`

### 4.2 MCP registry
- `server.json` manifest with package reference to PyPI
- Namespace: `io.github.aldred-coetzee/pace-ai`
- Publish via `mcp-publisher` CLI

### 4.3 Claude Desktop config
```json
{
  "mcpServers": {
    "pace-ai": {
      "command": "uv",
      "args": ["--directory", "/path/to/Pace-AI", "run", "pace-ai"],
      "env": {
        "STRAVA_CLIENT_ID": "your_id",
        "STRAVA_CLIENT_SECRET": "your_secret"
      }
    }
  }
}
```

## What We Build Now (This Session)

Phases 1-3 above. Phase 4 (PyPI + registry) once it's working and tested.

## Key Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Transport | stdio only | Never exposes API publicly |
| Token storage | Local SQLite in ~/.pace-ai/ | Secure, portable, no external deps |
| Activity caching | SQLite | Avoid hitting Strava rate limits (200/15min, 2000/day) |
| Coaching consistency | MCP prompts + methodology resource | Structured frameworks ensure repeatable advice |
| Library | stravalib | Mature, typed, handles rate limits |
| Packaging | pyproject.toml + uv | Modern Python, easy install |
