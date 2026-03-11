"""Notion API client for querying the running diary database."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import httpx

if TYPE_CHECKING:
    from notion_mcp.config import Settings

logger = logging.getLogger(__name__)

NOTION_API_BASE = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"


class NotionAPIError(RuntimeError):
    """Structured error from the Notion API with recovery guidance."""

    def __init__(self, code: str, message: str, action: str) -> None:
        super().__init__(message)
        self.code = code
        self.action = action

    def to_dict(self) -> dict[str, Any]:
        return {
            "error": self.code,
            "message": str(self),
            "action": self.action,
        }


class NotionClient:
    """Queries a Notion database for running diary entries."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._settings.notion_token}",
            "Notion-Version": NOTION_VERSION,
            "Content-Type": "application/json",
        }

    async def query_diary(self, start_cursor: str | None = None) -> dict[str, Any]:
        """Query the diary database, returning one page of results.

        Args:
            start_cursor: Pagination cursor from a previous response.

        Returns:
            Raw Notion API response dict with 'results', 'has_more', 'next_cursor'.
        """
        if not self._settings.notion_token:
            raise NotionAPIError(
                code="not_configured",
                message="NOTION_TOKEN is not set.",
                action="Set NOTION_TOKEN in your .env file.",
            )
        if not self._settings.diary_database_id:
            raise NotionAPIError(
                code="not_configured",
                message="NOTION_DIARY_DATABASE_ID is not set.",
                action="Set NOTION_DIARY_DATABASE_ID in your .env file.",
            )

        url = f"{NOTION_API_BASE}/databases/{self._settings.diary_database_id}/query"
        body: dict[str, Any] = {
            "sorts": [{"property": "Date", "direction": "descending"}],
        }
        if start_cursor:
            body["start_cursor"] = start_cursor

        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(url, headers=self._headers(), json=body, timeout=30.0)
            except httpx.HTTPError as e:
                raise NotionAPIError(
                    code="connection_error",
                    message=f"Failed to connect to Notion API: {e}",
                    action="Check your network connection and try again.",
                ) from e

        if resp.status_code == 401:
            raise NotionAPIError(
                code="auth_failed",
                message="Notion authentication failed (401).",
                action="Check your NOTION_TOKEN is valid and the integration has access to the database.",
            )
        if resp.status_code != 200:
            raise NotionAPIError(
                code="api_error",
                message=f"Notion API returned {resp.status_code}: {resp.text}",
                action="Check the request parameters and try again.",
            )

        return resp.json()

    async def fetch_all_entries(self) -> list[dict[str, Any]]:
        """Fetch all diary entries, handling pagination."""
        all_results: list[dict[str, Any]] = []
        cursor: str | None = None

        while True:
            data = await self.query_diary(start_cursor=cursor)
            all_results.extend(data.get("results", []))
            if not data.get("has_more"):
                break
            cursor = data.get("next_cursor")

        return all_results


def _parse_stress_select(select: dict[str, Any] | None) -> int | None:
    """Extract the numeric stress level from a Notion select option.

    Expects names like "3 (Moderate)" — returns the leading integer, or None.
    """
    if not select:
        return None
    name = select.get("name", "")
    parts = name.split(None, 1)
    if parts and parts[0].isdigit():
        return int(parts[0])
    return None


def parse_diary_entry(page: dict[str, Any]) -> dict[str, Any] | None:
    """Parse a Notion page into a diary entry dict.

    Returns None if the page has no Date property (skip invalid entries).
    """
    props = page.get("properties", {})

    # Date
    date_prop = props.get("Date", {})
    date_val = date_prop.get("date")
    if not date_val or not date_val.get("start"):
        return None
    date_str = date_val["start"]

    # Stress (select — name starts with the numeric level, e.g. "3 (Moderate)")
    stress_prop = props.get("Stress", {})
    stress = _parse_stress_select(stress_prop.get("select"))

    # Niggles (rich_text)
    niggles_prop = props.get("Niggles", {})
    niggles_parts = niggles_prop.get("rich_text", [])
    niggles = "".join(part.get("plain_text", "") for part in niggles_parts) if niggles_parts else None

    # Notes (rich_text)
    notes_prop = props.get("Notes", {})
    notes_parts = notes_prop.get("rich_text", [])
    notes = "".join(part.get("plain_text", "") for part in notes_parts) if notes_parts else None

    # page_id for deduplication
    page_id = page.get("id", "")
    last_edited = page.get("last_edited_time", "")

    return {
        "page_id": page_id,
        "last_edited": last_edited,
        "date": date_str,
        "stress": stress,
        "niggles": niggles,
        "notes": notes,
    }
