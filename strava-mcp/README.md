# strava-mcp

A generic MCP server for Strava data access. Handles OAuth, activity retrieval, streams, athlete stats, and caching. Designed to be used by any MCP client (Claude Desktop, Claude Code, etc.).

## Installation

```bash
pip install -e .

# With dev dependencies
pip install -e .[dev]
```

## Configuration

Copy `.env.example` to `.env` and fill in your Strava API credentials:

```bash
cp .env.example .env
```

You need a Strava API application. Create one at [strava.com/settings/api](https://www.strava.com/settings/api):
- Set **Authorization Callback Domain** to `localhost`
- Copy the **Client ID** and **Client Secret** into your `.env`

| Variable | Default | Description |
|----------|---------|-------------|
| `STRAVA_CLIENT_ID` | *(required)* | Your Strava API Client ID |
| `STRAVA_CLIENT_SECRET` | *(required)* | Your Strava API Client Secret |
| `STRAVA_ACCESS_TOKEN` | *(empty)* | Pre-existing access token (optional) |
| `STRAVA_REFRESH_TOKEN` | *(empty)* | Pre-existing refresh token (optional) |
| `STRAVA_MCP_HOST` | `127.0.0.1` | Server bind address |
| `STRAVA_MCP_PORT` | `8001` | Server HTTP port |
| `STRAVA_MCP_DB` | `strava_mcp.db` | SQLite path for tokens and cache |

## Running

```bash
strava-mcp
# Server starts on http://127.0.0.1:8001
```

## Tools

### `authenticate`

Triggers the Strava OAuth flow. Opens your browser to authorize the app, waits for the callback, and stores tokens in SQLite.

```
→ (no arguments)
← "Authenticated as Aldred. Token stored."
```

### `get_athlete`

Returns the authenticated athlete's profile (name, city, weight, clubs, etc.).

### `get_recent_activities`

Lists recent activities with summary stats.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `days` | int | 30 | Number of days to look back |

Returns: list of activities with distance (m/km), pace (min/km), moving time, elevation, HR, and suffer score.

### `get_activity`

Full detail for a single activity including splits, laps, and segment efforts.

| Parameter | Type | Description |
|-----------|------|-------------|
| `activity_id` | int | Strava activity ID |

### `get_activity_streams`

Time-series data for an activity.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `activity_id` | int | | Strava activity ID |
| `stream_types` | list[str] | `["time", "distance", "heartrate", "altitude", "cadence", "velocity_smooth"]` | Streams to fetch |

Available stream types: `time`, `distance`, `latlng`, `altitude`, `heartrate`, `cadence`, `watts`, `temp`, `moving`, `grade_smooth`, `velocity_smooth`.

### `get_athlete_stats`

Year-to-date and all-time athlete statistics (total runs, distance, elevation, etc.).

### `get_athlete_zones`

Heart rate and power zone definitions configured in the athlete's Strava account.

## Resources

| URI | Description |
|-----|-------------|
| `strava://athlete/profile` | Current athlete profile |
| `strava://rate-limits` | Strava API rate limit status |

## OAuth Flow

1. Claude calls `authenticate`
2. Your browser opens the Strava authorization page
3. You click "Authorize"
4. Strava redirects to `localhost:5678/callback` with an authorization code
5. The server exchanges the code for access + refresh tokens
6. Tokens are stored in SQLite and refreshed automatically on expiry

Scopes requested: `read`, `activity:read_all`, `profile:read_all`.

## Caching

All API responses are cached in SQLite with 1-hour TTL. Cache keys are scoped by query parameters (e.g., `recent_activities_30d_<hour>`). The `authenticate` tool is never cached.

## Troubleshooting

**"STRAVA_CLIENT_ID and STRAVA_CLIENT_SECRET must be set"**
- Make sure your `.env` file exists in the working directory (or a parent) and contains both values.

**OAuth callback timeout**
- The server listens on `localhost:5678` for the callback. Make sure that port is free.
- The callback domain in your Strava app settings must be `localhost`.

**Rate limits**
- Strava allows 100 requests per 15 minutes and 1000 per day.
- Check current usage via the `strava://rate-limits` resource.

## Tests

```bash
python -m pytest tests/unit/          # Unit tests (mocked HTTP)
python -m pytest tests/integration/   # Integration tests
python -m pytest tests/e2e/           # E2E server startup test
```

## License

[MIT](../LICENSE)
