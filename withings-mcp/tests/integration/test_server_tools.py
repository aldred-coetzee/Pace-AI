"""Integration tests for withings-mcp server tools.

Tests each tool through the actual async function with a mocked WithingsClient.
"""

from __future__ import annotations

import time
from unittest.mock import MagicMock

import pytest

from withings_mcp.client import WithingsAPIError
from withings_mcp.config import Settings


@pytest.fixture()
def _wired(monkeypatch):
    """Wire up server module globals with test instances."""
    import withings_mcp.server as srv

    settings = Settings()
    monkeypatch.setattr(srv, "settings", settings)

    now = int(time.time())
    mock_client = MagicMock()

    # get_measurements returns parsed dicts (the client already parses groups)
    mock_client.get_measurements.return_value = [
        {
            "date": now - 3600,
            "grpid": 1001,
            "datetime": "2026-03-10T08:00:00",
            "weight_kg": 75.5,
            "fat_ratio_pct": 18.2,
            "muscle_mass_kg": 35.1,
            "bone_mass_kg": 3.2,
            "hydration_kg": 40.0,
        },
    ]

    monkeypatch.setattr(srv, "withings", mock_client)
    return mock_client


@pytest.mark.usefixtures("_wired")
class TestAuthenticate:
    @pytest.mark.asyncio()
    async def test_authenticate_success(self, _wired):
        from withings_mcp.server import authenticate

        _wired._ensure_account.return_value = MagicMock()
        result = await authenticate()
        assert result["authenticated"] is True

    @pytest.mark.asyncio()
    async def test_authenticate_failure(self, _wired):
        from withings_mcp.server import authenticate

        _wired._ensure_account.side_effect = WithingsAPIError("auth_failed", "No session", "Re-auth")
        result = await authenticate()
        assert result["error"] == "auth_failed"


@pytest.mark.usefixtures("_wired")
class TestGetMeasurements:
    @pytest.mark.asyncio()
    async def test_get_measurements(self):
        from withings_mcp.server import get_measurements

        result = await get_measurements("2026-03-01", "2026-03-10")
        assert result["count"] == 1
        assert result["measurements"][0]["weight_kg"] == 75.5
        assert result["from_date"] == "2026-03-01"
        assert result["to_date"] == "2026-03-10"

    @pytest.mark.asyncio()
    async def test_get_measurements_api_error(self, _wired):
        from withings_mcp.server import get_measurements

        _wired.get_measurements.side_effect = WithingsAPIError("api_error", "Failed", "Retry")
        result = await get_measurements("2026-03-01", "2026-03-10")
        assert result["error"] == "api_error"


@pytest.mark.usefixtures("_wired")
class TestGetLatestWeight:
    @pytest.mark.asyncio()
    async def test_get_latest_weight(self):
        from withings_mcp.server import get_latest_weight

        result = await get_latest_weight()
        assert result["weight_kg"] == 75.5
        assert "date_str" in result

    @pytest.mark.asyncio()
    async def test_get_latest_weight_no_data(self, _wired):
        from withings_mcp.server import get_latest_weight

        _wired.get_measurements.return_value = []
        result = await get_latest_weight()
        assert "No weight measurements" in result["message"]

    @pytest.mark.asyncio()
    async def test_get_latest_weight_api_error(self, _wired):
        from withings_mcp.server import get_latest_weight

        _wired.get_measurements.side_effect = WithingsAPIError("api_error", "Failed", "Retry")
        result = await get_latest_weight()
        assert result["error"] == "api_error"


@pytest.mark.usefixtures("_wired")
class TestGetBloodPressure:
    @pytest.mark.asyncio()
    async def test_get_blood_pressure(self, _wired):
        from withings_mcp.server import get_blood_pressure

        now = int(time.time())
        _wired.get_measurements.return_value = [
            {
                "date": now - 7200,
                "grpid": 2001,
                "systolic_mmhg": 120.0,
                "diastolic_mmhg": 80.0,
                "heart_pulse_bpm": 65.0,
            },
        ]
        result = await get_blood_pressure("2026-03-01", "2026-03-10")
        assert result["count"] == 1
        assert result["readings"][0]["systolic_mmhg"] == 120.0
        assert result["readings"][0]["diastolic_mmhg"] == 80.0

    @pytest.mark.asyncio()
    async def test_get_blood_pressure_no_bp_data(self):
        from withings_mcp.server import get_blood_pressure

        # Default fixture has weight data, no BP data
        result = await get_blood_pressure("2026-03-01", "2026-03-10")
        assert result["count"] == 0
        assert result["readings"] == []

    @pytest.mark.asyncio()
    async def test_get_blood_pressure_api_error(self, _wired):
        from withings_mcp.server import get_blood_pressure

        _wired.get_measurements.side_effect = WithingsAPIError("api_error", "Failed", "Retry")
        result = await get_blood_pressure("2026-03-01", "2026-03-10")
        assert result["error"] == "api_error"


@pytest.mark.usefixtures("_wired")
class TestGetBodyCompositionTrend:
    @pytest.mark.asyncio()
    async def test_get_body_composition_trend(self):
        from withings_mcp.server import get_body_composition_trend

        result = await get_body_composition_trend(weeks=4)
        assert result["weeks_requested"] == 4
        assert len(result["trend"]) >= 1
        assert "avg_weight_kg" in result["trend"][0]

    @pytest.mark.asyncio()
    async def test_get_body_composition_trend_no_data(self, _wired):
        from withings_mcp.server import get_body_composition_trend

        _wired.get_measurements.return_value = []
        result = await get_body_composition_trend(weeks=4)
        assert "No weight measurements" in result["message"]
        assert result["weeks"] == []

    @pytest.mark.asyncio()
    async def test_get_body_composition_trend_api_error(self, _wired):
        from withings_mcp.server import get_body_composition_trend

        _wired.get_measurements.side_effect = WithingsAPIError("api_error", "Failed", "Retry")
        result = await get_body_composition_trend()
        assert result["error"] == "api_error"
