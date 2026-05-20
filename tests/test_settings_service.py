"""Tests for the settings service."""

from __future__ import annotations

from pathlib import Path

import pytest

from pulpitink.services.settings_service import Settings, SettingsService


def test_load_returns_defaults_when_missing(tmp_path: Path) -> None:
    svc = SettingsService(tmp_path / "settings.json")
    loaded = svc.load()
    assert loaded == Settings()
    assert loaded.language == "ko"


def test_save_then_load_roundtrip(tmp_path: Path) -> None:
    svc = SettingsService(tmp_path / "settings.json")
    svc.save(Settings(language="en", model="medium", preset="stt_basic"))
    loaded = svc.load()
    assert loaded.language == "en"
    assert loaded.model == "medium"
    assert loaded.preset == "stt_basic"


def test_update_merges_known_keys(tmp_path: Path) -> None:
    svc = SettingsService(tmp_path / "settings.json")
    svc.update(language="en")
    svc.update(model="large-v3")
    loaded = svc.load()
    assert loaded.language == "en"
    assert loaded.model == "large-v3"


def test_update_rejects_unknown_key(tmp_path: Path) -> None:
    svc = SettingsService(tmp_path / "settings.json")
    with pytest.raises(KeyError):
        svc.update(nonexistent="oops")


def test_load_ignores_extra_keys(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    path.write_text('{"language": "ja", "future_field": 1}', encoding="utf-8")
    svc = SettingsService(path)
    assert svc.load().language == "ja"


def test_resolved_paths_default_to_app_paths() -> None:
    settings = Settings()
    out = settings.resolved_output_dir()
    cache = settings.resolved_model_cache_dir()
    assert out.name == "exports"
    assert cache.name == "models"


def test_update_coerces_keep_history(tmp_path: Path) -> None:
    svc = SettingsService(tmp_path / "settings.json")
    assert svc.load().keep_history is True
    svc.update(keep_history="false")
    assert svc.load().keep_history is False
    svc.update(keep_history="1")
    assert svc.load().keep_history is True
    svc.update(keep_history=False)
    assert svc.load().keep_history is False
