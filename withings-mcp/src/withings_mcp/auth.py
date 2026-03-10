"""Withings authentication via withings-sync library.

The withings-sync library handles the full OAuth2 flow including token refresh.
Config is stored in JSON files (withings_app.json + .withings_user.json).
"""

from __future__ import annotations

from withings_sync.withings2 import WithingsAccount


def create_account(config_folder: str = "") -> WithingsAccount:
    """Create a WithingsAccount, optionally from a specific config folder.

    If config_folder is empty, uses the library defaults:
    - App config: bundled withings_app.json (or WITHINGS_APP env var)
    - User config: ~/.withings_user.json

    If config_folder is set, looks for:
    - {config_folder}/withings_app.json
    - {config_folder}/.withings_user.json
    """
    if config_folder:
        return WithingsAccount(config_folder=config_folder)
    return WithingsAccount()
