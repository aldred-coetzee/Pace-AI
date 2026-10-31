"""Configuration loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass

from pace_ai.workspace import load_config, resolve_in_workspace


@dataclass(frozen=True)
class Settings:
    client_id: str
    client_secret: str
    access_token: str | None = None
    refresh_token: str | None = None
    db_path: str = ""

    @classmethod
    def from_env(cls) -> Settings:
        load_config()

        client_id = os.environ.get("STRAVA_CLIENT_ID", "")
        client_secret = os.environ.get("STRAVA_CLIENT_SECRET", "")

        if not client_id or not client_secret:
            msg = "STRAVA_CLIENT_ID and STRAVA_CLIENT_SECRET must be set"
            raise ValueError(msg)

        # Relative overrides resolve against the workspace; absolute are used as given.
        raw_db = resolve_in_workspace(os.environ.get("STRAVA_DB") or "strava.db")

        return cls(
            client_id=client_id,
            client_secret=client_secret,
            access_token=os.environ.get("STRAVA_ACCESS_TOKEN"),
            refresh_token=os.environ.get("STRAVA_REFRESH_TOKEN"),
            db_path=raw_db,
        )
