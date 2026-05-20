"""Tests for the sermon reference parser + prompt builder."""

from __future__ import annotations

from pathlib import Path

import pytest

from sermonscript.core.reference import (
    align_segments_to_reference,
    build_reference_prompt,
    parse_reference,
    prompt_from_parsed,
)

SAMPLE_MD = """# 로마서 1장 강해

오늘 본문은 로마서 1장 1절~17절입니다. 사도 바울이 로마 교회에 보낸 편지입니다.

핵심 인물: John Calvin, 어거스틴. "이신칭의"라는 표현이 핵심입니다.

복음은 모든 믿는 자에게 구원을 주시는 하나님의 능력입니다. 복음은 능력입니다.
은혜와 평강이 함께하기를 빕니다.
"""


def test_parse_extracts_title_and_paragraphs(tmp_path: Path) -> None:
    p = tmp_path / "sermon.md"
    p.write_text(SAMPLE_MD, encoding="utf-8")
    parsed = parse_reference(p)
    assert parsed.title == "로마서 1장 강해"
    assert len(parsed.paragraphs) >= 3


def test_parse_extracts_bible_refs(tmp_path: Path) -> None:
    p = tmp_path / "sermon.md"
    p.write_text(SAMPLE_MD, encoding="utf-8")
    parsed = parse_reference(p)
    assert any(ref.startswith("로마서 1장") for ref in parsed.bible_refs)


def test_parse_extracts_proper_nouns(tmp_path: Path) -> None:
    p = tmp_path / "sermon.md"
    p.write_text(SAMPLE_MD, encoding="utf-8")
    parsed = parse_reference(p)
    # English capitalised names should show up.
    assert any("John Calvin" in pn for pn in parsed.proper_nouns)
    # Quoted Korean term should also be a candidate.
    assert any("이신칭의" in pn for pn in parsed.proper_nouns)


def test_parse_picks_keywords_from_repeated_terms(tmp_path: Path) -> None:
    p = tmp_path / "sermon.md"
    p.write_text(SAMPLE_MD, encoding="utf-8")
    parsed = parse_reference(p)
    assert "복음" in parsed.keywords


def test_parse_rejects_unsupported_extension(tmp_path: Path) -> None:
    bogus = tmp_path / "sermon.docx"
    bogus.write_text("...", encoding="utf-8")
    with pytest.raises(ValueError):
        parse_reference(bogus)


def test_build_prompt_stays_short(tmp_path: Path) -> None:
    p = tmp_path / "sermon.md"
    p.write_text(SAMPLE_MD * 10, encoding="utf-8")
    parsed = parse_reference(p)
    prompt = build_reference_prompt(prompt_from_parsed(parsed))
    assert "한국어 설교" in prompt
    assert "로마서" in prompt
    assert len(prompt) <= 280


def test_alignment_returns_empty_for_empty_input() -> None:
    assert align_segments_to_reference([], ["paragraph"]) == []
    assert align_segments_to_reference(["seg"], []) == []


def test_alignment_matches_overlapping_text() -> None:
    refs = ["복음은 능력입니다", "은혜와 평강이 함께하기를"]
    segs = ["복음은 능력입니다", "전혀 무관한 잡담"]
    pairs = align_segments_to_reference(segs, refs, min_score=70.0)
    assert any(p.segment_index == 0 and p.reference_index == 0 for p in pairs)
