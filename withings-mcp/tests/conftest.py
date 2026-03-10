"""Shared test fixtures for withings-mcp."""

from __future__ import annotations

import time
from unittest.mock import MagicMock

import pytest

from withings_mcp.config import Settings


@pytest.fixture()
def settings():
    """Test settings."""
    return Settings()


def make_mock_measure_group(
    weight_kg: float | None = 75.5,
    fat_ratio: float | None = 18.2,
    muscle_mass: float | None = 35.1,
    bone_mass: float | None = 3.2,
    hydration: float | None = 40.0,
    systolic: float | None = None,
    diastolic: float | None = None,
    heart_pulse: float | None = None,
    grpid: int = 1001,
    date: int | None = None,
) -> MagicMock:
    """Factory for a mocked WithingsMeasureGroup."""
    from datetime import datetime

    mock = MagicMock()
    mock.grpid = grpid
    mock.date = date or int(time.time()) - 3600
    mock.get_datetime.return_value = datetime.fromtimestamp(mock.date)
    mock.get_weight.return_value = weight_kg
    mock.get_fat_ratio.return_value = fat_ratio
    mock.get_fat_mass_weight.return_value = None
    mock.get_fat_free_mass.return_value = None
    mock.get_muscle_mass.return_value = muscle_mass
    mock.get_bone_mass.return_value = bone_mass
    mock.get_hydration.return_value = hydration
    mock.get_systolic_blood_pressure.return_value = systolic
    mock.get_diastolic_blood_pressure.return_value = diastolic
    mock.get_heart_pulse.return_value = heart_pulse
    return mock


def make_mock_bp_group(
    systolic: float = 120.0,
    diastolic: float = 80.0,
    heart_pulse: float = 65.0,
    grpid: int = 2001,
    date: int | None = None,
) -> MagicMock:
    """Factory for a mocked BP measurement group."""
    return make_mock_measure_group(
        weight_kg=None,
        fat_ratio=None,
        muscle_mass=None,
        bone_mass=None,
        hydration=None,
        systolic=systolic,
        diastolic=diastolic,
        heart_pulse=heart_pulse,
        grpid=grpid,
        date=date,
    )
