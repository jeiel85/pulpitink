"""Unit tests for Korean Jamo-based fuzzy matching algorithm and utility functions."""

from __future__ import annotations

import unicodedata

import pytest

from pulpit_ink.core.postprocess import jamo
from pulpit_ink.core.postprocess.jamo import (
    choseong,
    find_fuzzy_matches,
    hybrid_similarity,
    jamo_seq,
)


def test_jamo_seq() -> None:
    # Basic NFD decomposition (without whitespace)
    assert jamo_seq("예수") == unicodedata.normalize("NFD", "예수")
    assert jamo_seq("예 수") == unicodedata.normalize("NFD", "예수")
    assert jamo_seq("그리스도") == unicodedata.normalize("NFD", "그리스도")
    assert jamo_seq("") == ""


def test_choseong() -> None:
    # Extract only initial consonants
    assert choseong("그리스도") == "ㄱㄹㅅㄷ"
    assert choseong("예수님") == "ㅇㅅㄴ"
    assert choseong("복음") == "ㅂㅇ"
    assert choseong("사도 바울") == "ㅅㄷㅂㅇ"
    # Keep non-hangul
    assert choseong("예수 123! A") == "ㅇㅅ123!A"
    assert choseong("") == ""


def test_hybrid_similarity() -> None:
    # Exact match should be 1.0
    assert hybrid_similarity("예수", "예수") == pytest.approx(1.0)

    # Sound-alike hangul should have high similarity
    assert hybrid_similarity("그리스도", "그리시도") > 0.85
    assert hybrid_similarity("그리스도", "크리스토") > 0.60
    assert hybrid_similarity("예수", "이에수") > 0.60

    # Completely different strings should have low similarity
    assert hybrid_similarity("예수", "여러분") < 0.50
    assert hybrid_similarity("그리스도", "기독교") < 0.60
    assert hybrid_similarity("", "") == 0.0


def test_hybrid_similarity_falls_back_without_rapidfuzz(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(jamo, "fuzz", None)

    assert hybrid_similarity("예수", "예수") == pytest.approx(1.0)
    assert hybrid_similarity("그리스도", "그리시도") > 0.80


def test_find_fuzzy_matches_length_gate() -> None:
    # 2-syllable candidates should be skipped in fuzzy matching
    text = "이에수께서 복음을 보궁이라 전하셨다"
    candidates = ["예수", "복음", "그리스도"]

    # "예수" and "복음" are 2 syllables -> skipped by length gate (min_len=3)
    # "그리스도" is 4 syllables -> evaluated (but not in text)
    matches = find_fuzzy_matches(text, candidates, threshold=0.70, min_len=3)
    assert len(matches) == 0


def test_find_fuzzy_matches_success() -> None:
    text = "그리시도 이에수 크리스토께서 말씀하셨다"
    candidates = ["그리스도", "예수 그리스도", "사도 바울"]

    # "그리스도" (4 syllables >= 3) -> matches "그리시도" or "크리스토"
    # "예수 그리스도" (7 syllables >= 3) -> matches "이에수 크리스토" (or similar sliding span)
    matches = find_fuzzy_matches(text, candidates, threshold=0.70, min_len=3)

    # Extract candidate names that were successfully matched
    matched_candidates = {cand for _, cand, _ in matches}

    assert "그리스도" in matched_candidates
    assert "사도 바울" not in matched_candidates

    # Verify exact snippet detection
    snippet_for_christ = [snip for snip, cand, _ in matches if cand == "그리스도"]
    assert "그리시도" in snippet_for_christ or "크리스토" in snippet_for_christ


def test_find_fuzzy_matches_stop_words_exclusion() -> None:
    # "에서"는 DEFAULT_STOP_WORDS에 포함되어 있어 "에스더" 후보 매칭 스캔 시 무시되어야 합니다.
    text = "우리가 그곳에서 머물렀다"
    candidates = ["에스더"]
    matches = find_fuzzy_matches(text, candidates, threshold=0.70, min_len=3)
    assert len(matches) == 0


def test_find_fuzzy_matches_extended_stop_words() -> None:
    # 새로 추가된 스톱워드 "하여튼", "진짜", "정말" 등이 스캔 시 스킵되는지 확인
    text = "진짜 하여튼 대단한 오늘"
    candidates = ["진실한", "하늘나라", "오늘날"]
    matches = find_fuzzy_matches(text, candidates, threshold=0.70, min_len=3)
    # 진짜 -> 진실한 (우연한 유사도 매치 가능하나 스톱워드로 스킵됨)
    # 하여튼 -> 하늘나라 (유사도 매칭 스킵됨)
    assert len(matches) == 0


def test_find_fuzzy_matches_short_snippet_tuning() -> None:
    # 2글자 이하의 짧은 조각("오늘", "지금")이 우연히 높은 유사도로 "오늘날", "지극히"와 오탐 매치되는 것을
    # 동적 임계값 가드(0.78) 및 Double-pass ratio(0.65)가 안전하게 차단하는지 확인
    text = "오늘 지금 그곳에 갔다"
    candidates = ["오늘날", "지극히"] # 각각 3글자이므로 min_len=3 게이트 통과

    # 2글자 조각 "오늘"과 "오늘날"의 hybrid_similarity는 약 0.76 (자모 5/7겹침)
    # 2글자 조각 "지금"과 "지극히"의 hybrid_similarity는 약 0.72
    # threshold가 0.70일 때, 2글자 이하 동적 가드가 없다면 오탐 매칭 발생함
    matches = find_fuzzy_matches(text, candidates, threshold=0.70, min_len=3)

    # 동적 임계치(0.78)에 의해 2글자 조각 오탐은 모두 걸러져야 함
    assert len(matches) == 0


