"""Unit tests for cache module."""

from __future__ import annotations

from notion_mcp.cache import get_recent_entries, upsert_entries, upsert_entry
from tests.conftest import make_diary_entry


class TestUpsertEntry:
    def test_insert(self, mem_db):
        entry = make_diary_entry()
        upsert_entry(mem_db, entry)
        mem_db.commit()
        rows = mem_db.execute("SELECT * FROM diary_entries").fetchall()
        assert len(rows) == 1
        assert dict(rows[0])["date"] == "2026-03-10"

    def test_upsert_updates_existing(self, mem_db):
        entry = make_diary_entry(notes="Original")
        upsert_entry(mem_db, entry)
        mem_db.commit()

        updated = make_diary_entry(notes="Updated")
        upsert_entry(mem_db, updated)
        mem_db.commit()

        rows = mem_db.execute("SELECT * FROM diary_entries").fetchall()
        assert len(rows) == 1
        assert dict(rows[0])["notes"] == "Updated"


class TestUpsertEntries:
    def test_batch_upsert(self, mem_db):
        entries = [
            make_diary_entry(page_id="p1", date="2026-03-09"),
            make_diary_entry(page_id="p2", date="2026-03-10"),
        ]
        count = upsert_entries(mem_db, entries)
        assert count == 2
        rows = mem_db.execute("SELECT * FROM diary_entries ORDER BY date").fetchall()
        assert len(rows) == 2


class TestGetRecentEntries:
    def test_returns_recent(self, mem_db):
        entries = [
            make_diary_entry(page_id="p1", date="2026-03-10"),
            make_diary_entry(page_id="p2", date="2026-03-05"),
            make_diary_entry(page_id="p3", date="2020-01-01"),  # Very old
        ]
        upsert_entries(mem_db, entries)

        recent = get_recent_entries(mem_db, days=28)
        dates = [e["date"] for e in recent]
        assert "2026-03-10" in dates
        assert "2026-03-05" in dates
        assert "2020-01-01" not in dates

    def test_ordered_descending(self, mem_db):
        entries = [
            make_diary_entry(page_id="p1", date="2026-03-08"),
            make_diary_entry(page_id="p2", date="2026-03-10"),
            make_diary_entry(page_id="p3", date="2026-03-09"),
        ]
        upsert_entries(mem_db, entries)

        recent = get_recent_entries(mem_db, days=28)
        dates = [e["date"] for e in recent]
        assert dates == sorted(dates, reverse=True)

    def test_returns_correct_fields(self, mem_db):
        upsert_entries(mem_db, [make_diary_entry()])
        entries = get_recent_entries(mem_db, days=28)
        assert len(entries) == 1
        e = entries[0]
        assert "date" in e
        assert "stress" in e
        assert "niggles" in e
        assert "notes" in e
        # page_id and last_edited should NOT be in the output
        assert "page_id" not in e
        assert "last_edited" not in e

    def test_empty_db(self, mem_db):
        assert get_recent_entries(mem_db, days=28) == []
