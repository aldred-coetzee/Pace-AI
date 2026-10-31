"""Thin LLM helper — one headless `claude -p` call per agent, on the box's subscription.

Shape follows plate-and-glass/scripts/ai, plus one thing it lacks:
- an explicit model per agent, the cheapest adequate one, overridable with
  PACE_AI_MODEL_<AGENT> (e.g. PACE_AI_MODEL_PLAN=opus);
- --tools "": every call gets its data in the prompt and needs no tools, so
  no permission bypass is needed;
- disableAllHooks: the global Stop hook fires in headless runs, and the
  model's reply to it can replace the answer;
- --setting-sources project from an empty temp directory: otherwise the
  user's global CLAUDE.md is loaded into every call (measured 2026-10-31:
  22,035 input tokens for "say ok", 557 with this);
- --no-session-persistence: keeps these runs out of ~/.claude/projects, which
  the nightly refresh and the work log read as someone working.
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import tempfile

log = logging.getLogger(__name__)

# Cheapest adequate model per agent. Coaching reasoning gets Sonnet; turning a
# conversation or a plan into JSON gets Haiku.
DEFAULT_MODELS: dict[str, str] = {
    "chat": "sonnet",
    "plan": "sonnet",
    "nutrition": "sonnet",
    "end_session": "haiku",
    "exercise": "haiku",
}


def model_for(agent: str) -> str:
    """Model for an agent: PACE_AI_MODEL_<AGENT> if set, else the default."""
    return os.environ.get(f"PACE_AI_MODEL_{agent.upper()}") or DEFAULT_MODELS.get(agent, "sonnet")


def call_llm(system_prompt: str, user_prompt: str, agent: str, timeout: int = 300, model: str | None = None) -> str:
    """Call Claude headless. Returns the reply text, or a parenthesised error string.

    `model` overrides the per-agent default (the eval suite uses it to sweep models).
    """
    model = model or model_for(agent)
    cmd = [
        "claude",
        "-p",
        "--model",
        model,
        "--tools",
        "",
        "--no-session-persistence",
        "--setting-sources",
        "project",
        "--settings",
        '{"disableAllHooks":true}',
        "--output-format",
        "json",
    ]
    if system_prompt:
        cmd.extend(["--system-prompt", system_prompt])
    log.info("claude -p agent=%s model=%s prompt=%d chars", agent, model, len(user_prompt))
    try:
        with tempfile.TemporaryDirectory(prefix="pace-ai-llm-") as cwd:
            result = subprocess.run(
                cmd,
                check=False,
                input=user_prompt,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=cwd,
            )
    except subprocess.TimeoutExpired:
        log.exception("claude -p timed out (agent=%s)", agent)
        return "(timeout — Claude took too long)"
    except Exception as e:
        log.exception("claude -p failed (agent=%s)", agent)
        return f"(error: {e})"

    try:
        reply = json.loads(result.stdout)
    except json.JSONDecodeError:
        detail = (result.stderr or result.stdout).strip()[:300]
        log.error("claude -p exited %d with no JSON (agent=%s): %s", result.returncode, agent, detail)
        return f"(error: {detail or 'no response'})"
    if reply.get("is_error"):
        log.error("claude -p reported an error (agent=%s): %s", agent, reply.get("result"))
        return f"(error: {reply.get('result') or 'unknown'})"
    return reply.get("result") or "(no response)"
