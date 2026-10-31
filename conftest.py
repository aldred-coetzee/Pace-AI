"""Root pytest configuration: options for the opt-in LLM eval (tests/llm_eval).

Registered here, not in tests/llm_eval/conftest.py: a nested conftest is not
loaded until collection, so `pytest --live-llm` from the repo root would fail
with "unrecognized arguments".
"""

from __future__ import annotations

import pytest  # noqa: TC002  (used in the annotation, which is lazy)

DEFAULT_JUDGE_MODEL = "haiku"


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
        help="Model for generating coaching responses (default: the app's PLAN model, env: EVAL_GEN_MODEL).",
    )
    parser.addoption(
        "--judge-model",
        default=None,
        help=f"Model for judging response quality (default: {DEFAULT_JUDGE_MODEL}, env: EVAL_JUDGE_MODEL).",
    )
