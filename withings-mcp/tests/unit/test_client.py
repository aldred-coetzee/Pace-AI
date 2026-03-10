"""Unit tests for client module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from withings_mcp.client import WithingsAPIError, WithingsClient, _parse_group
from withings_mcp.config import Settings

from ..conftest import make_mock_bp_group, make_mock_measure_group


class TestWithingsAPIError:
    def test_to_dict(self):
        err = WithingsAPIError(code="test_error", message="Something broke", action="Fix it")
        d = err.to_dict()
        assert d["error"] == "test_error"
        assert d["message"] == "Something broke"
        assert d["action"] == "Fix it"

    def test_inherits_runtime_error(self):
        err = WithingsAPIError(code="test", message="msg", action="act")
        assert isinstance(err, RuntimeError)
        assert str(err) == "msg"


class TestParseGroup:
    def test_parses_weight_group(self):
        group = make_mock_measure_group(weight_kg=75.5, fat_ratio=18.2)
        result = _parse_group(group)
        assert result["weight_kg"] == 75.5
        assert result["fat_ratio_pct"] == 18.2
        assert result["grpid"] == 1001
        assert "datetime" in result

    def test_parses_bp_group(self):
        group = make_mock_bp_group(systolic=125.0, diastolic=82.0)
        result = _parse_group(group)
        assert result["systolic_mmhg"] == 125.0
        assert result["diastolic_mmhg"] == 82.0
        assert "weight_kg" not in result

    def test_omits_none_values(self):
        group = make_mock_measure_group(
            weight_kg=80.0, fat_ratio=None, muscle_mass=None, bone_mass=None, hydration=None
        )
        result = _parse_group(group)
        assert result["weight_kg"] == 80.0
        assert "fat_ratio_pct" not in result
        assert "muscle_mass_kg" not in result


class TestWithingsClient:
    def test_ensure_account_caches(self):
        settings = Settings()
        client = WithingsClient(settings)
        mock_account = MagicMock()
        client._account = mock_account

        result = client._ensure_account()
        assert result is mock_account

    def test_ensure_account_failure_raises(self):
        settings = Settings()
        client = WithingsClient(settings)

        with (
            patch("withings_mcp.auth.create_account", side_effect=Exception("Auth failed")),
            pytest.raises(WithingsAPIError, match="Failed to initialize"),
        ):
            client._ensure_account()

    def test_get_measurements_success(self):
        settings = Settings()
        client = WithingsClient(settings)
        mock_account = MagicMock()
        mock_account.get_measurements.return_value = [make_mock_measure_group(weight_kg=80.0)]
        client._account = mock_account

        result = client.get_measurements(1000, 2000)
        assert len(result) == 1
        assert result[0]["weight_kg"] == 80.0
        mock_account.get_measurements.assert_called_once_with(1000, 2000)

    def test_get_measurements_none_returns_empty(self):
        settings = Settings()
        client = WithingsClient(settings)
        mock_account = MagicMock()
        mock_account.get_measurements.return_value = None
        client._account = mock_account

        result = client.get_measurements(1000, 2000)
        assert result == []

    def test_get_measurements_auth_error_clears_account(self):
        settings = Settings()
        client = WithingsClient(settings)
        mock_account = MagicMock()
        mock_account.get_measurements.side_effect = Exception("401 unauthorized")
        client._account = mock_account

        with pytest.raises(WithingsAPIError, match="session expired"):
            client.get_measurements(1000, 2000)
        assert client._account is None

    def test_get_measurements_generic_error(self):
        settings = Settings()
        client = WithingsClient(settings)
        mock_account = MagicMock()
        mock_account.get_measurements.side_effect = Exception("Something unexpected")
        client._account = mock_account

        with pytest.raises(WithingsAPIError, match="Withings API error"):
            client.get_measurements(1000, 2000)

    def test_get_height_delegates(self):
        settings = Settings()
        client = WithingsClient(settings)
        mock_account = MagicMock()
        mock_account.get_height.return_value = 1.78
        client._account = mock_account

        result = client.get_height()
        assert result == 1.78
