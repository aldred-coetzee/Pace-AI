"""Unit tests for client module."""

from __future__ import annotations

import httpx
import pytest
import respx

from notion_mcp.client import NotionAPIError, NotionClient, _parse_stress_select, parse_diary_entry
from notion_mcp.config import Settings
from tests.conftest import make_notion_page, make_notion_query_response


@pytest.fixture()
def client():
    """NotionClient with test credentials."""
    return NotionClient(Settings(notion_token="ntn_test", diary_database_id="db-123"))


class TestNotionClient:
    @respx.mock
    @pytest.mark.asyncio()
    async def test_query_diary_success(self, client):
        response = make_notion_query_response()
        respx.post("https://api.notion.com/v1/databases/db-123/query").mock(
            return_value=httpx.Response(200, json=response)
        )
        result = await client.query_diary()
        assert len(result["results"]) == 1
        assert result["has_more"] is False

    @respx.mock
    @pytest.mark.asyncio()
    async def test_query_diary_with_cursor(self, client):
        response = make_notion_query_response()
        route = respx.post("https://api.notion.com/v1/databases/db-123/query").mock(
            return_value=httpx.Response(200, json=response)
        )
        await client.query_diary(start_cursor="cursor-abc")
        assert route.called
        body = route.calls[0].request.content
        assert b"cursor-abc" in body

    @respx.mock
    @pytest.mark.asyncio()
    async def test_query_diary_401(self, client):
        respx.post("https://api.notion.com/v1/databases/db-123/query").mock(
            return_value=httpx.Response(401, json={"message": "Unauthorized"})
        )
        with pytest.raises(NotionAPIError, match="authentication failed"):
            await client.query_diary()

    @respx.mock
    @pytest.mark.asyncio()
    async def test_query_diary_500(self, client):
        respx.post("https://api.notion.com/v1/databases/db-123/query").mock(
            return_value=httpx.Response(500, text="Internal Server Error")
        )
        with pytest.raises(NotionAPIError, match="500"):
            await client.query_diary()

    @pytest.mark.asyncio()
    async def test_query_diary_no_token(self):
        client = NotionClient(Settings(notion_token="", diary_database_id="db-123"))
        with pytest.raises(NotionAPIError, match="NOTION_TOKEN"):
            await client.query_diary()

    @pytest.mark.asyncio()
    async def test_query_diary_no_database_id(self):
        client = NotionClient(Settings(notion_token="ntn_test", diary_database_id=""))
        with pytest.raises(NotionAPIError, match="NOTION_DIARY_DATABASE_ID"):
            await client.query_diary()

    @respx.mock
    @pytest.mark.asyncio()
    async def test_fetch_all_entries_pagination(self, client):
        page1 = make_notion_query_response(
            pages=[make_notion_page(page_id="p1")],
            has_more=True,
            next_cursor="cursor-2",
        )
        page2 = make_notion_query_response(
            pages=[make_notion_page(page_id="p2")],
            has_more=False,
        )
        route = respx.post("https://api.notion.com/v1/databases/db-123/query")
        route.side_effect = [
            httpx.Response(200, json=page1),
            httpx.Response(200, json=page2),
        ]
        results = await client.fetch_all_entries()
        assert len(results) == 2
        assert results[0]["id"] == "p1"
        assert results[1]["id"] == "p2"

    @respx.mock
    @pytest.mark.asyncio()
    async def test_query_diary_connection_error(self, client):
        respx.post("https://api.notion.com/v1/databases/db-123/query").mock(
            side_effect=httpx.ConnectError("Connection refused")
        )
        with pytest.raises(NotionAPIError, match="connect"):
            await client.query_diary()


class TestNotionAPIError:
    def test_to_dict(self):
        err = NotionAPIError("auth_failed", "Bad token", "Re-auth")
        d = err.to_dict()
        assert d["error"] == "auth_failed"
        assert d["message"] == "Bad token"
        assert d["action"] == "Re-auth"


class TestParseStressSelect:
    def test_parses_number_prefix(self):
        assert _parse_stress_select({"name": "3 (Moderate)", "color": "yellow"}) == 3

    def test_parses_single_digit(self):
        assert _parse_stress_select({"name": "5 (Very High)", "color": "red"}) == 5

    def test_returns_none_for_none(self):
        assert _parse_stress_select(None) is None

    def test_returns_none_for_no_number(self):
        assert _parse_stress_select({"name": "Moderate", "color": "yellow"}) is None

    def test_returns_none_for_empty_name(self):
        assert _parse_stress_select({"name": ""}) is None


class TestParseDiaryEntry:
    def test_parses_full_entry(self):
        page = make_notion_page()
        entry = parse_diary_entry(page)
        assert entry is not None
        assert entry["date"] == "2026-03-10"
        assert entry["stress"] == 3
        assert entry["niggles"] == "Right achilles tight"
        assert entry["notes"] == "Easy 5k, felt okay"
        assert entry["page_id"] == "page-001"

    def test_parses_empty_optional_fields(self):
        page = make_notion_page(stress=None, niggles=None, notes=None)
        entry = parse_diary_entry(page)
        assert entry is not None
        assert entry["stress"] is None
        assert entry["niggles"] is None
        assert entry["notes"] is None

    def test_returns_none_for_missing_date(self):
        page = make_notion_page()
        page["properties"]["Date"] = {"date": None}
        assert parse_diary_entry(page) is None

    def test_returns_none_for_empty_date_start(self):
        page = make_notion_page()
        page["properties"]["Date"] = {"date": {"start": None}}
        assert parse_diary_entry(page) is None
