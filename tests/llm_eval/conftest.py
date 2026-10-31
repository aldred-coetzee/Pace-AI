"""Pytest configuration for LLM evaluation tests.

Flags (--live-llm, --gen-model, --judge-model) are registered in the repo-root
conftest.py, because pytest only honours addoption from a conftest it loads at
startup, which a nested one is not when running from the root.

Flags:
- --live-llm: use real API calls instead of golden responses
- --gen-model: model for generating coaching responses
- --judge-model: model for judging response quality

Environment variable fallbacks:
- EVAL_GEN_MODEL  (default: the model the app uses for PLAN, ui.llm.model_for("plan"))
- EVAL_JUDGE_MODEL (default: haiku)

Models are Claude Code aliases (haiku, sonnet, opus) or full ids; every call
goes through `claude -p`.
"""

from __future__ import annotations

import os

import pytest

from ui.llm import model_for

# ── Defaults ────────────────────────────────────────────────────────

DEFAULT_JUDGE_MODEL = "haiku"  # also the --judge-model help text in the root conftest.py


def default_gen_model() -> str:
    """The model the app itself uses for the PLAN agent."""
    return model_for("plan")


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
    return os.environ.get("EVAL_GEN_MODEL") or default_gen_model()


@pytest.fixture()
def judge_model(request: pytest.FixtureRequest) -> str:
    """Resolved judge model: --judge-model > EVAL_JUDGE_MODEL > default."""
    explicit = request.config.getoption("--judge-model")
    if explicit:
        return explicit
    return os.environ.get("EVAL_JUDGE_MODEL", DEFAULT_JUDGE_MODEL)
