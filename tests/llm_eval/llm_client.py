"""Thin LLM client abstraction supporting OpenRouter and Anthropic backends.

Resolution order:
1. OPENROUTER_API_KEY → uses OpenAI SDK with OpenRouter base URL
2. ANTHROPIC_API_KEY  → uses Anthropic SDK directly

Model names are mapped automatically (e.g. "claude-haiku-4-5-20251001"
becomes "anthropic/claude-haiku-4-5-20251001" for OpenRouter).
"""

from __future__ import annotations

import os


def _get_backend() -> str:
    """Determine which backend to use based on available env vars."""
    if os.environ.get("OPENROUTER_API_KEY"):
        return "openrouter"
    if os.environ.get("ANTHROPIC_API_KEY"):
        return "anthropic"
    msg = "Set OPENROUTER_API_KEY or ANTHROPIC_API_KEY to use LLM eval features."
    raise RuntimeError(msg)


async def complete(model: str, prompt: str, max_tokens: int = 4096) -> str:
    """Send a single-turn prompt and return the text response.

    Works with either OpenRouter or the Anthropic API, selected
    automatically based on which environment variable is set.
    """
    backend = _get_backend()

    if backend == "openrouter":
        return await _complete_openrouter(model, prompt, max_tokens)
    return await _complete_anthropic(model, prompt, max_tokens)


async def _complete_openrouter(model: str, prompt: str, max_tokens: int) -> str:
    from openai import AsyncOpenAI

    client = AsyncOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ["OPENROUTER_API_KEY"],
    )

    # OpenRouter expects provider-prefixed model names
    or_model = model if "/" in model else f"anthropic/{model}"

    response = await client.chat.completions.create(
        model=or_model,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content


async def _complete_anthropic(model: str, prompt: str, max_tokens: int) -> str:
    import anthropic

    client = anthropic.AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    response = await client.messages.create(
        model=model,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text
