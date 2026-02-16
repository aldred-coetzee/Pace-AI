# Pace-AI

AI running coach powered by MCP — connects Claude to your Strava data for personalized training analysis, race predictions, and evidence-based coaching.

Two MCP servers in one monorepo. Claude orchestrates between them: pulls your training data from Strava, then reasons about it using sports-science coaching methodology (VDOT, ACWR, Daniels' zones, periodization).

```
┌───────────────────────────────────────────────────────┐
│                    Claude (LLM)                       │
│         Orchestrates data + coaching logic            │
└──────────┬──────────────────────────┬─────────────────┘
           │                          │
     MCP tools/prompts          MCP tools/prompts
           │                          │
┌──────────▼──────────┐  ┌────────────▼─────────────────┐
│     strava-mcp      │  │         pace-ai              │
│   localhost:8001    │  │      localhost:8002          │
│                     │  │                              │
│ • OAuth + tokens    │  │ • VDOT / ACWR / zones        │
│ • Activities        │  │ • Goal tracking              │
│ • Streams (HR, GPS) │  │ • Coaching prompts           │
│ • Athlete stats     │  │ • Methodology knowledge base │
└──────────┬──────────┘  └────────────┬─────────────────┘
           │                          │
     Strava API                  SQLite (goals)
```

## Quick Start

### 1. Create a Strava API App

Go to [strava.com/settings/api](https://www.strava.com/settings/api) and create an application:
- **Authorization Callback Domain**: `localhost`
- Note your **Client ID** and **Client Secret**

### 2. Install

```bash
git clone https://github.com/aldred-coetzee/Pace-AI.git
cd Pace-AI
pip install -e ./strava-mcp -e ./pace-ai
```

### 3. Configure

```bash
cp strava-mcp/.env.example strava-mcp/.env
# Edit strava-mcp/.env — add your STRAVA_CLIENT_ID and STRAVA_CLIENT_SECRET
```

pace-ai needs no configuration (all settings have defaults).

### 4. Add to Claude

**Claude Desktop** — edit `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "strava-mcp": {
      "command": "strava-mcp",
      "type": "streamableHttp",
      "url": "http://127.0.0.1:8001/mcp"
    },
    "pace-ai": {
      "command": "pace-ai",
      "type": "streamableHttp",
      "url": "http://127.0.0.1:8002/mcp"
    }
  }
}
```

**Claude Code** — add to `.claude/settings.json`:

```json
{
  "mcpServers": {
    "strava-mcp": {
      "type": "streamableHttp",
      "url": "http://127.0.0.1:8001/mcp"
    },
    "pace-ai": {
      "type": "streamableHttp",
      "url": "http://127.0.0.1:8002/mcp"
    }
  }
}
```

### 5. Start a Conversation

Start both servers, then ask Claude:

```bash
strava-mcp &
pace-ai &
```

> "Authenticate with Strava, then analyze my last 4 weeks of running and give me a weekly plan."

Claude will call the `authenticate` tool (opens your browser for Strava OAuth), pull your activities, compute ACWR and training zones, then generate a personalized plan using the coaching methodology.

## What You Can Do

### strava-mcp — Data Access (7 tools, 2 resources)

| Tool | Description |
|------|-------------|
| `authenticate` | Trigger Strava OAuth flow (opens browser) |
| `get_athlete` | Athlete profile |
| `get_recent_activities` | Recent activities with pace, HR, elevation |
| `get_activity` | Full detail for one activity (splits, laps) |
| `get_activity_streams` | Time-series data (HR, GPS, cadence, altitude) |
| `get_athlete_stats` | Year-to-date and all-time stats |
| `get_athlete_zones` | Heart rate and power zone definitions |

### pace-ai — Coaching Intelligence (7 tools, 4 prompts, 2 resources)

| Tool | Description |
|------|-------------|
| `analyze_training_load` | ACWR calculation with injury risk classification |
| `predict_race_time` | VDOT + Riegel race time predictions |
| `calculate_training_zones` | Daniels' pace and HR zones |
| `set_goal` | Store a race goal (distance, target time, date) |
| `get_goals` | List all goals |
| `update_goal` | Update a goal |
| `delete_goal` | Delete a goal |

| Prompt | Description |
|--------|-------------|
| `weekly_plan` | Structured weekly training plan with methodology |
| `run_analysis` | Post-run coaching analysis |
| `race_readiness` | Race readiness assessment |
| `injury_risk` | Injury risk assessment from load patterns |

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `STRAVA_CLIENT_ID` | *(required)* | From Strava API settings |
| `STRAVA_CLIENT_SECRET` | *(required)* | From Strava API settings |
| `STRAVA_ACCESS_TOKEN` | *(empty)* | Optional bootstrap token |
| `STRAVA_REFRESH_TOKEN` | *(empty)* | Optional bootstrap token |
| `STRAVA_MCP_HOST` | `127.0.0.1` | strava-mcp bind address |
| `STRAVA_MCP_PORT` | `8001` | strava-mcp HTTP port |
| `STRAVA_MCP_DB` | `strava_mcp.db` | SQLite path (tokens + cache) |
| `PACE_AI_HOST` | `127.0.0.1` | pace-ai bind address |
| `PACE_AI_PORT` | `8002` | pace-ai HTTP port |
| `PACE_AI_DB` | `pace_ai.db` | SQLite path (goals) |

## Development

```bash
# Install in dev mode
pip install -e ./strava-mcp[dev] -e ./pace-ai[dev]

# Run tests
cd strava-mcp && python -m pytest tests/ && cd ..
cd pace-ai && python -m pytest tests/ && cd ..

# Lint
ruff check strava-mcp/ pace-ai/
ruff format --check strava-mcp/ pace-ai/
```

See [strava-mcp/README.md](strava-mcp/README.md) and [pace-ai/README.md](pace-ai/README.md) for server-specific details.

## License

[MIT](LICENSE)
