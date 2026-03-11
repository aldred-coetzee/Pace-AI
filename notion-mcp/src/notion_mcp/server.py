"""FastMCP server for Notion running diary."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from notion_mcp.cache import get_recent_entries, init_db, upsert_entries
from notion_mcp.client import NotionAPIError, NotionClient, parse_diary_entry
from notion_mcp.config import Settings

settings = Settings.from_env()
notion = NotionClient(settings)
db = init_db(settings.db_path)

mcp = FastMCP(
    "notion-mcp",
    instructions="MCP server for reading a Notion running diary — stress, niggles, and notes",
    host=settings.host,
    port=settings.port,
)


# ── Tools ──────────────────────────────────────────────────────────────


@mcp.tool()
async def get_diary_entries(days: int = 28) -> dict:
    """Get running diary entries from the last N days.

    Syncs new/updated entries from Notion into the local cache, then returns
    entries ordered by date descending.

    Each entry contains: date, stress (1-5), niggles, notes.

    Args:
        days: Number of days to look back (default 28).
    """
    try:
        # Sync from Notion into SQLite
        pages = await notion.fetch_all_entries()
        parsed = [e for p in pages if (e := parse_diary_entry(p)) is not None]
        synced = upsert_entries(db, parsed) if parsed else 0

        # Read from cache
        entries = get_recent_entries(db, days=days)

        return {
            "days": days,
            "synced": synced,
            "count": len(entries),
            "entries": entries,
        }
    except NotionAPIError as e:
        return e.to_dict()


# ── Resources ──────────────────────────────────────────────────────────


@mcp.resource("notion://diary-fields")
async def diary_fields_resource() -> str:
    """Available fields in each running diary entry."""
    import json

    fields = {
        "date": "Entry date (YYYY-MM-DD)",
        "stress": "Overall stress level (1-5 scale)",
        "niggles": "Physical niggles, aches, or injury notes",
        "notes": "General notes about how the day/run felt",
    }
    return json.dumps(fields, indent=2)


# ── Entry Point ────────────────────────────────────────────────────────


def main() -> None:
    """Entry point for the notion-mcp server."""
    import os

    mcp.run(transport=os.environ.get("MCP_TRANSPORT", "streamable-http"))


if __name__ == "__main__":
    main()
