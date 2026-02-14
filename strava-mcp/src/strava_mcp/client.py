"""Strava API client with automatic token refresh."""

from __future__ import annotations

import time
from typing import Any

import httpx

from strava_mcp.auth import TokenStore, refresh_access_token
from strava_mcp.config import Settings

STRAVA_API_BASE = "https://www.strava.com/api/v3"


class RateLimitInfo:
    """Tracks Strava API rate limit state from response headers."""

    def __init__(self) -> None:
        self.fifteen_min_usage: int = 0
        self.fifteen_min_limit: int = 100  # Read rate limit (binding for read-only apps)
        self.daily_usage: int = 0
        self.daily_limit: int = 1000  # Read rate limit (binding for read-only apps)

    def update_from_headers(self, headers: httpx.Headers) -> None:
        try:
            usage = headers.get("X-RateLimit-Usage", "")
            limit = headers.get("X-RateLimit-Limit", "")
            if usage:
                parts = usage.split(",")
                if len(parts) == 2:
                    self.fifteen_min_usage = int(parts[0].strip())
                    self.daily_usage = int(parts[1].strip())
            if limit:
                parts = limit.split(",")
                if len(parts) == 2:
                    self.fifteen_min_limit = int(parts[0].strip())
                    self.daily_limit = int(parts[1].strip())
        except ValueError:
            pass  # Malformed headers — don't crash the request

    def to_dict(self) -> dict[str, Any]:
        return {
            "fifteen_min": {"usage": self.fifteen_min_usage, "limit": self.fifteen_min_limit},
            "daily": {"usage": self.daily_usage, "limit": self.daily_limit},
        }


class StravaClient:
    """Async Strava API client with token management."""

    def __init__(self, settings: Settings, token_store: TokenStore) -> None:
        self._settings = settings
        self._token_store = token_store
        self._http: httpx.AsyncClient | None = None
        self.rate_limits = RateLimitInfo()

    async def _get_http(self) -> httpx.AsyncClient:
        if self._http is None or self._http.is_closed:
            self._http = httpx.AsyncClient(base_url=STRAVA_API_BASE, timeout=30.0)
        return self._http

    async def close(self) -> None:
        if self._http and not self._http.is_closed:
            await self._http.aclose()

    async def _get_access_token(self) -> str:
        """Get a valid access token, refreshing if expired."""
        tokens = self._token_store.load()

        # If we have stored tokens, check expiry
        if tokens:
            if tokens["expires_at"] > time.time() + 60:
                return tokens["access_token"]
            # Token expired — refresh it
            refreshed = await refresh_access_token(
                self._settings.client_id,
                self._settings.client_secret,
                tokens["refresh_token"],
            )
            self._token_store.save(
                access_token=refreshed["access_token"],
                refresh_token=refreshed["refresh_token"],
                expires_at=refreshed["expires_at"],
                athlete_id=tokens.get("athlete_id"),
            )
            return refreshed["access_token"]

        # Fall back to env var tokens (first run before OAuth)
        if self._settings.access_token:
            return self._settings.access_token

        msg = "No access token available. Run the authenticate tool first."
        raise RuntimeError(msg)

    async def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        """Make an authenticated API request."""
        token = await self._get_access_token()
        http = await self._get_http()

        resp = await http.request(
            method,
            path,
            headers={"Authorization": f"Bearer {token}"},
            **kwargs,
        )
        self.rate_limits.update_from_headers(resp.headers)

        if resp.status_code == 429:
            msg = "Strava API rate limit exceeded. Check strava://rate-limits for current usage."
            raise RuntimeError(msg)
        if resp.status_code == 401:
            # Token may have been revoked — clear stored tokens
            self._token_store.clear()
            msg = "Strava token expired or revoked. Run the authenticate tool to re-authorize."
            raise RuntimeError(msg)

        resp.raise_for_status()
        return resp.json()

    async def get_athlete(self) -> dict[str, Any]:
        return await self._request("GET", "/athlete")

    async def get_athlete_stats(self, athlete_id: int) -> dict[str, Any]:
        return await self._request("GET", f"/athletes/{athlete_id}/stats")

    async def get_athlete_zones(self) -> dict[str, Any]:
        return await self._request("GET", "/athlete/zones")

    async def get_activities(self, *, after: int | None = None, before: int | None = None, per_page: int = 50) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"per_page": per_page}
        if after is not None:
            params["after"] = after
        if before is not None:
            params["before"] = before
        return await self._request("GET", "/athlete/activities", params=params)

    async def get_activity(self, activity_id: int) -> dict[str, Any]:
        return await self._request("GET", f"/activities/{activity_id}", params={"include_all_efforts": True})

    async def get_activity_streams(self, activity_id: int, stream_types: list[str]) -> dict[str, Any]:
        keys = ",".join(stream_types)
        return await self._request(
            "GET",
            f"/activities/{activity_id}/streams",
            params={"keys": keys, "key_type": "time"},
        )
