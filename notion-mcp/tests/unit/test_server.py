"""Unit tests for server module."""

from __future__ import annotations


class TestMainSignature:
    def test_main_is_callable(self):
        from notion_mcp.server import main

        assert callable(main)
