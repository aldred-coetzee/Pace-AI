"""Configuration loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass

from pace_ai.workspace import load_config, resolve_in_workspace


@dataclass(frozen=True)
class Settings:
    email: str = ""
    password: str = ""
    garth_home: str = ""

    @classmethod
    def from_env(cls) -> Settings:
        load_config()

        email = os.environ.get("GARMIN_EMAIL", "")
        password = os.environ.get("GARMIN_PASSWORD", "")

        # Credentials are needed only by `pace-ai-garmin-login`; the client
        # authenticates from saved garth tokens.
        return cls(
            email=email,
            password=password,
            garth_home=resolve_in_workspace(os.environ.get("GARTH_HOME") or "garth"),
        )
