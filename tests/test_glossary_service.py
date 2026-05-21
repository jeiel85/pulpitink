"""Tests for the custom Glossary service and lexicon file saving/loading."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from pulpit_ink.core.postprocess import postprocess_text
from pulpit_ink.core.postprocess.lexicon import (
    Lexicon,
    load_user_lexicon,
    save_user_lexicon,
)
from pulpit_ink.services.transcribe_service import TranscribeRequest, _build_lexicon


def test_save_user_lexicon(tmp_path: Path) -> None:
    """Test that custom entries are safely dumped to a JSON file."""
    target_file = tmp_path / "custom_dict.json"
    entries = {
        "엘로힘": ["멜로힘", "엘로임"],
        "야훼": ["약회"],
    }

    # 1. First time write
    save_user_lexicon(target_file, entries)
    assert target_file.exists()

    # Verify content
    loaded_raw = json.loads(target_file.read_text(encoding="utf-8"))
    assert loaded_raw["엘로힘"] == ["멜로힘", "엘로임"]
    assert loaded_raw["야훼"] == ["약회"]

    # 2. Overwrite / Backup restoration verification
    new_entries = {
        "엘로힘": ["멜로힘"],
        "새에덴교회": ["세외 대교회"],
    }
    save_user_lexicon(target_file, new_entries)

    # Target should be updated, and backup should exist (or clean up)
    loaded_new = json.loads(target_file.read_text(encoding="utf-8"))
    assert "새에덴교회" in loaded_new
    assert "야훼" not in loaded_new


def test_load_user_lexicon_merge(tmp_path: Path) -> None:
    """Test that load_user_lexicon merges default terms with custom terms."""
    dict_file = tmp_path / "user_dict.json"
    entries = {
        "이필립 목사님": ["잎일립 목사님", "이필립"],
    }
    save_user_lexicon(dict_file, entries)

    # Load custom lexicon
    lex = load_user_lexicon(dict_file)
    assert isinstance(lex, Lexicon)

    # Default bible books should still exist
    assert "창세기" in lex.entries
    # Custom term should exist
    assert "이필립 목사님" in lex.entries
    assert "잎일립 목사님" in lex.entries["이필립 목사님"]


def test_postprocess_with_user_lexicon(tmp_path: Path) -> None:
    """Verify that postprocess_text correctly substitutes custom terms."""
    dict_file = tmp_path / "user_dict.json"
    entries = {
        "엘로힘": ["멜로힘", "엘로임"],
        "이필립 목사님": ["잎일립 목사님"],
    }
    save_user_lexicon(dict_file, entries)

    lex = load_user_lexicon(dict_file)

    # Test postprocess substitution
    input_text = "오늘 잎일립 목사님 설교에서 멜로힘과 엘로임의 차이를 나눴다."
    expected = "오늘 이필립 목사님 설교에서 엘로힘과 엘로힘의 차이를 나눴다."

    result = postprocess_text(input_text, lexicon=lex)
    assert result == expected


def test_build_lexicon_fallback(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that _build_lexicon resolves to default data dir user_dict.json if path is omitted."""

    # Mock get_app_paths to return our temp dir as data_dir
    from pulpit_ink.app.paths import AppPaths

    dummy_paths = AppPaths(
        data_dir=tmp_path,
        cache_dir=tmp_path / "cache",
        log_dir=tmp_path / "log",
        models_dir=tmp_path / "models",
        jobs_dir=tmp_path / "jobs",
    )

    monkeypatch.setattr(
        "pulpit_ink.app.paths.get_app_paths",
        lambda: dummy_paths
    )

    # 1. If user_dict.json does not exist, it should return default lexicon
    req = TranscribeRequest(
        input_path=Path("dummy.mp3"),
        output_dir=tmp_path,
        user_dict_path=None
    )
    lex = _build_lexicon(req)
    assert "이필립" not in lex.entries

    # 2. If user_dict.json exists in app data dir, it should be loaded automatically
    custom_dict_path = tmp_path / "user_dict.json"
    entries = {
        "이필립": ["잎일립"],
    }
    save_user_lexicon(custom_dict_path, entries)

    lex_auto = _build_lexicon(req)
    assert "이필립" in lex_auto.entries
    assert "잎일립" in lex_auto.entries["이필립"]
