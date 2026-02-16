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
    host=settings.host,
    port=settings.port,
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
    result = {stream["type"]: stream["data"] for stream in data} if isinstance(data, list) else data

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


@mcp.tool()
async def get_best_efforts(days: int = 365) -> list[dict]:
    """Get personal best efforts across all activities for standard distances.

    Scans activity history and extracts auto-detected best efforts (400m, 1K, mile,
    5K, 10K, half marathon, marathon). Returns the single best time for each distance.

    Args:
        days: Number of days to look back (default 365).
    """
    after = int((datetime.now(tz=timezone.utc) - timedelta(days=days)).timestamp())
    cache_key = f"best_efforts_{days}d_{after // 86400}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    activities = await strava.get_all_activities(after=after)

    # Collect best efforts from detailed activities (best_efforts only on DetailedActivity)
    bests: dict[str, dict] = {}
    for a in activities:
        if a.get("type") != "Run" and a.get("sport_type") not in ("Run", "TrailRun", "VirtualRun"):
            continue
        try:
            detail = await strava.get_activity(a["id"])
        except Exception:
            continue
        for effort in detail.get("best_efforts", []):
            name = effort.get("name", "")
            elapsed = effort.get("elapsed_time", 0)
            if not name or not elapsed:
                continue
            if name not in bests or elapsed < bests[name]["elapsed_time"]:
                bests[name] = {
                    "distance_name": name,
                    "distance_m": effort.get("distance", 0),
                    "elapsed_time": elapsed,
                    "elapsed_time_formatted": _format_seconds(elapsed),
                    "activity_id": a["id"],
                    "activity_name": a.get("name", ""),
                    "activity_date": a.get("start_date", ""),
                }

    result = sorted(bests.values(), key=lambda x: x["distance_m"])
    cache.set(cache_key, result)
    return result


@mcp.tool()
async def get_weekly_summary(weeks: int = 8) -> list[dict]:
    """Aggregate activities into rolling weekly summaries.

    Returns per-week totals: distance, time, elevation, run count, average pace,
    longest run, and week-over-week change percentage.

    Args:
        weeks: Number of weeks to summarise (default 8).
    """
    days = weeks * 7
    after = int((datetime.now(tz=timezone.utc) - timedelta(days=days)).timestamp())
    cache_key = f"weekly_summary_{weeks}w_{after // 86400}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    activities = await strava.get_all_activities(after=after)
    runs = [a for a in activities if a.get("type") == "Run" or a.get("sport_type") in ("Run", "TrailRun", "VirtualRun")]

    # Bucket into ISO weeks
    week_buckets: dict[str, list[dict]] = {}
    for r in runs:
        dt = datetime.fromisoformat(r["start_date"].replace("Z", "+00:00"))
        week_key = dt.strftime("%G-W%V")
        week_buckets.setdefault(week_key, []).append(r)

    # Build sorted weekly summaries
    summaries: list[dict] = []
    for week_key in sorted(week_buckets):
        bucket = week_buckets[week_key]
        total_distance = sum(a.get("distance", 0) for a in bucket)
        total_time = sum(a.get("moving_time", 0) for a in bucket)
        total_elevation = sum(a.get("total_elevation_gain", 0) for a in bucket)
        longest_run = max((a.get("distance", 0) for a in bucket), default=0)
        avg_speed = total_distance / total_time if total_time > 0 else 0

        summaries.append(
            {
                "week": week_key,
                "run_count": len(bucket),
                "total_distance_km": round(total_distance / 1000, 2),
                "total_time_s": total_time,
                "total_time_formatted": _format_seconds(total_time),
                "total_elevation_m": round(total_elevation, 1),
                "longest_run_km": round(longest_run / 1000, 2),
                "average_pace_per_km": _speed_to_pace(avg_speed),
            }
        )

    # Add week-over-week change
    for i, s in enumerate(summaries):
        if i > 0 and summaries[i - 1]["total_distance_km"] > 0:
            prev = summaries[i - 1]["total_distance_km"]
            s["week_over_week_change_pct"] = round((s["total_distance_km"] - prev) / prev * 100, 1)
        else:
            s["week_over_week_change_pct"] = None

    cache.set(cache_key, summaries)
    return summaries


@mcp.tool()
async def get_shoe_mileage() -> list[dict]:
    """Get mileage for all shoes/gear linked to running activities.

    Returns each shoe with total distance, activity count, and retirement warnings
    (>500 km and >800 km thresholds).
    """
    cache_key = f"shoe_mileage_{int(time.time()) // 3600}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    athlete = await strava.get_athlete()
    shoes_raw = athlete.get("shoes", [])

    result = []
    for shoe in shoes_raw:
        distance_km = round(shoe.get("distance", 0) / 1000, 1)
        retired = shoe.get("retired", False)
        result.append(
            {
                "id": shoe.get("id", ""),
                "name": shoe.get("name", "Unknown"),
                "distance_km": distance_km,
                "retired": retired,
                "warning": "replace_soon" if distance_km > 500 and not retired else None,
                "critical": "overdue_replacement" if distance_km > 800 and not retired else None,
            }
        )

    result.sort(key=lambda x: x["distance_km"], reverse=True)
    cache.set(cache_key, result)
    return result


@mcp.tool()
async def search_activities(
    days: int = 90,
    activity_type: str | None = None,
    min_distance_km: float | None = None,
    max_distance_km: float | None = None,
    name_contains: str | None = None,
) -> list[dict]:
    """Search and filter activities by type, distance, and name.

    Args:
        days: Number of days to look back (default 90).
        activity_type: Filter by activity type (e.g. "Run", "Ride", "Swim").
        min_distance_km: Minimum distance in km.
        max_distance_km: Maximum distance in km.
        name_contains: Filter by name substring (case-insensitive).
    """
    after = int((datetime.now(tz=timezone.utc) - timedelta(days=days)).timestamp())
    activities = await strava.get_all_activities(after=after)

    results = []
    for a in activities:
        # Type filter: check both type and sport_type fields
        if (
            activity_type
            and a.get("type", "").lower() != activity_type.lower()
            and a.get("sport_type", "").lower() != activity_type.lower()
        ):
            continue

        dist_km = a.get("distance", 0) / 1000

        # Distance filters
        if min_distance_km is not None and dist_km < min_distance_km:
            continue
        if max_distance_km is not None and dist_km > max_distance_km:
            continue

        # Name filter
        if name_contains and name_contains.lower() not in a.get("name", "").lower():
            continue

        results.append(
            {
                "id": a["id"],
                "name": a.get("name", ""),
                "type": a.get("type", ""),
                "start_date": a.get("start_date", ""),
                "distance_km": round(dist_km, 2),
                "moving_time_s": a.get("moving_time", 0),
                "moving_time_formatted": _format_seconds(a.get("moving_time", 0)),
                "pace_min_per_km": _speed_to_pace(a.get("average_speed", 0)),
                "average_heartrate": a.get("average_heartrate"),
                "total_elevation_gain_m": a.get("total_elevation_gain", 0),
            }
        )

    return results


@mcp.tool()
async def get_segment_analysis(days: int = 180, min_efforts: int = 2) -> list[dict]:
    """Find repeated segments and compare performance over time.

    Scans recent running activities for Strava segments that have been run multiple times,
    showing the progression of times for each segment.

    Args:
        days: Number of days to look back (default 180).
        min_efforts: Minimum number of efforts on a segment to include (default 2).
    """
    after = int((datetime.now(tz=timezone.utc) - timedelta(days=days)).timestamp())
    cache_key = f"segment_analysis_{days}d_{min_efforts}e_{after // 86400}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    activities = await strava.get_all_activities(after=after)
    runs = [a for a in activities if a.get("type") == "Run" or a.get("sport_type") in ("Run", "TrailRun")]

    # Collect segment efforts from detailed activities
    segment_efforts: dict[int, list[dict]] = {}
    segment_info: dict[int, dict] = {}

    for a in runs:
        try:
            detail = await strava.get_activity(a["id"])
        except Exception:
            continue

        for effort in detail.get("segment_efforts", []):
            seg = effort.get("segment", {})
            seg_id = seg.get("id")
            if not seg_id:
                continue

            if seg_id not in segment_info:
                segment_info[seg_id] = {
                    "name": seg.get("name", "Unknown"),
                    "distance_m": seg.get("distance", 0),
                }

            segment_efforts.setdefault(seg_id, []).append(
                {
                    "elapsed_time": effort.get("elapsed_time", 0),
                    "elapsed_time_formatted": _format_seconds(effort.get("elapsed_time", 0)),
                    "activity_id": a["id"],
                    "activity_name": a.get("name", ""),
                    "date": effort.get("start_date", a.get("start_date", "")),
                    "average_heartrate": effort.get("average_heartrate"),
                }
            )

    # Filter to segments with enough efforts and build result
    result = []
    for seg_id, efforts in segment_efforts.items():
        if len(efforts) < min_efforts:
            continue

        efforts_sorted = sorted(efforts, key=lambda e: e["date"])
        times = [e["elapsed_time"] for e in efforts_sorted]
        best_time = min(times)
        worst_time = max(times)

        # Trend: compare first half avg to second half avg
        mid = len(times) // 2
        first_avg = sum(times[:mid]) / mid if mid > 0 else times[0]
        second_avg = sum(times[mid:]) / (len(times) - mid) if len(times) - mid > 0 else times[-1]
        trend_pct = round((second_avg - first_avg) / first_avg * 100, 1) if first_avg > 0 else 0.0

        info = segment_info[seg_id]
        result.append(
            {
                "segment_id": seg_id,
                "segment_name": info["name"],
                "distance_m": info["distance_m"],
                "effort_count": len(efforts_sorted),
                "best_time": _format_seconds(best_time),
                "best_time_seconds": best_time,
                "worst_time": _format_seconds(worst_time),
                "improvement_pct": round((worst_time - best_time) / worst_time * 100, 1) if worst_time > 0 else 0,
                "trend_pct": trend_pct,
                "trend_direction": "improving" if trend_pct < -3 else "declining" if trend_pct > 3 else "stable",
                "efforts": efforts_sorted,
            }
        )

    result.sort(key=lambda x: x["effort_count"], reverse=True)
    cache.set(cache_key, result)
    return result


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


def _format_seconds(total_seconds: int) -> str:
    """Format seconds as H:MM:SS or M:SS."""
    h, remainder = divmod(total_seconds, 3600)
    m, s = divmod(remainder, 60)
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def main() -> None:
    """Entry point for the strava-mcp server."""
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
