"""The workspace: the one directory that holds every personal file.

The repository is public, so credentials, tokens, databases and caches never
live inside the checkout. They live here (default ``~/.local/share/pace-ai``,
override with ``PACE_AI_WORKSPACE``).
"""

from __future__ import annotations

import logging
import os
import secrets
import stat
from pathlib import Path

from dotenv import load_dotenv

log = logging.getLogger(__name__)

DEFAULT_WORKSPACE = "~/.local/share/pace-ai"
CONFIG_NAME = "config.env"

_loaded = False


def workspace_dir() -> Path:
    """Return the workspace directory, creating it (mode 0700) if needed."""
    path = Path(os.environ.get("PACE_AI_WORKSPACE") or DEFAULT_WORKSPACE).expanduser()
    path.mkdir(parents=True, mode=0o700, exist_ok=True)
    return path


def workspace_path(name: str) -> Path:
    """Return ``name`` inside the workspace (no file is created)."""
    return workspace_dir() / name


def _warn_if_open(path: Path) -> None:
    if path.exists() and path.stat().st_mode & (stat.S_IRWXG | stat.S_IRWXO):
        log.warning("%s is accessible by group/others; run: chmod %s %s", path, "700" if path.is_dir() else "600", path)


def load_config() -> None:
    """Load ``config.env`` from the workspace, once per process.

    Real environment variables win over the file. A missing file is fine.
    """
    global _loaded
    if _loaded:
        return
    _loaded = True
    root = workspace_dir()
    _warn_if_open(root)
    cfg = root / CONFIG_NAME
    if cfg.exists():
        _warn_if_open(cfg)
        load_dotenv(cfg, override=False)
    else:
        log.info("No %s found; using environment variables only", cfg)


def resolve_in_workspace(raw: str) -> str:
    """Resolve a configured path: absolute as given, relative against the workspace."""
    p = Path(raw).expanduser()
    return str(p if p.is_absolute() else workspace_dir() / p)


def secret_key() -> str:
    """Return the session-signing key, generating it (mode 0600) on first use.

    Kept in the workspace so it survives restarts and never sits in the
    public checkout.
    """
    path = workspace_path("secret_key")
    if not path.exists():
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w") as f:
            f.write(secrets.token_hex(32))
    _warn_if_open(path)
    return path.read_text().strip()


def _reset_for_tests() -> None:
    """Forget that config.env was loaded (tests only)."""
    global _loaded
    _loaded = False
