"""Integration tests for pace-ai server tools."""

from __future__ import annotations

import pytest

from pace_ai.config import Settings
from pace_ai.database import GoalDB


@pytest.fixture()
def _wired(tmp_path, monkeypatch):
    """Wire up server module globals with test instances."""
    import pace_ai.server as srv

    db = str(tmp_path / "integration.db")
    settings = Settings(db_path=db)
    monkeypatch.setattr(srv, "settings", settings)
    monkeypatch.setattr(srv, "goal_db", GoalDB(db))


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
        assert "Progressive overload" in result
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
