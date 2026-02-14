# Pace-AI: Project Plan

## Overview

Two separate MCP servers, both in Python, using Streamable HTTP transport:

1. **strava-mcp** - Generic Strava data access server. Useful to anyone. Registered separately on the MCP registry.
2. **pace-ai** - Running coach intelligence layer. Coaching prompts, methodology, goals, analysis. Uses Strava data that Claude fetches via strava-mcp.

Claude orchestrates between them: pulls data from strava-mcp, reasons about it using pace-ai's coaching framework.

## Architecture

```
Claude Desktop / Claude Code
        │
        ├── Streamable HTTP ──► strava-mcp (localhost:8001)
        │                        ├── OAuth2 token management
        │                        ├── Activity tools
        │                        └── Athlete tools
        │
        └── Streamable HTTP ──► pace-ai (localhost:8002)
                                 ├── Coaching prompts
                                 ├── Methodology resources
                                 ├── Goal management tools
                                 └── Training analysis tools
```

**Security model:** Strava API credentials via environment variables (`.env`, never committed). Streamable HTTP on localhost only. OAuth tokens stored in local SQLite.

---

## Server 1: strava-mcp

A general-purpose Strava MCP server. No coaching opinions — just clean data access.

### Project Structure

```
strava-mcp/
├── pyproject.toml
├── README.md
├── .env.example                  # STRAVA_CLIENT_ID, STRAVA_CLIENT_SECRET
├── .gitignore
├── server.json                   # MCP registry manifest
├── src/
│   └── strava_mcp/
│       ├── __init__.py
│       ├── server.py             # FastMCP entry point (Streamable HTTP)
│       ├── config.py             # Settings from env vars
│       ├── auth.py               # OAuth2 flow (browser + localhost callback)
│       ├── client.py             # Strava API wrapper + token refresh
│       └── cache.py              # SQLite activity cache
└── tests/
    └── test_tools.py
```

### Tools

| Tool | Description |
|---|---|
| `authenticate` | Trigger Strava OAuth flow (opens browser, localhost callback) |
| `get_athlete` | Get authenticated athlete profile |
| `get_recent_activities(days=30)` | List recent activities with summary stats |
| `get_activity(activity_id)` | Full activity detail: splits, laps, HR, pace |
| `get_activity_streams(activity_id, stream_types)` | Time-series data (heartrate, pace, altitude, etc.) |
| `get_athlete_stats` | Year-to-date and all-time stats |
| `get_athlete_zones` | Heart rate and power zone definitions |

### Resources

| Resource | Description |
|---|---|
| `strava://athlete/profile` | Current athlete profile data |
| `strava://rate-limits` | Current Strava API rate limit status |

### Registry

- **Namespace:** `io.github.aldred-coetzee/strava-mcp`
- **PyPI package:** `strava-mcp`
- Discoverable by anyone wanting Strava data in their MCP workflow

---

## Server 2: pace-ai

The coaching intelligence layer. No direct Strava API calls — Claude fetches data from strava-mcp and feeds it into pace-ai's coaching framework.

### Project Structure

```
pace-ai/
├── pyproject.toml
├── README.md
├── .gitignore
├── server.json                   # MCP registry manifest
├── src/
│   └── pace_ai/
│       ├── __init__.py
│       ├── server.py             # FastMCP entry point (Streamable HTTP)
│       ├── config.py             # Settings
│       ├── database.py           # SQLite for goals + athlete preferences
│       ├── tools/
│       │   ├── __init__.py
│       │   ├── goals.py          # Goal CRUD tools
│       │   └── analysis.py       # Training analysis tools
│       ├── prompts/
│       │   ├── __init__.py
│       │   └── coaching.py       # Coaching prompt templates
│       └── resources/
│           ├── __init__.py
│           └── methodology.py    # Coaching methodology + principles
└── tests/
    └── test_coaching.py
```

### Tools

| Tool | Description |
|---|---|
| `set_goal(race_type, target_time, race_date, notes)` | Store a training goal |
| `get_goals()` | List current goals |
| `update_goal(goal_id, ...)` | Modify a goal |
| `delete_goal(goal_id)` | Remove a goal |
| `analyze_training_load(weekly_distances)` | Compute ACWR, monotony, strain from provided data |
| `predict_race_time(recent_race_distance, recent_race_time, target_distance)` | Riegel / VDOT prediction |
| `calculate_training_zones(threshold_pace_or_hr)` | Daniels' VDOT zones from threshold data |

### Prompts (structured coaching — the key to repeatable advice)

MCP prompts are templates that guide Claude's reasoning. They inject relevant context and frame analysis using established running science, so coaching is consistent session to session.

#### `weekly_plan`
> "Generate a training plan for the upcoming week"
- **Expects Claude to provide:** current goals, last 4 weeks of training data, recent PRs
- **Framework:** progressive overload, 80/20 polarised training, adequate recovery
- **Output structure:** day-by-day plan with session type, distance, target pace/effort, purpose

#### `run_analysis`
> "Analyze a specific run"
- **Expects Claude to provide:** activity details, splits, HR data
- **Framework:** pace consistency (coefficient of variation), HR drift, effort distribution vs targets
- **Output structure:** what went well, what to improve, how it fits the training block

#### `race_readiness`
> "Am I ready for my upcoming race?"
- **Expects Claude to provide:** goal details, training volume trend, recent performances
- **Framework:** taper timing, volume benchmarks, VDOT pace predictions, Riegel formula
- **Output structure:** readiness score, strengths, risks, recommended final-week adjustments

#### `injury_risk`
> "Assess training load for injury risk"
- **Expects Claude to provide:** weekly mileage for last 8 weeks
- **Framework:** 10% rule, acute:chronic workload ratio (0.8-1.3 optimal), monotony/strain indices
- **Output structure:** risk level, specific concerns, recommended adjustments

### Resources (coaching knowledge base)

#### `coaching://methodology`
Static reference that Claude can pull in at any time. Contains:
- **Core principles:** progressive overload, specificity, recovery, individualisation
- **Training zones:** easy, tempo, threshold, interval, repetition (Daniels' VDOT model)
- **Race predictors:** VDOT tables, Riegel formula, key workouts as race indicators
- **Weekly structure:** long run, speed work, tempo, easy days, rest day guidelines
- **Red flags:** sudden mileage jumps (>10%/week), persistent elevated resting HR, declining performance despite increased volume
- **Periodisation:** base → build → peak → taper → race → recovery

This ensures Claude gives evidence-based, structured advice — not generic platitudes.

#### `coaching://zones-explained`
Detailed explanation of each training zone with purpose, feel, and typical session formats.

---

## Build Order

### Phase 1: strava-mcp (data layer)
1. Project setup: pyproject.toml, .gitignore, .env.example
2. Strava OAuth flow (browser + localhost callback, token stored in SQLite)
3. Strava API client with token refresh
4. MCP tools: authenticate, get_athlete, get_recent_activities, get_activity, get_activity_streams, get_athlete_stats, get_athlete_zones
5. Activity cache in SQLite
6. Streamable HTTP transport on localhost
7. Test with MCP Inspector

### Phase 2: pace-ai (coaching layer)
1. Project setup
2. SQLite database for goals + preferences
3. Goal management tools
4. Analysis tools (ACWR, VDOT, training zones)
5. Coaching prompts (weekly_plan, run_analysis, race_readiness, injury_risk)
6. Methodology resources
7. Streamable HTTP transport on localhost
8. Test with MCP Inspector

### Phase 3: Integration test
1. Run both servers
2. Configure Claude Desktop / Claude Code to use both
3. End-to-end: "Analyze my last week of training and suggest next week's plan"

### Phase 4: Package & register (later)
1. PyPI packaging for both
2. MCP registry: `io.github.aldred-coetzee/strava-mcp`
3. MCP registry: `io.github.aldred-coetzee/pace-ai`

---

## Key Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Two servers | strava-mcp + pace-ai | Separation of concerns; Strava server is reusable by anyone |
| Transport | Streamable HTTP | Future-proof, flexible, supports multiple clients |
| Strava credentials | Environment variables (.env) | Simple, standard, never committed |
| Token storage | Local SQLite | Portable, no external deps |
| Activity caching | SQLite (in strava-mcp) | Respect Strava rate limits (200/15min, 2000/day) |
| Coaching consistency | MCP prompts + methodology resources | Structured frameworks = repeatable advice |
| Analysis library | Pure Python (no heavy deps) | VDOT/Riegel/ACWR are simple formulas |
| Python version | 3.10+ | MCP SDK requirement |

## What We Build This Session

Phase 1 (strava-mcp) first. Then Phase 2 (pace-ai). Both as subdirectories of this repo for now — can split to separate repos for registry publishing later.
