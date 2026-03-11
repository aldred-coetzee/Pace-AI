"""Integration tests for notion-mcp server tools.

Tests each tool through the actual async function with mocked NotionClient.
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from notion_mcp.client import NotionAPIError
from notion_mcp.config import Settings
from tests.conftest import make_notion_page


@pytest.fixture()
def _wired(monkeypatch, mem_db):
    """Wire up server module globals with test instances."""
    import notion_mcp.server as srv

    settings = Settings()
    monkeypatch.setattr(srv, "settings", settings)
    monkeypatch.setattr(srv, "db", mem_db)

    mock_client = AsyncMock()
    mock_client.fetch_all_entries.return_value = [make_notion_page()]
    monkeypatch.setattr(srv, "notion", mock_client)
    return mock_client


@pytest.mark.usefixtures("_wired")
class TestGetDiaryEntries:
    @pytest.mark.asyncio()
    async def test_syncs_and_returns(self, _wired, mem_db):
        from notion_mcp.server import get_diary_entries

        result = await get_diary_entries(days=28)
        assert result["synced"] == 1
        assert result["count"] == 1
        assert result["days"] == 28
        assert result["entries"][0]["date"] == "2026-03-10"
        assert result["entries"][0]["stress"] == 3
        assert result["entries"][0]["niggles"] == "Right achilles tight"

    @pytest.mark.asyncio()
    async def test_returns_empty_when_no_entries(self, _wired):
        from notion_mcp.server import get_diary_entries

        _wired.fetch_all_entries.return_value = []
        result = await get_diary_entries(days=7)
        assert result["count"] == 0
        assert result["entries"] == []
        assert result["synced"] == 0

    @pytest.mark.asyncio()
    async def test_api_error_returns_error_dict(self, _wired):
        from notion_mcp.server import get_diary_entries

        _wired.fetch_all_entries.side_effect = NotionAPIError("auth_failed", "Bad token", "Re-auth")
        result = await get_diary_entries()
        assert result["error"] == "auth_failed"

    @pytest.mark.asyncio()
    async def test_custom_days_param(self, _wired):
        from notion_mcp.server import get_diary_entries

        result = await get_diary_entries(days=7)
        assert result["days"] == 7

    @pytest.mark.asyncio()
    async def test_skips_entries_without_date(self, _wired):
        from notion_mcp.server import get_diary_entries

        page_no_date = make_notion_page()
        page_no_date["properties"]["Date"] = {"date": None}
        _wired.fetch_all_entries.return_value = [page_no_date]

        result = await get_diary_entries()
        assert result["synced"] == 0
        assert result["count"] == 0

    @pytest.mark.asyncio()
    async def test_multiple_entries(self, _wired):
        from notion_mcp.server import get_diary_entries

        _wired.fetch_all_entries.return_value = [
            make_notion_page(page_id="p1", date="2026-03-10", stress=4),
            make_notion_page(page_id="p2", date="2026-03-09", stress=2),
        ]
        result = await get_diary_entries(days=28)
        assert result["synced"] == 2
        assert result["count"] == 2
        # Should be ordered by date descending
        assert result["entries"][0]["date"] == "2026-03-10"
        assert result["entries"][1]["date"] == "2026-03-09"
