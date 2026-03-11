"""Shared test fixtures for notion-mcp."""

from __future__ import annotations

import pytest

from notion_mcp.cache import init_db
from notion_mcp.config import Settings


@pytest.fixture()
def settings():
    """Test settings with no real credentials."""
    return Settings()


@pytest.fixture()
def mem_db():
    """In-memory SQLite database with schema initialized."""
    conn = init_db(":memory:")
    yield conn
    conn.close()


def make_notion_page(
    page_id: str = "page-001",
    date: str = "2026-03-10",
    stress: int | None = 3,
    niggles: str | None = "Right achilles tight",
    notes: str | None = "Easy 5k, felt okay",
    last_edited: str = "2026-03-10T10:00:00.000Z",
) -> dict:
    """Factory for a Notion page object matching the diary database schema."""
    props: dict = {
        "Date": {"date": {"start": date} if date else None},
        "Stress": {
            "type": "select",
            "select": {"id": "test", "name": f"{stress} (Test)", "color": "yellow"} if stress is not None else None,
        },
        "Niggles": {
            "rich_text": [{"plain_text": niggles}] if niggles else [],
        },
        "Notes": {
            "rich_text": [{"plain_text": notes}] if notes else [],
        },
        "Title": {"title": []},
    }
    return {
        "id": page_id,
        "last_edited_time": last_edited,
        "properties": props,
    }


def make_notion_query_response(
    pages: list[dict] | None = None,
    has_more: bool = False,
    next_cursor: str | None = None,
) -> dict:
    """Factory for a Notion database query API response."""
    return {
        "results": pages or [make_notion_page()],
        "has_more": has_more,
        "next_cursor": next_cursor,
    }


def make_diary_entry(
    page_id: str = "page-001",
    date: str = "2026-03-10",
    stress: int | None = 3,
    niggles: str | None = "Right achilles tight",
    notes: str | None = "Easy 5k, felt okay",
    last_edited: str = "2026-03-10T10:00:00.000Z",
) -> dict:
    """Factory for a parsed diary entry dict (output of parse_diary_entry)."""
    return {
        "page_id": page_id,
        "last_edited": last_edited,
        "date": date,
        "stress": stress,
        "niggles": niggles,
        "notes": notes,
    }
