"""Unit tests for auth module."""

from __future__ import annotations

import httpx
import pytest
import respx

from strava_mcp.auth import (
    STRAVA_TOKEN_URL,
    exchange_code,
    refresh_access_token,
)


class TestTokenStore:
    def test_save_and_load(self, token_store):
        token_store.save("access1", "refresh1", 9999999999, athlete_id=42)
        result = token_store.load()

        assert result is not None
        assert result["access_token"] == "access1"
        assert result["refresh_token"] == "refresh1"
        assert result["expires_at"] == 9999999999
        assert result["athlete_id"] == 42

    def test_load_empty(self, token_store):
        assert token_store.load() is None

    def test_save_overwrites(self, token_store):
        token_store.save("old_access", "old_refresh", 1000)
        token_store.save("new_access", "new_refresh", 2000)
        result = token_store.load()

        assert result["access_token"] == "new_access"
        assert result["refresh_token"] == "new_refresh"

    def test_clear(self, token_store):
        token_store.save("access", "refresh", 9999)
        token_store.clear()

        assert token_store.load() is None

    def test_save_without_athlete_id(self, token_store):
        token_store.save("access", "refresh", 9999)
        result = token_store.load()
        assert result["athlete_id"] is None


class TestExchangeCode:
    @respx.mock
    @pytest.mark.asyncio()
    async def test_exchange_code_success(self):
        token_response = {
            "access_token": "new_access",
            "refresh_token": "new_refresh",
            "expires_at": 9999999999,
            "athlete": {"id": 42, "firstname": "Test"},
        }
        respx.post(STRAVA_TOKEN_URL).mock(return_value=httpx.Response(200, json=token_response))

        result = await exchange_code("client_id", "client_secret", "auth_code")

        assert result["access_token"] == "new_access"
        assert result["refresh_token"] == "new_refresh"
        assert result["athlete"]["id"] == 42

    @respx.mock
    @pytest.mark.asyncio()
    async def test_exchange_code_error(self):
        respx.post(STRAVA_TOKEN_URL).mock(return_value=httpx.Response(401, json={"error": "invalid"}))

        with pytest.raises(httpx.HTTPStatusError):
            await exchange_code("client_id", "client_secret", "bad_code")


class TestRefreshAccessToken:
    @respx.mock
    @pytest.mark.asyncio()
    async def test_refresh_success(self):
        token_response = {
            "access_token": "refreshed_access",
            "refresh_token": "refreshed_refresh",
            "expires_at": 9999999999,
        }
        respx.post(STRAVA_TOKEN_URL).mock(return_value=httpx.Response(200, json=token_response))

        result = await refresh_access_token("client_id", "client_secret", "old_refresh")

        assert result["access_token"] == "refreshed_access"

    @respx.mock
    @pytest.mark.asyncio()
    async def test_refresh_expired_token_error(self):
        respx.post(STRAVA_TOKEN_URL).mock(return_value=httpx.Response(401, json={"error": "invalid"}))

        with pytest.raises(httpx.HTTPStatusError):
            await refresh_access_token("client_id", "client_secret", "expired_refresh")
