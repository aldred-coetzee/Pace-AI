"""Integration tests for pace-ai server tools."""

from __future__ import annotations

import pytest

from pace_ai.config import Settings
from pace_ai.database import GoalDB, HistoryDB


@pytest.fixture()
def _wired(tmp_path, monkeypatch):
    """Wire up server module globals with test instances."""
    import pace_ai.server as srv

    db = str(tmp_path / "integration.db")
    settings = Settings(db_path=db)
    monkeypatch.setattr(srv, "settings", settings)
    monkeypatch.setattr(srv, "goal_db", GoalDB(db))
    monkeypatch.setattr(srv, "history_db", HistoryDB(db))


@pytest.mark.usefixtures("_wired")
class TestGoalLifecycle:
    @pytest.mark.asyncio()
    async def test_full_crud(self):
        from pace_ai.server import delete_goal, get_goals, set_goal, update_goal

        # Create
        goal = await set_goal("5k", "22:00", race_date="2025-03-01", notes="Park Run")
        assert goal["race_type"] == "5k"
        assert goal["target_time_formatted"] == "22:00"
        goal_id = goal["id"]

        # Read
        goals = await get_goals()
        assert len(goals) == 1
        assert goals[0]["id"] == goal_id

        # Update
        updated = await update_goal(goal_id, target_time="21:30")
        assert updated["target_time_seconds"] == 1290

        # Delete
        result = await delete_goal(goal_id)
        assert "deleted" in result

        # Verify empty
        goals = await get_goals()
        assert len(goals) == 0


@pytest.mark.usefixtures("_wired")
class TestAnalysisTools:
    @pytest.mark.asyncio()
    async def test_analyze_training_load(self):
        from pace_ai.server import analyze_training_load

        result = await analyze_training_load([30, 35, 32, 38, 36])
        assert "acwr" in result
        assert "risk_level" in result
        assert result["risk_level"] == "optimal"
        assert "load_variability_cv" in result

    @pytest.mark.asyncio()
    async def test_predict_race_time(self):
        from pace_ai.server import predict_race_time

        result = await predict_race_time("5k", "22:00", "half marathon")
        assert "predicted_time" in result
        assert result["vdot"] > 0

    @pytest.mark.asyncio()
    async def test_calculate_training_zones(self):
        from pace_ai.server import calculate_training_zones

        result = await calculate_training_zones(threshold_pace_per_km="4:30", threshold_hr=175)
        assert "zones" in result
        assert "easy" in result["zones"]
        assert "threshold" in result["zones"]

    @pytest.mark.asyncio()
    async def test_calculate_training_zones_from_vdot(self):
        from pace_ai.server import calculate_training_zones

        result = await calculate_training_zones(vdot=50)
        assert "zones" in result
        assert len(result["zones"]) == 5
        assert result["reference"]["vdot"] == 50


@pytest.mark.usefixtures("_wired")
class TestPrompts:
    @pytest.mark.asyncio()
    async def test_weekly_plan_prompt(self):
        from pace_ai.server import weekly_plan

        result = await weekly_plan(goals_json='[{"race_type": "5k", "target_time_formatted": "22:00"}]')
        assert "Research Evidence" in result
        assert "progressive overload" in result
        assert "5k" in result

    @pytest.mark.asyncio()
    async def test_run_analysis_prompt(self):
        from pace_ai.server import run_analysis

        result = await run_analysis(
            activity_json='{"name": "Tempo", "type": "Run", "distance": 8000, "moving_time": 2400}',
        )
        assert "Pace consistency" in result

    @pytest.mark.asyncio()
    async def test_race_readiness_prompt(self):
        from pace_ai.server import race_readiness

        result = await race_readiness(goals_json='[{"race_type": "half marathon", "target_time_formatted": "1:30:00"}]')
        assert "Readiness score" in result

    @pytest.mark.asyncio()
    async def test_injury_risk_prompt(self):
        from pace_ai.server import injury_risk

        result = await injury_risk(
            weekly_distances_json="[30, 35, 32, 40]",
            training_load_json='{"acwr": 1.17, "risk_level": "optimal"}',
        )
        assert "10% rule" in result


@pytest.mark.usefixtures("_wired")
class TestSyncLifecycle:
    @pytest.mark.asyncio()
    async def test_sync_strava_and_query(self):
        import json

        from pace_ai.server import get_recent_activities_local, sync_strava
        from tests.conftest import sample_strava_activities

        activities = sample_strava_activities()
        result = await sync_strava(json.dumps(activities))
        assert result["activities_synced"] == 3

        local = await get_recent_activities_local(days=30)
        assert len(local) == 3

    @pytest.mark.asyncio()
    async def test_sync_wellness_and_query(self):
        import json

        from pace_ai.server import get_recent_wellness, sync_garmin_wellness
        from tests.conftest import sample_wellness_data

        result = await sync_garmin_wellness(json.dumps(sample_wellness_data()))
        assert result["records_synced"] == 2

        wellness = await get_recent_wellness(days=7)
        assert len(wellness) == 2

    @pytest.mark.asyncio()
    async def test_sync_status_tracking(self):
        import json

        from pace_ai.server import get_sync_status, sync_garmin_wellness, sync_strava
        from tests.conftest import sample_strava_activities, sample_wellness_data

        await sync_strava(json.dumps(sample_strava_activities()))
        await sync_garmin_wellness(json.dumps(sample_wellness_data()))

        status = await get_sync_status()
        sources = {s["source"] for s in status}
        assert "strava" in sources
        assert "garmin_wellness" in sources

    @pytest.mark.asyncio()
    async def test_sync_notion_and_query(self):
        import json

        from pace_ai.server import get_recent_diary, sync_notion
        from tests.conftest import sample_diary_entries

        result = await sync_notion(json.dumps(sample_diary_entries()))
        assert result["records_synced"] == 2

        diary = await get_recent_diary(days=7)
        assert len(diary) == 2

    @pytest.mark.asyncio()
    async def test_race_history_and_pbs(self):
        import json

        from pace_ai.server import get_pbs, get_race_history, sync_strava
        from tests.conftest import sample_strava_activities

        await sync_strava(json.dumps(sample_strava_activities()))

        races = await get_race_history()
        assert len(races) >= 1

        pbs = await get_pbs()
        assert len(pbs) >= 1


@pytest.mark.usefixtures("_wired")
class TestProfileLifecycle:
    @pytest.mark.asyncio()
    async def test_generate_and_get_profile(self):
        import json

        from pace_ai.server import generate_athlete_profile, get_athlete_profile, sync_strava
        from tests.conftest import sample_strava_activities

        # Empty profile
        profile = await get_athlete_profile()
        assert profile is None

        # Sync data then generate
        await sync_strava(json.dumps(sample_strava_activities()))
        profile = await generate_athlete_profile()
        assert profile is not None
        assert profile["id"] == 1

        # Verify get returns same
        fetched = await get_athlete_profile()
        assert fetched["id"] == 1

    @pytest.mark.asyncio()
    async def test_update_manual_fields(self):
        import json

        from pace_ai.server import get_athlete_profile, update_athlete_profile_manual

        profile = await update_athlete_profile_manual(json.dumps({"gender": "male", "experience_level": "advanced"}))
        assert profile["gender"] == "male"
        assert profile["experience_level"] == "advanced"

        fetched = await get_athlete_profile()
        assert fetched["gender"] == "male"

    @pytest.mark.asyncio()
    async def test_reject_auto_fields(self):
        import json

        from pace_ai.server import update_athlete_profile_manual

        with pytest.raises(ValueError, match="auto-derived"):
            await update_athlete_profile_manual(json.dumps({"estimated_vdot": 50}))


@pytest.mark.usefixtures("_wired")
class TestWeeklyDistances:
    @pytest.mark.asyncio()
    async def test_get_weekly_distances(self):
        import json

        from pace_ai.server import get_weekly_distances, sync_strava
        from tests.conftest import sample_strava_activities

        await sync_strava(json.dumps(sample_strava_activities()))
        weeks = await get_weekly_distances(weeks=4, sport_type="run")
        assert len(weeks) >= 1
        assert all("distance_km" in w for w in weeks)


@pytest.mark.usefixtures("_wired")
class TestSyncAll:
    @pytest.mark.asyncio()
    async def test_sync_all_tool(self):
        from unittest.mock import AsyncMock, MagicMock, patch

        from pace_ai.server import sync_all
        from tests.conftest import sample_strava_activities

        mock_strava = AsyncMock()
        mock_strava.get_all_activities.return_value = sample_strava_activities()

        mock_garmin = MagicMock()
        mock_garmin.get_body_battery.return_value = None
        mock_garmin.get_sleep.return_value = None
        mock_garmin.get_stress.return_value = None
        mock_garmin.get_resting_hr.return_value = None
        mock_garmin.get_workouts.return_value = []

        mock_withings = MagicMock()
        mock_withings.get_measurements.return_value = []

        mock_notion = AsyncMock()
        mock_notion.fetch_all_entries.return_value = []

        with (
            patch("strava_mcp.client.StravaClient", return_value=mock_strava),
            patch("strava_mcp.config.Settings.from_env", return_value=MagicMock(db_path=":memory:")),
            patch("strava_mcp.auth.TokenStore", return_value=MagicMock()),
            patch("garmin_mcp.client.GarminClient", return_value=mock_garmin),
            patch("garmin_mcp.config.Settings.from_env", return_value=MagicMock()),
            patch("withings_mcp.client.WithingsClient", return_value=mock_withings),
            patch("withings_mcp.config.Settings.from_env", return_value=MagicMock()),
            patch("notion_mcp.client.NotionClient", return_value=mock_notion),
            patch("notion_mcp.config.Settings.from_env", return_value=MagicMock()),
        ):
            result = await sync_all()

        assert "results" in result
        assert result["sources_synced"] >= 3
        assert "strava" in result["results"]


@pytest.mark.usefixtures("_wired")
class TestCoachingMemory:
    @pytest.mark.asyncio()
    async def test_coaching_log_lifecycle(self):
        import json

        from pace_ai.server import append_coaching_log, get_recent_coaching_log, search_coaching_log

        # Append
        entry = json.dumps({"summary": "Discussed achilles recovery", "follow_up": "Check pain after 3 runs"})
        result = await append_coaching_log(entry)
        assert result["id"] == 1
        assert result["summary"] == "Discussed achilles recovery"

        # Recent
        recent = await get_recent_coaching_log(limit=5)
        assert len(recent) == 1

        # Search
        found = await search_coaching_log("achilles")
        assert len(found) == 1
        assert "achilles" in found[0]["summary"]

        # Search no results
        empty = await search_coaching_log("marathon")
        assert empty == []

    @pytest.mark.asyncio()
    async def test_coaching_context_lifecycle(self):
        from pace_ai.server import get_coaching_context, update_coaching_context

        # Empty
        ctx = await get_coaching_context()
        assert ctx is None

        # Set
        result = await update_coaching_context("Return-to-running phase. Achilles managing well.")
        assert result["updated_at"] is not None

        # Get
        ctx = await get_coaching_context()
        assert "Return-to-running" in ctx["content"]

        # Overwrite
        await update_coaching_context("Phase 2: building base mileage.")
        ctx = await get_coaching_context()
        assert "Phase 2" in ctx["content"]

    @pytest.mark.asyncio()
    async def test_context_word_limit(self):
        from pace_ai.server import update_coaching_context

        long_content = " ".join(["word"] * 2001)
        result = await update_coaching_context(long_content)
        assert result["error"] == "word_limit_exceeded"

    @pytest.mark.asyncio()
    async def test_athlete_facts_lifecycle(self):
        from pace_ai.server import add_athlete_fact, get_athlete_facts, update_athlete_fact

        # Add
        fact = await add_athlete_fact("injury", "Achilles tendinopathy since July 2025")
        assert fact["id"] == 1
        assert fact["category"] == "injury"

        # Get all
        facts = await get_athlete_facts()
        assert len(facts) == 1

        # Get by category
        facts = await get_athlete_facts(category="injury")
        assert len(facts) == 1

        # Update
        updated = await update_athlete_fact(fact["id"], "Achilles — resolving")
        assert updated["fact"] == "Achilles — resolving"

        # Invalid category
        result = await add_athlete_fact("bogus", "some fact")
        assert result["error"] == "invalid_category"

        # Not found
        result = await update_athlete_fact(999, "nope")
        assert result["error"] == "not_found"
