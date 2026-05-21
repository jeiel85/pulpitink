"""Shared pytest fixtures.

The key responsibility is keeping every test isolated from the user's
real PulpitInk data directory. We point ``platformdirs`` at a temp
location for the whole test session.
"""

from __future__ import annotations

from pathlib import Path

import pytest

import pulpit_ink.app.paths as paths_module


@pytest.fixture(autouse=True)
def _isolated_app_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Redirect ``get_app_paths`` to a temp directory for each test."""

    base = tmp_path / "PulpitInk_data"
    cache = tmp_path / "PulpitInk_cache"
    logs = tmp_path / "PulpitInk_logs"
    fake = paths_module.AppPaths(
        data_dir=base,
        cache_dir=cache,
        log_dir=logs,
        models_dir=base / "models",
        jobs_dir=cache / "jobs",
    )
    fake.ensure()
    monkeypatch.setattr(paths_module, "get_app_paths", lambda: fake)
    return base
