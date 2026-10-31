"""LLM client for the eval suite: every call goes through `claude -p`.

This is the same path the app uses (`ui.llm.call_llm`), so the eval grades what
the app actually sends, on the box's subscription, with no API keys. Model
names are Claude Code aliases (`haiku`, `sonnet`, `opus`) or full model ids.
"""

from __future__ import annotations

import asyncio

from ui.llm import call_llm

# call_llm reports failures as a parenthesised string; a grader must not score
# those as if they were answers.
_ERROR_PREFIXES = ("(error:", "(timeout", "(no response")


class LLMError(RuntimeError):
    """The `claude -p` call failed (call_llm returns errors as text)."""


async def complete(model: str, prompt: str, system: str = "", timeout: int = 300) -> str:
    """Send a single-turn prompt through `claude -p` and return the reply text."""
    reply = await asyncio.to_thread(call_llm, system, prompt, "eval", timeout, model)
    if reply.startswith(_ERROR_PREFIXES):
        raise LLMError(f"claude -p failed (model={model}): {reply}")
    return reply
