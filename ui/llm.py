"""Thin LLM helper — OpenRouter in cloud, claude -p locally as fallback."""

from __future__ import annotations

import logging
import os
import subprocess

from openai import OpenAI

log = logging.getLogger(__name__)

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.environ["OPENROUTER_API_KEY"],
        )
    return _client


def _call_claude_cli(system_prompt: str, user_prompt: str, timeout: int) -> str:
    """Fall back to local claude -p subprocess (uses Claude subscription)."""
    cmd = ["claude", "-p", "--dangerously-skip-permissions"]
    if system_prompt:
        cmd.extend(["--system-prompt", system_prompt])
    try:
        result = subprocess.run(
            cmd,
            input=user_prompt,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return result.stdout.strip() or result.stderr.strip() or "(no response)"
    except subprocess.TimeoutExpired:
        log.exception("claude -p timed out")
        return "(timeout — Claude took too long)"
    except Exception as e:
        log.exception("claude -p failed")
        return f"(error: {e})"


def call_llm(system_prompt: str, user_prompt: str, timeout: int = 300) -> str:
    """Call LLM. Uses OpenRouter if OPENROUTER_API_KEY is set, else claude -p."""
    if not os.environ.get("OPENROUTER_API_KEY"):
        log.info("OPENROUTER_API_KEY not set — falling back to claude -p")
        return _call_claude_cli(system_prompt, user_prompt, timeout)

    model = os.environ.get("LLM_MODEL", "google/gemini-2.5-flash")
    try:
        response = _get_client().chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            timeout=timeout,
        )
        return response.choices[0].message.content or "(no response)"
    except Exception as e:
        log.exception("LLM call failed")
        return f"(error: {e})"
