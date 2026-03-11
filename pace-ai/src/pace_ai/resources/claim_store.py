"""Claim store — query evidence-backed coaching claims from SQLite.

Provides query_claims() for retrieving scored, ranked claims by category
and population relevance.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[4]
_DEFAULT_DB = str(_PROJECT_ROOT / "research" / "claims.db")


def query_claims(
    category: str | list[str],
    population: str,
    limit: int = 20,
    *,
    db_path: str | None = None,
) -> list[dict]:
    """Query evidence-backed claims by category and population.

    Scoring:
        - Claims matching population exactly: score = 1.0 * confidence
        - Claims with population 'all': score = 0.7 * confidence
        - Other claims in matching categories: score = 0.5 * confidence

    Args:
        category: Single category or list of categories to filter by.
        population: Target population for relevance scoring.
        limit: Maximum number of claims to return (default 20).
        db_path: Override path to claims.db (defaults to research/claims.db).

    Returns:
        List of claim dicts sorted by score descending, each containing:
        text, specific_value, category, population, confidence, paper_id, score.
    """
    db = db_path or _DEFAULT_DB

    categories = [category] if isinstance(category, str) else list(category)
    placeholders = ",".join("?" for _ in categories)

    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row

    try:
        rows = conn.execute(
            f"""
            SELECT
                text,
                specific_value,
                category,
                population,
                confidence,
                paper_id,
                CASE
                    WHEN population = ? THEN 1.0 * confidence
                    WHEN population = 'all' THEN 0.7 * confidence
                    ELSE 0.5 * confidence
                END AS score
            FROM claims
            WHERE category IN ({placeholders})
            ORDER BY score DESC
            LIMIT ?
            """,
            [population, *categories, limit],
        ).fetchall()

        return [
            {
                "text": row["text"],
                "specific_value": row["specific_value"],
                "category": row["category"],
                "population": row["population"],
                "confidence": row["confidence"],
                "paper_id": row["paper_id"],
                "score": row["score"],
            }
            for row in rows
        ]
    finally:
        conn.close()
