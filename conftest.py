"""Root pytest configuration: options for the opt-in LLM eval (tests/llm_eval).

Registered here, not in tests/llm_eval/conftest.py: a nested conftest is not
loaded until collection, so `pytest --live-llm` from the repo root would fail
with "unrecognized arguments".
"""

from __future__ import annotations

import os
import tempfile

import pytest

DEFAULT_JUDGE_MODEL = "haiku"

# ui.config computes workspace paths at import time, which happens during
# collection, before any fixture runs. Point at a throwaway workspace now so
# even import can never create or touch the real one.
os.environ["PACE_AI_WORKSPACE"] = tempfile.mkdtemp(prefix="pace-ai-test-ws-")


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


@pytest.fixture(autouse=True)
def _isolated_workspace(tmp_path, monkeypatch):
    """Point every test at a throwaway workspace; none may touch the real one."""
    from pace_ai import workspace

    ws = tmp_path / "pace-ai-workspace"
    monkeypatch.setenv("PACE_AI_WORKSPACE", str(ws))
    for var in (
        "PACE_AI_DB",
        "STRAVA_DB",
        "NOTION_DB",
        "GARTH_HOME",
        "WITHINGS_CONFIG_FOLDER",
    ):
        monkeypatch.delenv(var, raising=False)
    workspace._reset_for_tests()
    yield
    workspace._reset_for_tests()
