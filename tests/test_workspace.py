"""Tests for the workspace module."""

from __future__ import annotations

import logging
import os
import stat

from pace_ai import workspace


def test_default_path(monkeypatch, tmp_path):
    monkeypatch.delenv("PACE_AI_WORKSPACE")
    monkeypatch.setenv("HOME", str(tmp_path))
    assert workspace.workspace_dir() == tmp_path / ".local" / "share" / "pace-ai"


def test_env_override_and_created_0700(tmp_path):
    d = workspace.workspace_dir()
    assert d == tmp_path / "pace-ai-workspace"
    assert d.is_dir()
    assert stat.S_IMODE(d.stat().st_mode) == 0o700


def test_workspace_path(tmp_path):
    assert workspace.workspace_path("a.db") == tmp_path / "pace-ai-workspace" / "a.db"


def test_resolve_relative_and_absolute(tmp_path):
    assert workspace.resolve_in_workspace("a.db") == str(tmp_path / "pace-ai-workspace" / "a.db")
    assert workspace.resolve_in_workspace("/x/a.db") == "/x/a.db"


def _write_config(tmp_path, text, mode=0o600):
    d = workspace.workspace_dir()
    cfg = d / "config.env"
    cfg.write_text(text)
    cfg.chmod(mode)
    return cfg


def test_config_env_loaded(monkeypatch, tmp_path):
    monkeypatch.delenv("PACE_TEST_KEY", raising=False)
    _write_config(tmp_path, "PACE_TEST_KEY=hello\n")
    workspace.load_config()
    assert os.environ["PACE_TEST_KEY"] == "hello"
    monkeypatch.delenv("PACE_TEST_KEY")


def test_real_env_not_overridden(monkeypatch, tmp_path):
    monkeypatch.setenv("PACE_TEST_KEY", "real")
    _write_config(tmp_path, "PACE_TEST_KEY=file\n")
    workspace.load_config()
    assert os.environ["PACE_TEST_KEY"] == "real"


def test_missing_config_is_fine():
    workspace.load_config()  # no exception


def test_loads_once(monkeypatch, tmp_path):
    monkeypatch.delenv("PACE_TEST_KEY", raising=False)
    workspace.load_config()
    _write_config(tmp_path, "PACE_TEST_KEY=late\n")
    workspace.load_config()
    assert "PACE_TEST_KEY" not in os.environ


def test_warns_on_world_readable_config(tmp_path, caplog):
    _write_config(tmp_path, "A=1\n", mode=0o644)
    with caplog.at_level(logging.WARNING, logger="pace_ai.workspace"):
        workspace.load_config()
    assert any("config.env" in r.message and "chmod" in r.message for r in caplog.records)
    os.environ.pop("A", None)


def test_no_warning_when_private(tmp_path, caplog):
    _write_config(tmp_path, "PACE_TEST_Q=1\n")
    with caplog.at_level(logging.WARNING, logger="pace_ai.workspace"):
        workspace.load_config()
    assert not caplog.records
    os.environ.pop("PACE_TEST_Q", None)


def test_secret_key_is_created_private_and_stable() -> None:
    import stat

    from pace_ai.workspace import secret_key, workspace_path

    first = secret_key()
    path = workspace_path("secret_key")
    assert len(first) == 64
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert secret_key() == first
