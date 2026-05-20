"""Tests for the model catalog service."""

from __future__ import annotations

from pathlib import Path

from pulpitink.services.model_service import (
    is_supported,
    list_models,
    model_cache_dir,
)


def test_list_models_includes_defaults() -> None:
    names = {m.name for m in list_models()}
    assert {"tiny", "base", "small", "medium", "large-v3"} <= names


def test_is_supported() -> None:
    assert is_supported("small") is True
    assert is_supported("doesnotexist") is False


def test_model_cache_dir_default_under_app_paths() -> None:
    path = model_cache_dir()
    assert path.exists()
    assert path.name == "models"


def test_model_cache_dir_honours_override(tmp_path: Path) -> None:
    override = tmp_path / "custom-cache"
    path = model_cache_dir(override)
    assert path == override
    assert path.exists()
