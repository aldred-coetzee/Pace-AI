#!/usr/bin/env python3
"""Build claims.db from research JSON files.

Reads domain JSON files (papers) and claim JSON files (claims),
populates a SQLite database at research/claims.db.

Usage:
    python research/build_claims_db.py
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

_BROAD_POPULATIONS = frozenset({
    "general population",
    "all populations",
    "healthy adults",
    "general",
})


def _normalize_population(pop: str) -> str:
    """Normalize broad population descriptors to 'all'."""
    if pop.lower().strip() in _BROAD_POPULATIONS:
        return "all"
    return pop


def build_db(research_dir: Path, db_path: Path) -> None:
    """Build the claims database from research JSON files."""
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=WAL")

    conn.executescript("""
        DROP TABLE IF EXISTS claims;
        DROP TABLE IF EXISTS papers;

        CREATE TABLE papers (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            authors TEXT NOT NULL,
            year INTEGER,
            journal TEXT,
            doi TEXT,
            pubmed_id TEXT,
            study_type TEXT,
            domain_id TEXT NOT NULL
        );

        CREATE TABLE claims (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            paper_id TEXT NOT NULL REFERENCES papers(id),
            text TEXT NOT NULL,
            specific_value TEXT,
            category TEXT NOT NULL,
            population TEXT NOT NULL,
            confidence REAL NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE INDEX idx_claims_category ON claims(category);
        CREATE INDEX idx_claims_population ON claims(population);
        CREATE INDEX idx_claims_paper_id ON claims(paper_id);
    """)

    # Load papers from domain files
    domains_dir = research_dir / "domains"
    paper_count = 0
    for domain_file in sorted(domains_dir.glob("*.json")):
        with open(domain_file) as f:
            domain = json.load(f)
        domain_id = domain["domain_id"]
        for paper in domain.get("papers", []):
            conn.execute(
                """INSERT OR IGNORE INTO papers
                   (id, title, authors, year, journal, doi, pubmed_id, study_type, domain_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    paper["id"],
                    paper["title"],
                    json.dumps(paper.get("authors", [])),
                    paper.get("year"),
                    paper.get("journal"),
                    paper.get("doi"),
                    paper.get("pubmed_id"),
                    paper.get("study_type"),
                    domain_id,
                ),
            )
            paper_count += 1

    # Load claims from claim files
    claims_dir = research_dir / "claims"
    claim_count = 0
    for claim_file in sorted(claims_dir.glob("*.json")):
        paper_id = claim_file.stem
        with open(claim_file) as f:
            claims = json.load(f)
        for claim in claims:
            conn.execute(
                """INSERT INTO claims
                   (paper_id, text, specific_value, category, population, confidence)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    paper_id,
                    claim["text"],
                    claim.get("specific_value"),
                    claim["category"],
                    _normalize_population(claim["population"]),
                    claim["confidence"],
                ),
            )
            claim_count += 1

    conn.commit()

    paper_total = conn.execute("SELECT COUNT(*) FROM papers").fetchone()[0]
    claim_total = conn.execute("SELECT COUNT(*) FROM claims").fetchone()[0]
    all_total = conn.execute("SELECT COUNT(*) FROM claims WHERE population = 'all'").fetchone()[0]
    print(f"Built {db_path}")
    print(f"  Papers: {paper_total} (from {paper_count} inserts across {len(list(domains_dir.glob('*.json')))} domains)")
    print(f"  Claims: {claim_total} ({all_total} with population='all')")

    conn.close()


def main() -> None:
    research_dir = Path(__file__).resolve().parent
    db_path = research_dir / "claims.db"

    if db_path.exists():
        db_path.unlink()

    build_db(research_dir, db_path)


if __name__ == "__main__":
    main()
