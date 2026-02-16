"""Garmin Connect API client wrapping garminconnect.Garmin."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from garminconnect import Garmin

from garmin_mcp.auth import GarminAuth

if TYPE_CHECKING:
    from garmin_mcp.config import Settings

logger = logging.getLogger(__name__)


class GarminAPIError(RuntimeError):
    """Structured error from the Garmin Connect API with recovery guidance."""

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


class GarminClient:
    """Wraps garminconnect.Garmin with lazy init and error handling."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._garmin: Garmin | None = None
        self._auth = GarminAuth(settings.garth_home)

    def _ensure_client(self) -> Garmin:
        """Lazily initialize and authenticate the Garmin client."""
        if self._garmin is not None:
            return self._garmin

        if not self._auth.resume():
            raise GarminAPIError(
                code="auth_required",
                message="No valid Garmin session found.",
                action="Run `garmin-mcp-login` to authenticate first.",
            )

        try:
            self._garmin = Garmin()
            self._garmin.login(self._settings.garth_home)
        except Exception as e:
            raise GarminAPIError(
                code="auth_failed",
                message=f"Failed to initialize Garmin client: {e}",
                action="Run `garmin-mcp-login` to re-authenticate.",
            ) from e

        return self._garmin

    def _call(self, method_name: str, *args: Any, **kwargs: Any) -> Any:
        """Call a method on the Garmin client with error handling."""
        client = self._ensure_client()
        method = getattr(client, method_name, None)
        if method is None:
            msg = f"Garmin client has no method '{method_name}'"
            raise AttributeError(msg)
        try:
            return method(*args, **kwargs)
        except Exception as e:
            error_str = str(e).lower()
            if "401" in error_str or "auth" in error_str or "unauthorized" in error_str:
                self._garmin = None
                raise GarminAPIError(
                    code="auth_expired",
                    message="Garmin session expired.",
                    action="Run `garmin-mcp-login` to re-authenticate.",
                ) from e
            if "429" in error_str or "too many" in error_str:
                raise GarminAPIError(
                    code="rate_limited",
                    message="Garmin API rate limit exceeded.",
                    action="Wait a few minutes and try again.",
                ) from e
            raise GarminAPIError(
                code="api_error",
                message=f"Garmin API error: {e}",
                action="Check the request parameters and try again.",
            ) from e

    def check_auth(self) -> dict[str, Any]:
        """Check if authentication is valid. Returns user info."""
        client = self._ensure_client()
        try:
            name = client.get_full_name()
            return {"authenticated": True, "display_name": name}
        except Exception:
            return {"authenticated": True, "display_name": "Unknown"}

    def get_workouts(self, start: int = 0, limit: int = 100) -> Any:
        """List workouts from Garmin Connect."""
        return self._call("get_workouts", start, limit)

    def get_workout(self, workout_id: int) -> Any:
        """Get a single workout by ID."""
        return self._call("get_workout_by_id", workout_id)

    def create_workout(self, workout_json: dict[str, Any]) -> Any:
        """Create a workout in Garmin Connect."""
        return self._call("upload_workout", workout_json)

    def delete_workout(self, workout_id: int) -> Any:
        """Delete a workout from Garmin Connect.

        Uses garth directly since garminconnect doesn't expose this method.
        """
        client = self._ensure_client()
        try:
            url = f"/workout-service/workout/{workout_id}"
            resp = client.garth.delete("connectapi", url, api=True)
            resp.raise_for_status()
            return {"deleted": True, "workout_id": workout_id}
        except Exception as e:
            raise GarminAPIError(
                code="delete_failed",
                message=f"Failed to delete workout {workout_id}: {e}",
                action="Check the workout ID and try again.",
            ) from e

    def schedule_workout(self, workout_id: int, date: str) -> Any:
        """Schedule a workout to a specific date.

        Args:
            workout_id: The Garmin workout ID.
            date: Date in YYYY-MM-DD format.

        Uses garth directly since garminconnect doesn't expose this method.
        """
        client = self._ensure_client()
        try:
            url = f"/workout-service/schedule/{workout_id}"
            payload = {"date": date}
            resp = client.garth.post("connectapi", url, json=payload, api=True)
            resp.raise_for_status()
            return {"scheduled": True, "workout_id": workout_id, "date": date}
        except Exception as e:
            raise GarminAPIError(
                code="schedule_failed",
                message=f"Failed to schedule workout {workout_id} on {date}: {e}",
                action="Check the workout ID and date format (YYYY-MM-DD).",
            ) from e

    def get_calendar(self, year: int, month: int) -> Any:
        """Get calendar events for a month.

        Uses garth directly since garminconnect doesn't expose this method.
        """
        client = self._ensure_client()
        try:
            url = f"/workout-service/schedule/{year}/{month}"
            resp = client.garth.get("connectapi", url, api=True)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            raise GarminAPIError(
                code="calendar_error",
                message=f"Failed to get calendar for {year}-{month:02d}: {e}",
                action="Check the year and month values.",
            ) from e
