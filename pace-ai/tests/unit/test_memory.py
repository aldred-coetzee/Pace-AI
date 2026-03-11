"""Unit tests for coaching memory tools."""

from __future__ import annotations

import pytest

from pace_ai.tools.memory import (
    add_athlete_fact,
    append_coaching_log,
    get_athlete_facts,
    get_coaching_context,
    get_recent_coaching_log,
    search_coaching_log,
    update_athlete_fact,
    update_coaching_context,
)


class TestAppendCoachingLog:
    def test_basic_append(self, history_db):
        result = append_coaching_log(history_db, {"summary": "First coaching session"})
        assert result["id"] == 1
        assert result["summary"] == "First coaching session"
        assert result["created_at"] is not None

    def test_full_entry(self, history_db):
        result = append_coaching_log(
            history_db,
            {
                "summary": "Return to running check-in",
                "prescriptions": ["eccentric heel drops 3x15", "easy run 20min"],
                "workout_ids": ["WK001", "WK002"],
                "acwr": 0.8,
                "weekly_km": 12.5,
                "body_battery": 75,
                "stress_level": 30,
                "notion_stress": 2,
                "notion_niggles": "slight achilles tightness",
                "follow_up": "Check achilles response after 3 runs",
            },
        )
        assert result["acwr"] == 0.8
        assert "eccentric" in result["prescriptions"]
        assert "WK001" in result["workout_ids"]
        assert result["follow_up"] == "Check achilles response after 3 runs"

    def test_summary_required(self, history_db):
        with pytest.raises(ValueError, match="summary is required"):
            append_coaching_log(history_db, {})

    def test_empty_summary_rejected(self, history_db):
        with pytest.raises(ValueError, match="summary is required"):
            append_coaching_log(history_db, {"summary": ""})

    def test_multiple_appends(self, history_db):
        append_coaching_log(history_db, {"summary": "Session 1"})
        append_coaching_log(history_db, {"summary": "Session 2"})
        append_coaching_log(history_db, {"summary": "Session 3"})
        logs = get_recent_coaching_log(history_db, limit=10)
        assert len(logs) == 3


class TestGetRecentCoachingLog:
    def test_empty_log(self, history_db):
        result = get_recent_coaching_log(history_db)
        assert result == []

    def test_respects_limit(self, history_db):
        for i in range(10):
            append_coaching_log(history_db, {"summary": f"Session {i}"})
        result = get_recent_coaching_log(history_db, limit=3)
        assert len(result) == 3

    def test_ordered_desc(self, history_db):
        append_coaching_log(history_db, {"summary": "First"})
        append_coaching_log(history_db, {"summary": "Second"})
        result = get_recent_coaching_log(history_db, limit=5)
        assert result[0]["summary"] == "Second"
        assert result[1]["summary"] == "First"


class TestSearchCoachingLog:
    def test_search_by_summary(self, history_db):
        append_coaching_log(history_db, {"summary": "Discussed achilles recovery protocol"})
        append_coaching_log(history_db, {"summary": "Weekly mileage review"})
        result = search_coaching_log(history_db, "achilles")
        assert len(result) == 1
        assert "achilles" in result[0]["summary"]

    def test_search_by_prescriptions(self, history_db):
        append_coaching_log(
            history_db,
            {"summary": "Rehab session", "prescriptions": ["eccentric heel drops 3x15"]},
        )
        result = search_coaching_log(history_db, "heel drops")
        assert len(result) == 1

    def test_search_no_results(self, history_db):
        append_coaching_log(history_db, {"summary": "Easy run discussion"})
        result = search_coaching_log(history_db, "marathon")
        assert result == []

    def test_search_case_insensitive(self, history_db):
        append_coaching_log(history_db, {"summary": "Achilles tendinopathy management"})
        result = search_coaching_log(history_db, "achilles")
        assert len(result) == 1


class TestCoachingContext:
    def test_empty_context(self, history_db):
        assert get_coaching_context(history_db) is None

    def test_set_and_get(self, history_db):
        update_coaching_context(history_db, "Currently in return-to-running phase.")
        ctx = get_coaching_context(history_db)
        assert ctx is not None
        assert ctx["content"] == "Currently in return-to-running phase."
        assert ctx["updated_at"] is not None

    def test_overwrite(self, history_db):
        update_coaching_context(history_db, "Phase 1")
        update_coaching_context(history_db, "Phase 2")
        ctx = get_coaching_context(history_db)
        assert ctx["content"] == "Phase 2"

    def test_word_limit(self, history_db):
        long_content = " ".join(["word"] * 2001)
        with pytest.raises(ValueError, match="2000 word limit"):
            update_coaching_context(history_db, long_content)

    def test_at_word_limit(self, history_db):
        content = " ".join(["word"] * 2000)
        result = update_coaching_context(history_db, content)
        assert result["updated_at"] is not None


class TestAthleteFacts:
    def test_add_fact(self, history_db):
        result = add_athlete_fact(history_db, "injury", "Achilles tendinopathy since July 2025")
        assert result["id"] == 1
        assert result["category"] == "injury"
        assert result["fact"] == "Achilles tendinopathy since July 2025"
        assert result["active"] == 1

    def test_add_with_source(self, history_db):
        log = append_coaching_log(history_db, {"summary": "Discovered achilles issue"})
        fact = add_athlete_fact(history_db, "injury", "Achilles pain", source_log_id=log["id"])
        assert fact["source"] == str(log["id"])

    def test_invalid_category(self, history_db):
        with pytest.raises(ValueError, match="Invalid category"):
            add_athlete_fact(history_db, "bogus", "some fact")

    def test_get_all_facts(self, history_db):
        add_athlete_fact(history_db, "injury", "Achilles tendinopathy")
        add_athlete_fact(history_db, "preference", "Prefers Saturday long runs")
        add_athlete_fact(history_db, "training_response", "Responds well to polarized training")
        facts = get_athlete_facts(history_db)
        assert len(facts) == 3

    def test_get_by_category(self, history_db):
        add_athlete_fact(history_db, "injury", "Achilles tendinopathy")
        add_athlete_fact(history_db, "preference", "Prefers Saturday long runs")
        facts = get_athlete_facts(history_db, category="injury")
        assert len(facts) == 1
        assert facts[0]["category"] == "injury"

    def test_invalid_category_filter(self, history_db):
        with pytest.raises(ValueError, match="Invalid category"):
            get_athlete_facts(history_db, category="bogus")

    def test_update_fact(self, history_db):
        fact = add_athlete_fact(history_db, "injury", "Achilles — unresolved")
        updated = update_athlete_fact(history_db, fact["id"], "Achilles — resolving")
        assert updated["fact"] == "Achilles — resolving"
        assert updated["id"] == fact["id"]

    def test_update_nonexistent(self, history_db):
        result = update_athlete_fact(history_db, 999, "doesn't exist")
        assert result is None

    def test_deactivated_facts_excluded(self, history_db):
        fact = add_athlete_fact(history_db, "injury", "Old injury")
        history_db.deactivate_athlete_fact(fact["id"])
        facts = get_athlete_facts(history_db)
        assert len(facts) == 0

    def test_ordered_by_category_then_date(self, history_db):
        add_athlete_fact(history_db, "preference", "Saturday long runs")
        add_athlete_fact(history_db, "injury", "Achilles")
        add_athlete_fact(history_db, "goal", "Sub-1:40 half marathon")
        facts = get_athlete_facts(history_db)
        categories = [f["category"] for f in facts]
        assert categories == sorted(categories)
