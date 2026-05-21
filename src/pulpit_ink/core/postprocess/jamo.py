"""Korean Jamo-based fuzzy matching utilities for STT error correction.

Uses NFD normalization and Choseong (initial consonant) extraction
combined with rapidfuzz to find phonetic near-matches for Korean nouns.
"""

from __future__ import annotations

import unicodedata
from collections.abc import Iterable
from difflib import SequenceMatcher

try:
    from rapidfuzz import fuzz
except ImportError:  # pragma: no cover - exercised in CI without [reference]
    fuzz = None

CHO_TABLE: tuple[str, ...] = (
    "ㄱ", "ㄲ", "ㄴ", "ㄷ", "ㄸ", "ㄹ", "ㅁ", "ㅂ", "ㅃ",
    "ㅅ", "ㅆ", "ㅇ", "ㅈ", "ㅉ", "ㅊ", "ㅋ", "ㅌ", "ㅍ", "ㅎ"
)

DEFAULT_STOP_WORDS: set[str] = {
    # 기존 불용어
    "에서", "하고", "그리고", "우리", "그의", "그들", "어떤", "또한", "으로", "로써", "로서",
    "에게", "한테", "하며", "했다", "한다", "하여", "때문", "대한", "대해", "위해", "위한",
    "아니", "모든", "가장", "같이", "같은", "이런", "저런", "그런",
    # 실사용 설교/강의용 다수 어미, 지시어, 조사 추가 보강
    "이다", "이며", "이고", "하는", "은", "는", "이", "가", "을", "를", "의", "와", "과", "에",
    "우리가", "그들의", "오늘", "지금", "그것", "이것", "저것", "어떻게", "그렇게", "이렇게", "저렇게",
    "하여튼", "아주", "매우", "너무", "진짜", "정말", "그녀", "너희", "너희가", "너희들", "그들가",
    "했다가", "하면서", "했으나", "했더니", "하더니", "하니까", "해서", "하니", "합니다"
}


def _ratio(a: str, b: str) -> float:
    if fuzz is not None:
        return fuzz.ratio(a, b) / 100.0
    return SequenceMatcher(None, a, b).ratio()


def jamo_seq(text: str) -> str:
    """Decompose Korean syllables into NFD jamo sequence and strip whitespace."""
    if not text:
        return ""
    decomposed = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in decomposed if not ch.isspace())


def choseong(text: str) -> str:
    """Extract Choseong (initial consonants) from Korean syllables and strip whitespace."""
    if not text:
        return ""
    nfc_text = unicodedata.normalize("NFC", text)
    out: list[str] = []
    for ch in nfc_text:
        code = ord(ch)
        if 0xAC00 <= code <= 0xD7A3:
            idx = (code - 0xAC00) // 588
            out.append(CHO_TABLE[idx])
        elif not ch.isspace():
            out.append(ch)
    return "".join(out)


def hybrid_similarity(a: str, b: str, weights: tuple[float, float] = (0.6, 0.4)) -> float:
    """Calculate phonetic similarity as a weighted sum of Jamo and Choseong ratios.

    Returns a float between 0.0 and 1.0.
    """
    jamo_a = jamo_seq(a)
    jamo_b = jamo_seq(b)
    cho_a = choseong(a)
    cho_b = choseong(b)

    if not jamo_a and not jamo_b:
        return 0.0

    ratio_score = _ratio(jamo_a, jamo_b)
    cho_score = _ratio(cho_a, cho_b)

    return weights[0] * ratio_score + weights[1] * cho_score


def find_fuzzy_matches(
    text: str,
    candidates: Iterable[str],
    threshold: float = 0.70,
    min_len: int = 3,
) -> list[tuple[str, str, float]]:
    """Scan `text` for phonetic near-matches of `candidates` using sliding windows.

    To prevent false positives:
    1. Candidates shorter than `min_len` are skipped.
    2. Jamo-level `fuzz.ratio` must be at least 0.50 (Double Pass).

    Returns a list of (found_snippet, candidate_word, similarity_score).
    """
    out: list[tuple[str, str, float]] = []
    # Deduplicate and filter candidates by length
    valid_candidates = sorted(
        {c.strip() for c in candidates if c and len(c.strip()) >= min_len},
        key=len,
        reverse=True
    )
    if not valid_candidates or not text or not text.strip():
        return []

    n = len(text)
    for candidate in valid_candidates:
        cand_len = len(candidate)
        best_score = 0.0
        best_snippet: str | None = None

        # Sliding window over the raw text. Window sizes range from len-1 to len+2.
        for w_len in range(max(1, cand_len - 1), min(n + 1, cand_len + 3)):
            for start in range(n - w_len + 1):
                sub = text[start : start + w_len].strip()
                if not sub:
                    continue
                if sub in DEFAULT_STOP_WORDS:
                    continue

                # 2글자 이하의 짧은 텍스트 조각에 대해 더 엄격한 자모 매칭 Double-pass 비율 적용
                min_j_ratio = 0.65 if len(sub) <= 2 else 0.50

                score = hybrid_similarity(sub, candidate)
                if score > best_score:
                    # Double-pass gate: raw jamo ratio must be >= min_j_ratio
                    j_ratio = _ratio(jamo_seq(sub), jamo_seq(candidate))
                    if j_ratio >= min_j_ratio:
                        best_score = score
                        best_snippet = sub

        # 최종 매칭 판단 시에도 2글자 이하면 더욱 보수적인 동적 임계값 가드 적용
        final_threshold = max(threshold, 0.78) if best_snippet and len(best_snippet) <= 2 else threshold
        if best_score >= final_threshold and best_snippet:
            out.append((best_snippet, candidate, best_score))

    return out
