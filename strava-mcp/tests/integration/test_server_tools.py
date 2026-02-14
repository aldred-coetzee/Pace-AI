"""Integration tests for strava-mcp server tools with mocked Strava API."""

from __future__ import annotations

import httpx
import pytest
import respx

from strava_mcp.auth import TokenStore
from strava_mcp.cache import ActivityCache
from strava_mcp.client import STRAVA_API_BASE, StravaClient
from strava_mcp.config import Settings

from ..conftest import (
    sample_activity,
    sample_activity_detail,
    sample_athlete,
    sample_athlete_stats,
    sample_streams,
    sample_zones,
)


@pytest.fixture()
def _wired(tmp_path, monkeypatch):
    """Wire up server module globals with test instances."""
    import strava_mcp.server as srv

    db = str(tmp_path / "integration.db")
    settings = Settings(
        client_id="12345",
        client_secret="test_secret",
        access_token="test_access_token",
        db_path=db,
    )
    monkeypatch.setattr(srv, "settings", settings)
    monkeypatch.setattr(srv, "token_store", TokenStore(db))
    monkeypatch.setattr(srv, "cache", ActivityCache(db))
    monkeypatch.setattr(srv, "strava", StravaClient(settings, TokenStore(db)))


@pytest.mark.usefixtures("_wired")
class TestGetAthleteTool:
    @respx.mock
    @pytest.mark.asyncio()
    async def test_returns_athlete_profile(self):
        from strava_mcp.server import get_athlete

        athlete = sample_athlete()
        respx.get(f"{STRAVA_API_BASE}/athlete").mock(return_value=httpx.Response(200, json=athlete))

        result = await get_athlete()
        assert result["id"] == 123456
        assert result["firstname"] == "Test"

    @respx.mock
    @pytest.mark.asyncio()
    async def test_caches_athlete_profile(self):
        from strava_mcp.server import get_athlete

        athlete = sample_athlete()
        route = respx.get(f"{STRAVA_API_BASE}/athlete").mock(return_value=httpx.Response(200, json=athlete))

        await get_athlete()
        await get_athlete()  # should hit cache

        assert route.call_count == 1


@pytest.mark.usefixtures("_wired")
class TestGetRecentActivitiesTool:
    @respx.mock
    @pytest.mark.asyncio()
    async def test_returns_enriched_activities(self):
        from strava_mcp.server import get_recent_activities

        activities = [sample_activity(1), sample_activity(2, distance=5000.0, average_speed=2.5)]
        respx.get(f"{STRAVA_API_BASE}/athlete/activities").mock(return_value=httpx.Response(200, json=activities))

        result = await get_recent_activities(days=30)
        assert len(result) == 2
        assert result[0]["distance_km"] == 10.0
        assert result[0]["pace_min_per_km"] is not None
        assert result[1]["distance_km"] == 5.0


@pytest.mark.usefixtures("_wired")
class TestGetActivityTool:
    @respx.mock
    @pytest.mark.asyncio()
    async def test_returns_full_detail(self):
        from strava_mcp.server import get_activity

        detail = sample_activity_detail(42)
        respx.get(f"{STRAVA_API_BASE}/activities/42").mock(return_value=httpx.Response(200, json=detail))

        result = await get_activity(42)
        assert result["id"] == 42
        assert len(result["splits_metric"]) == 10
        assert len(result["laps"]) == 2


@pytest.mark.usefixtures("_wired")
class TestGetActivityStreamsTool:
    @respx.mock
    @pytest.mark.asyncio()
    async def test_reshapes_streams(self):
        from strava_mcp.server import get_activity_streams

        streams = sample_streams()
        respx.get(f"{STRAVA_API_BASE}/activities/42/streams").mock(return_value=httpx.Response(200, json=streams))

        result = await get_activity_streams(42)
        assert "time" in result
        assert "heartrate" in result
        assert isinstance(result["time"], list)


@pytest.mark.usefixtures("_wired")
class TestGetAthleteStatsTool:
    @respx.mock
    @pytest.mark.asyncio()
    async def test_returns_stats(self):
        from strava_mcp.server import get_athlete_stats

        athlete = sample_athlete()
        stats = sample_athlete_stats()
        respx.get(f"{STRAVA_API_BASE}/athlete").mock(return_value=httpx.Response(200, json=athlete))
        respx.get(f"{STRAVA_API_BASE}/athletes/123456/stats").mock(return_value=httpx.Response(200, json=stats))

        result = await get_athlete_stats()
        assert "ytd_run_totals" in result
        assert result["ytd_run_totals"]["count"] == 150


@pytest.mark.usefixtures("_wired")
class TestGetAthleteZonesTool:
    @respx.mock
    @pytest.mark.asyncio()
    async def test_returns_zones(self):
        from strava_mcp.server import get_athlete_zones

        zones = sample_zones()
        respx.get(f"{STRAVA_API_BASE}/athlete/zones").mock(return_value=httpx.Response(200, json=zones))

        result = await get_athlete_zones()
        assert "heart_rate" in result
        assert len(result["heart_rate"]["zones"]) == 5
