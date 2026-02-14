"""FastMCP server for Strava data access."""

from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone

from mcp.server.fastmcp import FastMCP

from strava_mcp.auth import TokenStore, run_oauth_flow
from strava_mcp.cache import ActivityCache
from strava_mcp.client import StravaClient
from strava_mcp.config import Settings

settings = Settings.from_env()
token_store = TokenStore(settings.db_path)
cache = ActivityCache(settings.db_path)
strava = StravaClient(settings, token_store)

mcp = FastMCP(
    "strava-mcp",
    instructions="A generic MCP server for Strava data access",
)


# ── Tools ──────────────────────────────────────────────────────────────


@mcp.tool()
async def authenticate() -> str:
    """Trigger Strava OAuth flow. Opens a browser for authorization."""
    try:
        result = await run_oauth_flow(settings.client_id, settings.client_secret)
        token_store.save(
            access_token=result["access_token"],
            refresh_token=result["refresh_token"],
            expires_at=result["expires_at"],
            athlete_id=result.get("athlete", {}).get("id"),
        )
        athlete_name = result.get("athlete", {}).get("firstname", "Unknown")
        return f"Authenticated as {athlete_name}. Token stored."
    except Exception as e:
        return f"Authentication failed: {e}"


@mcp.tool()
async def get_athlete() -> dict:
    """Get the authenticated athlete's profile."""
    cache_key = "athlete_profile"
    cached = cache.get(cache_key)
    if cached:
        return cached
    data = await strava.get_athlete()
    cache.set(cache_key, data)
    return data


@mcp.tool()
async def get_recent_activities(days: int = 30) -> list[dict]:
    """List recent activities with summary stats.

    Args:
        days: Number of days to look back (default 30).
    """
    after = int((datetime.now(tz=timezone.utc) - timedelta(days=days)).timestamp())
    cache_key = f"recent_activities_{days}d_{after // 3600}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    activities = await strava.get_activities(after=after)
    result = [
        {
            "id": a["id"],
            "name": a["name"],
            "type": a["type"],
            "sport_type": a.get("sport_type", a["type"]),
            "start_date": a["start_date"],
            "distance_m": a["distance"],
            "distance_km": round(a["distance"] / 1000, 2),
            "moving_time_s": a["moving_time"],
            "elapsed_time_s": a["elapsed_time"],
            "total_elevation_gain_m": a.get("total_elevation_gain", 0),
            "average_speed_mps": a.get("average_speed", 0),
            "pace_min_per_km": _speed_to_pace(a.get("average_speed", 0)),
            "average_heartrate": a.get("average_heartrate"),
            "max_heartrate": a.get("max_heartrate"),
            "suffer_score": a.get("suffer_score"),
        }
        for a in activities
    ]
    cache.set(cache_key, result)
    return result


@mcp.tool()
async def get_activity(activity_id: int) -> dict:
    """Get full activity detail including splits, laps, HR, and pace.

    Args:
        activity_id: The Strava activity ID.
    """
    cache_key = f"activity_{activity_id}"
    cached = cache.get(cache_key)
    if cached:
        return cached
    data = await strava.get_activity(activity_id)
    cache.set(cache_key, data)
    return data


@mcp.tool()
async def get_activity_streams(activity_id: int, stream_types: list[str] | None = None) -> dict:
    """Get time-series data for an activity.

    Args:
        activity_id: The Strava activity ID.
        stream_types: List of stream types to fetch. Defaults to common running streams.
            Available: time, distance, latlng, altitude, heartrate, cadence, watts,
            temp, moving, grade_smooth, velocity_smooth.
    """
    if stream_types is None:
        stream_types = ["time", "distance", "heartrate", "altitude", "cadence", "velocity_smooth"]

    cache_key = f"streams_{activity_id}_{'_'.join(sorted(stream_types))}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    data = await strava.get_activity_streams(activity_id, stream_types)

    # Strava returns a list of stream objects; reshape to {type: data}
    if isinstance(data, list):
        result = {stream["type"]: stream["data"] for stream in data}
    else:
        result = data

    cache.set(cache_key, result)
    return result


@mcp.tool()
async def get_athlete_stats() -> dict:
    """Get year-to-date and all-time athlete statistics."""
    athlete = await strava.get_athlete()
    athlete_id = athlete["id"]

    cache_key = f"athlete_stats_{athlete_id}_{int(time.time()) // 3600}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    data = await strava.get_athlete_stats(athlete_id)
    cache.set(cache_key, data)
    return data


@mcp.tool()
async def get_athlete_zones() -> dict:
    """Get heart rate and power zone definitions for the athlete."""
    cache_key = "athlete_zones"
    cached = cache.get(cache_key)
    if cached:
        return cached
    data = await strava.get_athlete_zones()
    cache.set(cache_key, data)
    return data


# ── Resources ──────────────────────────────────────────────────────────


@mcp.resource("strava://athlete/profile")
async def athlete_profile_resource() -> dict:
    """Current athlete profile data."""
    return await strava.get_athlete()


@mcp.resource("strava://rate-limits")
async def rate_limits_resource() -> dict:
    """Current Strava API rate limit status."""
    return strava.rate_limits.to_dict()


# ── Helpers ────────────────────────────────────────────────────────────


def _speed_to_pace(speed_mps: float) -> str | None:
    """Convert m/s to min:sec/km pace string."""
    if speed_mps <= 0:
        return None
    pace_seconds = 1000 / speed_mps
    minutes = int(pace_seconds // 60)
    seconds = int(pace_seconds % 60)
    return f"{minutes}:{seconds:02d}"


def main() -> None:
    """Entry point for the strava-mcp server."""
    mcp.run(transport="streamable-http", host=settings.host, port=settings.port)


if __name__ == "__main__":
    main()
