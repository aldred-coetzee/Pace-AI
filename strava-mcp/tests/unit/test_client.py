"""Unit tests for Strava API client."""

from __future__ import annotations

import time

import httpx
import pytest
import respx

from strava_mcp.auth import TokenStore
from strava_mcp.client import STRAVA_API_BASE, RateLimitInfo, StravaClient
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
def strava_client(settings, token_store):
    return StravaClient(settings, token_store)


class TestRateLimitInfo:
    def test_default_values(self):
        info = RateLimitInfo()
        assert info.fifteen_min_limit == 100
        assert info.daily_limit == 1000

    def test_update_from_headers(self):
        info = RateLimitInfo()
        headers = httpx.Headers({"X-RateLimit-Usage": "42, 500", "X-RateLimit-Limit": "100, 1000"})
        info.update_from_headers(headers)

        assert info.fifteen_min_usage == 42
        assert info.daily_usage == 500
        assert info.fifteen_min_limit == 100
        assert info.daily_limit == 1000

    def test_update_from_empty_headers(self):
        info = RateLimitInfo()
        info.update_from_headers(httpx.Headers({}))
        assert info.fifteen_min_usage == 0
        assert info.daily_usage == 0

    def test_to_dict(self):
        info = RateLimitInfo()
        d = info.to_dict()
        assert "fifteen_min" in d
        assert "daily" in d
        assert d["fifteen_min"]["usage"] == 0
        assert d["daily"]["limit"] == 1000


class TestStravaClient:
    @respx.mock
    @pytest.mark.asyncio()
    async def test_get_athlete(self, strava_client):
        athlete = sample_athlete()
        respx.get(f"{STRAVA_API_BASE}/athlete").mock(return_value=httpx.Response(200, json=athlete))

        result = await strava_client.get_athlete()
        assert result["id"] == 123456
        assert result["firstname"] == "Test"
        await strava_client.close()

    @respx.mock
    @pytest.mark.asyncio()
    async def test_get_activities(self, strava_client):
        activities = [sample_activity(1), sample_activity(2)]
        respx.get(f"{STRAVA_API_BASE}/athlete/activities").mock(return_value=httpx.Response(200, json=activities))

        result = await strava_client.get_activities(per_page=10)
        assert len(result) == 2
        assert result[0]["id"] == 1
        await strava_client.close()

    @respx.mock
    @pytest.mark.asyncio()
    async def test_get_activity(self, strava_client):
        detail = sample_activity_detail(42)
        respx.get(f"{STRAVA_API_BASE}/activities/42").mock(return_value=httpx.Response(200, json=detail))

        result = await strava_client.get_activity(42)
        assert result["id"] == 42
        assert "splits_metric" in result
        await strava_client.close()

    @respx.mock
    @pytest.mark.asyncio()
    async def test_get_activity_streams(self, strava_client):
        streams = sample_streams()
        respx.get(f"{STRAVA_API_BASE}/activities/42/streams").mock(return_value=httpx.Response(200, json=streams))

        result = await strava_client.get_activity_streams(42, ["time", "heartrate"])
        assert isinstance(result, list)
        assert result[0]["type"] == "time"
        await strava_client.close()

    @respx.mock
    @pytest.mark.asyncio()
    async def test_get_athlete_stats(self, strava_client):
        stats = sample_athlete_stats()
        respx.get(f"{STRAVA_API_BASE}/athletes/42/stats").mock(return_value=httpx.Response(200, json=stats))

        result = await strava_client.get_athlete_stats(42)
        assert "ytd_run_totals" in result
        await strava_client.close()

    @respx.mock
    @pytest.mark.asyncio()
    async def test_get_athlete_zones(self, strava_client):
        zones = sample_zones()
        respx.get(f"{STRAVA_API_BASE}/athlete/zones").mock(return_value=httpx.Response(200, json=zones))

        result = await strava_client.get_athlete_zones()
        assert "heart_rate" in result
        await strava_client.close()

    @respx.mock
    @pytest.mark.asyncio()
    async def test_401_raises_runtime_error(self, strava_client):
        respx.get(f"{STRAVA_API_BASE}/athlete").mock(return_value=httpx.Response(401, json={"message": "Unauthorized"}))

        with pytest.raises(RuntimeError, match="expired or revoked"):
            await strava_client.get_athlete()
        await strava_client.close()

    @respx.mock
    @pytest.mark.asyncio()
    async def test_429_raises_rate_limit_error(self, strava_client):
        respx.get(f"{STRAVA_API_BASE}/athlete").mock(
            return_value=httpx.Response(429, json={"message": "Rate Limit Exceeded"}),
        )

        with pytest.raises(RuntimeError, match="rate limit"):
            await strava_client.get_athlete()
        await strava_client.close()

    @respx.mock
    @pytest.mark.asyncio()
    async def test_500_raises_http_error(self, strava_client):
        respx.get(f"{STRAVA_API_BASE}/athlete").mock(return_value=httpx.Response(500, json={"message": "Server Error"}))

        with pytest.raises(httpx.HTTPStatusError):
            await strava_client.get_athlete()
        await strava_client.close()

    @respx.mock
    @pytest.mark.asyncio()
    async def test_rate_limits_updated(self, strava_client):
        athlete = sample_athlete()
        headers = {"X-RateLimit-Usage": "5, 100", "X-RateLimit-Limit": "100, 1000"}
        respx.get(f"{STRAVA_API_BASE}/athlete").mock(return_value=httpx.Response(200, json=athlete, headers=headers))

        await strava_client.get_athlete()
        assert strava_client.rate_limits.fifteen_min_usage == 5
        assert strava_client.rate_limits.daily_usage == 100
        await strava_client.close()

    @respx.mock
    @pytest.mark.asyncio()
    async def test_token_refresh_on_expiry(self, strava_client, token_store):
        # Store an expired token
        token_store.save("expired_access", "my_refresh", int(time.time()) - 100, athlete_id=42)

        # Mock the token refresh endpoint
        refresh_response = {
            "access_token": "new_access",
            "refresh_token": "new_refresh",
            "expires_at": int(time.time()) + 3600,
        }
        respx.post("https://www.strava.com/oauth/token").mock(return_value=httpx.Response(200, json=refresh_response))

        # Mock the actual API call
        athlete = sample_athlete()
        respx.get(f"{STRAVA_API_BASE}/athlete").mock(return_value=httpx.Response(200, json=athlete))

        result = await strava_client.get_athlete()
        assert result["id"] == 123456

        # Verify token was updated
        tokens = token_store.load()
        assert tokens["access_token"] == "new_access"
        await strava_client.close()

    @pytest.mark.asyncio()
    async def test_no_token_raises(self, tmp_path):
        s = Settings(client_id="1", client_secret="s", db_path=str(tmp_path / "test.db"))
        ts = TokenStore(str(tmp_path / "test.db"))
        client = StravaClient(s, ts)

        with pytest.raises(RuntimeError, match="No access token"):
            await client._get_access_token()
        await client.close()
