"""Withings authentication via withings-sync library.

The withings-sync library handles the full OAuth2 flow including token refresh.
Config is stored in JSON files (withings_app.json + .withings_user.json).
"""

from __future__ import annotations

import os

from withings_sync.withings2 import WithingsAccount


def create_account(config_folder: str = "") -> WithingsAccount:
    """Create a WithingsAccount, optionally from a specific config folder.

    Settings default config_folder to <workspace>/withings, so the user token
    file (.withings_user.json) never lands in the home directory or checkout.

    If config_folder is set:
    - {config_folder}/.withings_user.json holds the user tokens (always)
    - {config_folder}/withings_app.json is used if present, otherwise the
      library-bundled app config (or the WITHINGS_APP env var)

    If config_folder is empty, uses the library defaults (~/.withings_user.json).
    """
    if config_folder:
        # The library writes .withings_user.json here but does not create the folder.
        os.makedirs(config_folder, mode=0o700, exist_ok=True)
        return WithingsAccount(config_folder=config_folder)
    return WithingsAccount()
