"""Pytest configuration for LLM evaluation tests.

Adds a --live-llm flag to control whether tests use mocked golden responses
or call a real LLM and score with an LLM judge.
"""

from __future__ import annotations

import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add --live-llm flag to pytest."""
    parser.addoption(
        "--live-llm",
        action="store_true",
        default=False,
        help="Run LLM evaluation with real API calls instead of mocked golden responses.",
    )


@pytest.fixture()
def live_llm(request: pytest.FixtureRequest) -> bool:
    """Whether to use live LLM calls."""
    return bool(request.config.getoption("--live-llm"))
