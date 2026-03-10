"""Withings API client wrapping withings-sync's WithingsAccount."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from withings_sync.withings2 import WithingsAccount, WithingsMeasureGroup

    from withings_mcp.config import Settings

logger = logging.getLogger(__name__)


class WithingsAPIError(RuntimeError):
    """Structured error from the Withings API with recovery guidance."""

    def __init__(self, code: str, message: str, action: str) -> None:
        super().__init__(message)
        self.code = code
        self.action = action

    def to_dict(self) -> dict[str, Any]:
        return {
            "error": self.code,
            "message": str(self),
            "action": self.action,
        }


class WithingsClient:
    """Wraps withings-sync WithingsAccount with lazy init and error handling."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._account: WithingsAccount | None = None

    def _ensure_account(self) -> WithingsAccount:
        """Lazily initialize the Withings account (triggers auth if needed)."""
        if self._account is not None:
            return self._account

        try:
            from withings_mcp.auth import create_account

            self._account = create_account(self._settings.config_folder)
        except Exception as e:
            raise WithingsAPIError(
                code="auth_failed",
                message=f"Failed to initialize Withings account: {e}",
                action="Check your Withings credentials and re-authenticate.",
            ) from e

        return self._account

    def _call_measurements(self, startdate: int, enddate: int) -> list[WithingsMeasureGroup] | None:
        """Call get_measurements with error handling."""
        account = self._ensure_account()
        try:
            return account.get_measurements(startdate, enddate)
        except Exception as e:
            error_str = str(e).lower()
            if "401" in error_str or "auth" in error_str or "token" in error_str:
                self._account = None
                raise WithingsAPIError(
                    code="auth_expired",
                    message="Withings session expired.",
                    action="Re-authenticate with Withings.",
                ) from e
            raise WithingsAPIError(
                code="api_error",
                message=f"Withings API error: {e}",
                action="Check the request parameters and try again.",
            ) from e

    def get_measurements(self, startdate: int, enddate: int) -> list[dict[str, Any]]:
        """Get body measurements between two timestamps.

        Returns list of parsed measurement dicts with named fields.
        """
        groups = self._call_measurements(startdate, enddate)
        if groups is None:
            return []
        return [_parse_group(g) for g in groups]

    def get_height(self) -> float | None:
        """Get the user's height in meters."""
        account = self._ensure_account()
        try:
            return account.get_height()
        except Exception as e:
            raise WithingsAPIError(
                code="api_error",
                message=f"Failed to get height: {e}",
                action="Check your Withings account.",
            ) from e


def _parse_group(group: WithingsMeasureGroup) -> dict[str, Any]:
    """Parse a WithingsMeasureGroup into a structured dict."""
    entry: dict[str, Any] = {
        "date": group.date,
        "grpid": group.grpid,
    }

    dt = group.get_datetime()
    if dt:
        entry["datetime"] = dt.isoformat()

    extractors: list[tuple[str, Any]] = [
        ("weight_kg", group.get_weight),
        ("fat_ratio_pct", group.get_fat_ratio),
        ("fat_mass_kg", group.get_fat_mass_weight),
        ("fat_free_mass_kg", group.get_fat_free_mass),
        ("muscle_mass_kg", group.get_muscle_mass),
        ("bone_mass_kg", group.get_bone_mass),
        ("hydration_kg", group.get_hydration),
        ("systolic_mmhg", group.get_systolic_blood_pressure),
        ("diastolic_mmhg", group.get_diastolic_blood_pressure),
        ("heart_pulse_bpm", group.get_heart_pulse),
    ]

    for name, extractor in extractors:
        value = extractor()
        if value is not None:
            entry[name] = value

    return entry
