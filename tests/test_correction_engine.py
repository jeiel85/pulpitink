"""Tests for the correction suggestion engine + helpers."""

from __future__ import annotations

from pathlib import Path

from pulpit_ink.core.postprocess import Lexicon
from pulpit_ink.core.reference.corrections import (
    CorrectionEngine,
    apply_correction_to_segment,
)
from pulpit_ink.core.reference.parser import ParsedReference


def test_engine_suggests_bible_reference_normalisation() -> None:
    engine = CorrectionEngine()
    cands = engine.suggestions_for(0, "오늘 본문은 로마서 일장 일절입니다.")
    assert any(c.kind == "bible_ref" for c in cands)
    bible = [c for c in cands if c.kind == "bible_ref"][0]
    assert "1장 1절" in bible.suggested_text


def test_engine_suggests_lexicon_for_known_wrong_form() -> None:
    engine = CorrectionEngine()
    cands = engine.suggestions_for(0, "본문은 고린도 전서 5장입니다.")
    assert any(
        c.kind == "user_dict" and c.suggested_text == "고린도전서" for c in cands
    )


def test_engine_does_not_suggest_for_clean_text() -> None:
    engine = CorrectionEngine()
    assert engine.suggestions_for(0, "오늘은 좋은 날입니다.") == []


def test_engine_uses_user_lexicon_entries() -> None:
    lex = Lexicon()
    lex.add("성만찬", "성 만찬")
    engine = CorrectionEngine(lexicon=lex)
    cands = engine.suggestions_for(2, "오늘은 성 만찬을 시행합니다.")
    assert any(c.suggested_text == "성만찬" for c in cands)


def test_engine_from_reference_seeds_proper_nouns() -> None:
    parsed = ParsedReference(
        source_path=Path("sermon.md"),
        title="t",
        content="",
        paragraphs=[],
        bible_refs=[],
        keywords=[],
        proper_nouns=["John Calvin"],
    )
    engine = CorrectionEngine.from_reference(parsed)
    cands = engine.suggestions_for(1, "오늘 인물은 john  calvin 입니다.")
    assert any(c.kind == "proper_noun" and c.suggested_text == "John Calvin" for c in cands)


def test_engine_emits_each_pair_only_once() -> None:
    engine = CorrectionEngine()
    cands = engine.suggestions_for(
        0, "고린도 전서 1장과 고린도 전서 2장에서 말씀하셨습니다."
    )
    user_dict_hits = [c for c in cands if c.kind == "user_dict"]
    assert len(user_dict_hits) == 1


def test_apply_correction_replaces_first_occurrence() -> None:
    new = apply_correction_to_segment(
        raw_text="고린도 전서 5장 1절을 본문으로",
        clean_text="",
        edited_text="",
        original="고린도 전서",
        suggested="고린도전서",
    )
    assert new == "고린도전서 5장 1절을 본문으로"


def test_apply_correction_prefers_edited_text() -> None:
    new = apply_correction_to_segment(
        raw_text="raw text",
        clean_text="clean text",
        edited_text="edited 고린도 전서",
        original="고린도 전서",
        suggested="고린도전서",
    )
    assert new == "edited 고린도전서"


def test_apply_correction_falls_back_when_original_missing() -> None:
    new = apply_correction_to_segment(
        raw_text="다른 내용",
        clean_text="",
        edited_text="",
        original="없음",
        suggested="대체",
    )
    assert new == "대체"
