"""Unit tests for claim_store.query_claims."""

from __future__ import annotations

import json
import sqlite3

import pytest

from pace_ai.resources.claim_store import query_claims


@pytest.fixture()
def claims_db(tmp_path):
    """Create a test claims database with known data."""
    db_path = str(tmp_path / "test_claims.db")
    conn = sqlite3.connect(db_path)
    conn.executescript("""
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
    """)

    # Insert test papers
    conn.execute(
        "INSERT INTO papers VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ("paper_a", "Paper A", json.dumps(["Author A"]), 2020, "Journal A", None, None, "rct", "training_load"),
    )
    conn.execute(
        "INSERT INTO papers VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ("paper_b", "Paper B", json.dumps(["Author B"]), 2021, "Journal B", None, None, "meta", "injury"),
    )

    # Insert test claims with varied populations and confidences
    test_claims = [
        # Exact population match candidates
        ("paper_a", "ACWR 0.8-1.3 is optimal", "0.8-1.3", "training_load", "recreational runners", 0.9),
        ("paper_a", "10% rule is a guideline", "10%", "training_load", "recreational runners", 0.7),
        # Population 'all' candidates
        ("paper_a", "Progressive overload drives adaptation", None, "training_load", "all", 0.85),
        ("paper_b", "Load spikes increase injury risk", None, "training_load", "all", 0.8),
        # Different population (should rank lower)
        ("paper_a", "Elite athletes tolerate higher loads", None, "training_load", "elite athletes", 0.95),
        ("paper_b", "Youth need more recovery", None, "training_load", "youth athletes", 0.75),
        # Different category (should not appear in training_load queries)
        ("paper_b", "Stretching prevents injury", None, "injury", "recreational runners", 0.6),
        ("paper_b", "Ice baths reduce inflammation", None, "injury", "all", 0.7),
    ]
    for paper_id, text, specific_value, category, population, confidence in test_claims:
        conn.execute(
            "INSERT INTO claims (paper_id, text, specific_value, category, population, confidence)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (paper_id, text, specific_value, category, population, confidence),
        )

    conn.commit()
    conn.close()
    return db_path


class TestPopulationScoring:
    def test_exact_population_ranks_above_all(self, claims_db):
        """Claims matching population exactly should score higher than 'all' claims."""
        results = query_claims("training_load", "recreational runners", db_path=claims_db)
        # Exact match: 1.0 * confidence vs 'all': 0.7 * confidence
        # "ACWR 0.8-1.3 is optimal" (exact, conf=0.9) → score 0.9
        # "Progressive overload" (all, conf=0.85) → score 0.595
        assert len(results) > 0
        exact_matches = [r for r in results if r["population"] == "recreational runners"]
        all_matches = [r for r in results if r["population"] == "all"]
        assert len(exact_matches) > 0
        assert len(all_matches) > 0
        # Best exact match should have higher score than best 'all' match
        assert exact_matches[0]["score"] > all_matches[0]["score"]

    def test_exact_population_score_is_confidence(self, claims_db):
        """Exact population match should have score = 1.0 * confidence."""
        results = query_claims("training_load", "recreational runners", db_path=claims_db)
        exact = [r for r in results if r["population"] == "recreational runners"]
        for r in exact:
            assert r["score"] == pytest.approx(1.0 * r["confidence"])

    def test_all_population_score_is_0_7_times_confidence(self, claims_db):
        """Population 'all' should have score = 0.7 * confidence."""
        results = query_claims("training_load", "recreational runners", db_path=claims_db)
        all_pop = [r for r in results if r["population"] == "all"]
        for r in all_pop:
            assert r["score"] == pytest.approx(0.7 * r["confidence"])

    def test_other_population_score_is_0_5_times_confidence(self, claims_db):
        """Non-matching populations should have score = 0.5 * confidence."""
        results = query_claims("training_load", "recreational runners", db_path=claims_db)
        other = [r for r in results if r["population"] not in ("recreational runners", "all")]
        for r in other:
            assert r["score"] == pytest.approx(0.5 * r["confidence"])


class TestConfidenceOrdering:
    def test_results_sorted_by_score_descending(self, claims_db):
        """Results should be sorted by score (population_weight * confidence) descending."""
        results = query_claims("training_load", "recreational runners", db_path=claims_db)
        scores = [r["score"] for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_higher_confidence_ranks_higher_within_same_population(self, claims_db):
        """Within same population tier, higher confidence should rank higher."""
        results = query_claims("training_load", "recreational runners", db_path=claims_db)
        exact = [r for r in results if r["population"] == "recreational runners"]
        confidences = [r["confidence"] for r in exact]
        assert confidences == sorted(confidences, reverse=True)


class TestCategoryFiltering:
    def test_single_category(self, claims_db):
        """Should only return claims matching the queried category."""
        results = query_claims("training_load", "recreational runners", db_path=claims_db)
        assert all(r["category"] == "training_load" for r in results)
        assert len(results) == 6  # all training_load claims

    def test_multiple_categories(self, claims_db):
        """Should return claims from all queried categories."""
        results = query_claims(["training_load", "injury"], "recreational runners", db_path=claims_db)
        categories = {r["category"] for r in results}
        assert categories == {"training_load", "injury"}

    def test_nonexistent_category(self, claims_db):
        """Should return empty list for a category with no claims."""
        results = query_claims("nonexistent_category", "recreational runners", db_path=claims_db)
        assert results == []


class TestEmptyResults:
    def test_empty_db(self, tmp_path):
        """Should return empty list when database has no claims."""
        db_path = str(tmp_path / "empty.db")
        conn = sqlite3.connect(db_path)
        conn.executescript("""
            CREATE TABLE papers (
                id TEXT PRIMARY KEY, title TEXT NOT NULL, authors TEXT NOT NULL,
                year INTEGER, journal TEXT, doi TEXT, pubmed_id TEXT,
                study_type TEXT, domain_id TEXT NOT NULL
            );
            CREATE TABLE claims (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                paper_id TEXT NOT NULL, text TEXT NOT NULL, specific_value TEXT,
                category TEXT NOT NULL, population TEXT NOT NULL,
                confidence REAL NOT NULL, created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
        """)
        conn.commit()
        conn.close()
        results = query_claims("training_load", "recreational runners", db_path=db_path)
        assert results == []

    def test_no_matching_category(self, claims_db):
        """Should return empty list when no claims match the category."""
        results = query_claims("nonexistent", "all", db_path=claims_db)
        assert results == []


class TestLimit:
    def test_limit_respected(self, claims_db):
        """Should return at most `limit` results."""
        results = query_claims("training_load", "recreational runners", limit=2, db_path=claims_db)
        assert len(results) <= 2

    def test_default_limit(self, claims_db):
        """Default limit of 20 should work without specifying."""
        results = query_claims("training_load", "recreational runners", db_path=claims_db)
        assert len(results) <= 20


class TestReturnStructure:
    def test_result_dict_keys(self, claims_db):
        """Each result should contain the required keys."""
        results = query_claims("training_load", "recreational runners", db_path=claims_db)
        required_keys = {"text", "specific_value", "category", "population", "confidence", "paper_id", "score"}
        for r in results:
            assert set(r.keys()) == required_keys

    def test_specific_value_can_be_none(self, claims_db):
        """specific_value should be None when not available."""
        results = query_claims("training_load", "recreational runners", db_path=claims_db)
        none_values = [r for r in results if r["specific_value"] is None]
        assert len(none_values) > 0
