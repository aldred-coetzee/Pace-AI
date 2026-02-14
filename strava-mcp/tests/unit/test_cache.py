"""Unit tests for cache module."""

from __future__ import annotations

import time
from unittest.mock import patch

from strava_mcp.cache import ActivityCache


class TestActivityCache:
    def test_set_and_get(self, cache):
        cache.set("key1", {"data": "value"})
        result = cache.get("key1")
        assert result == {"data": "value"}

    def test_get_missing_key(self, cache):
        assert cache.get("nonexistent") is None

    def test_get_expired(self, tmp_path):
        db = str(tmp_path / "test.db")
        short_cache = ActivityCache(db, ttl=1)
        short_cache.set("key1", {"data": "value"})

        with patch("strava_mcp.cache.time") as mock_time:
            # First call for set used real time, now simulate 2 seconds later
            mock_time.time.return_value = time.time() + 2
            assert short_cache.get("key1") is None

    def test_overwrite(self, cache):
        cache.set("key1", {"v": 1})
        cache.set("key1", {"v": 2})
        assert cache.get("key1") == {"v": 2}

    def test_delete(self, cache):
        cache.set("key1", {"data": "value"})
        cache.delete("key1")
        assert cache.get("key1") is None

    def test_clear(self, cache):
        cache.set("key1", {"a": 1})
        cache.set("key2", {"b": 2})
        cache.clear()
        assert cache.get("key1") is None
        assert cache.get("key2") is None

    def test_clear_expired(self, tmp_path):
        db = str(tmp_path / "test.db")
        short_cache = ActivityCache(db, ttl=1)
        short_cache.set("old", {"data": "old"})

        with patch("strava_mcp.cache.time") as mock_time:
            mock_time.time.return_value = time.time() + 2
            count = short_cache.clear_expired()
            assert count == 1

    def test_stores_complex_data(self, cache):
        data = {
            "activities": [{"id": 1, "name": "Run"}, {"id": 2, "name": "Ride"}],
            "count": 2,
            "nested": {"a": {"b": [1, 2, 3]}},
        }
        cache.set("complex", data)
        assert cache.get("complex") == data

    def test_stores_list(self, cache):
        data = [1, 2, 3, "four"]
        cache.set("list", data)
        assert cache.get("list") == data
