"""Pytest configuration for LLM evaluation tests.

Adds flags to control:
- --live-llm: use real API calls instead of golden responses
- --gen-model: model for generating coaching responses
- --judge-model: model for judging response quality

Environment variable fallbacks:
- EVAL_GEN_MODEL  (default: qwen/qwen3-235b-a22b)
- EVAL_JUDGE_MODEL (default: claude-haiku-4-5-20251001)
"""

from __future__ import annotations

import os

import pytest

# ── Defaults ────────────────────────────────────────────────────────

DEFAULT_GEN_MODEL = "qwen/qwen3-235b-a22b"
DEFAULT_JUDGE_MODEL = "google/gemini-2.0-flash-001"


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add LLM eval flags to pytest."""
    parser.addoption(
        "--live-llm",
        action="store_true",
        default=False,
        help="Run LLM evaluation with real API calls instead of mocked golden responses.",
    )
    parser.addoption(
        "--gen-model",
        default=None,
        help=f"Model for generating coaching responses (default: ${DEFAULT_GEN_MODEL}, env: EVAL_GEN_MODEL).",
    )
    parser.addoption(
        "--judge-model",
        default=None,
        help=f"Model for judging response quality (default: ${DEFAULT_JUDGE_MODEL}, env: EVAL_JUDGE_MODEL).",
    )


@pytest.fixture()
def live_llm(request: pytest.FixtureRequest) -> bool:
    """Whether to use live LLM calls."""
    return bool(request.config.getoption("--live-llm"))


@pytest.fixture()
def gen_model(request: pytest.FixtureRequest) -> str:
    """Resolved generation model: --gen-model > EVAL_GEN_MODEL > default."""
    explicit = request.config.getoption("--gen-model")
    if explicit:
        return explicit
    return os.environ.get("EVAL_GEN_MODEL", DEFAULT_GEN_MODEL)


@pytest.fixture()
def judge_model(request: pytest.FixtureRequest) -> str:
    """Resolved judge model: --judge-model > EVAL_JUDGE_MODEL > default."""
    explicit = request.config.getoption("--judge-model")
    if explicit:
        return explicit
    return os.environ.get("EVAL_JUDGE_MODEL", DEFAULT_JUDGE_MODEL)
