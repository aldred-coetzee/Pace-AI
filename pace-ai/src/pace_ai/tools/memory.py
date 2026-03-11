"""Coaching memory tools — persistent memory across coaching conversations.

Claude's session pattern:

START OF SESSION:
1. get_coaching_context()          — what's relevant right now
2. get_recent_coaching_log(5)      — what happened recently
3. sync_all()                      — fresh data from all sources
4. get_athlete_facts()             — permanent context

END OF SESSION:
1. append_coaching_log(...)        — record what happened
2. update_coaching_context(...)    — rewrite active context
3. add_athlete_fact(...) if needed — any new permanent insights
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pace_ai.database import HistoryDB

_VALID_CATEGORIES = {"injury", "training_response", "goal", "preference", "other"}
_MAX_CONTEXT_WORDS = 2000


def append_coaching_log(db: HistoryDB, entry: dict[str, Any]) -> dict[str, Any]:
    """Append a coaching log entry.

    Args:
        db: HistoryDB instance.
        entry: Dict with required 'summary' and optional: prescriptions (list),
            workout_ids (list), acwr, weekly_km, body_battery, stress_level,
            notion_stress, notion_niggles, follow_up.

    Returns:
        The new log entry dict with id and created_at.

    Raises:
        ValueError: If summary is missing or empty.
    """
    if not entry.get("summary"):
        msg = "summary is required and cannot be empty"
        raise ValueError(msg)
    return db.append_coaching_log(entry)


def get_coaching_context(db: HistoryDB) -> dict[str, Any] | None:
    """Return current coaching context, or None if not yet set."""
    return db.get_coaching_context()


def update_coaching_context(db: HistoryDB, content: str) -> dict[str, Any]:
    """Rewrite the coaching context.

    Args:
        db: HistoryDB instance.
        content: Rich text content for the coaching context.

    Returns:
        Updated context dict with updated_at.

    Raises:
        ValueError: If content exceeds 2000 words.
    """
    word_count = len(content.split())
    if word_count > _MAX_CONTEXT_WORDS:
        msg = f"Coaching context exceeds {_MAX_CONTEXT_WORDS} word limit ({word_count} words). Trim before saving."
        raise ValueError(msg)
    return db.update_coaching_context(content)


def search_coaching_log(db: HistoryDB, query: str, limit: int = 10) -> list[dict[str, Any]]:
    """Search coaching log by text match across summary and prescriptions.

    Args:
        db: HistoryDB instance.
        query: Search term (e.g. "eccentric heel drops", "achilles", "long run").
        limit: Max results (default 10).

    Returns:
        Matching log entries ordered by date desc.
    """
    return db.search_coaching_log(query, limit)


def get_recent_coaching_log(db: HistoryDB, limit: int = 5) -> list[dict[str, Any]]:
    """Return last N coaching log entries ordered by date desc.

    Args:
        db: HistoryDB instance.
        limit: Number of entries to return (default 5).
    """
    return db.get_recent_coaching_log(limit)


def add_athlete_fact(db: HistoryDB, category: str, fact: str, source_log_id: int | None = None) -> dict[str, Any]:
    """Add a permanent fact about the athlete.

    Args:
        db: HistoryDB instance.
        category: One of 'injury', 'training_response', 'goal', 'preference', 'other'.
        fact: Plain text description of the fact.
        source_log_id: Optional coaching_log id this fact came from.

    Returns:
        The new fact dict with id.

    Raises:
        ValueError: If category is not valid.
    """
    if category not in _VALID_CATEGORIES:
        msg = f"Invalid category '{category}'. Must be one of: {sorted(_VALID_CATEGORIES)}"
        raise ValueError(msg)
    source = str(source_log_id) if source_log_id is not None else None
    return db.add_athlete_fact(category, fact, source)


def get_athlete_facts(db: HistoryDB, category: str | None = None) -> list[dict[str, Any]]:
    """Return all active athlete facts, optionally filtered by category.

    Args:
        db: HistoryDB instance.
        category: Optional filter — one of 'injury', 'training_response', 'goal', 'preference', 'other'.
    """
    if category and category not in _VALID_CATEGORIES:
        msg = f"Invalid category '{category}'. Must be one of: {sorted(_VALID_CATEGORIES)}"
        raise ValueError(msg)
    return db.get_athlete_facts(category)


def update_athlete_fact(db: HistoryDB, fact_id: int, fact: str) -> dict[str, Any] | None:
    """Update an athlete fact's text.

    Args:
        db: HistoryDB instance.
        fact_id: ID of the fact to update.
        fact: New text for the fact.

    Returns:
        Updated fact dict, or None if not found.
    """
    return db.update_athlete_fact(fact_id, fact)
