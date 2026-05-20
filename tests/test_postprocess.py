"""Tests for the postprocess pipeline + lexicon."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from sermonscript.core.postprocess import (
    Lexicon,
    load_user_lexicon,
    normalise_bible_reference,
    postprocess_text,
)
from sermonscript.core.postprocess.lexicon import default_lexicon


def test_normalise_bible_reference_sino_numerals() -> None:
    assert normalise_bible_reference("로마서 일장 일절") == "로마서 1장 1절"
    assert normalise_bible_reference("창세기 삼장 십육절") == "창세기 3장 16절"
    # idempotent: already canonical form stays the same.
    assert normalise_bible_reference("로마서 1장 1절") == "로마서 1장 1절"


def test_normalise_collapses_book_name_spacing() -> None:
    # Lexicon already turns "고린도 전서" into "고린도전서" — bible_refs
    # normalisation collapses extra whitespace between book and chapter.
    base = "로마서   3장 16절"
    assert normalise_bible_reference(base) == "로마서 3장 16절"


def test_normalise_leaves_unrelated_text_alone() -> None:
    # Plain numerals not attached to 장/절 should not be rewritten.
    assert normalise_bible_reference("이 사람은 일을 잘합니다") == "이 사람은 일을 잘합니다"


def test_lexicon_apply_replaces_known_wrong_forms() -> None:
    lex = default_lexicon()
    src = "오늘 본문은 고린도 전서 5장 1절입니다."
    out = lex.apply(src)
    assert "고린도전서" in out
    assert "고린도 전서" not in out


def test_lexicon_does_not_rewrite_when_no_wrong_forms() -> None:
    lex = Lexicon()
    lex.add("아멘")  # no wrong forms
    assert lex.apply("아멘 합시다") == "아멘 합시다"


def test_postprocess_text_runs_full_pipeline() -> None:
    src = "오늘 본문은 고린도 전서 일장 일절입니다."
    out = postprocess_text(src)
    assert "고린도전서" in out
    assert "1장 1절" in out
    assert "고린도 전서" not in out
    assert "일장" not in out


def test_postprocess_handles_empty_text() -> None:
    assert postprocess_text("") == ""
    assert postprocess_text("   ") == ""


def test_load_user_lexicon_layers_on_top(tmp_path: Path) -> None:
    user_dict = tmp_path / "user.json"
    user_dict.write_text(
        json.dumps({"맥체인": ["맥 체인", "맥체 인"]}, ensure_ascii=False),
        encoding="utf-8",
    )
    lex = load_user_lexicon(user_dict)
    assert "맥체인" in lex.apply("오늘은 맥 체인 묵상을 했다.")
    # default lexicon entries still active
    assert "고린도전서" in lex.apply("고린도 전서 5장")


def test_load_user_lexicon_missing_path_returns_default() -> None:
    lex = load_user_lexicon(None)
    assert isinstance(lex, Lexicon)
    # ensures default entries are present
    assert lex.apply("고린도 전서") == "고린도전서"


def test_load_user_lexicon_rejects_non_json(tmp_path: Path) -> None:
    bogus = tmp_path / "bad.json"
    bogus.write_text("not json", encoding="utf-8")
    with pytest.raises(ValueError):
        load_user_lexicon(bogus)
