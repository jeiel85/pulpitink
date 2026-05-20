"""Parse a TXT/Markdown sermon reference into structured fields.

The reference document is the user-supplied script for the sermon being
transcribed. Goal 3 uses it for two things:

1. Building a short ``initial_prompt`` for faster-whisper (using key terms
   only — never the full text, which would prime the model to hallucinate
   text the speaker didn't actually say).
2. Generating *pending* correction suggestions (bible references, proper
   nouns, user dictionary hits). The user reviews each suggestion in the
   editor and decides whether to apply it.

The parser is intentionally lenient: any UTF-8 text file is acceptable
input. Markdown ``#`` headers, the first non-empty line, and the
filename together determine the title. Bible references are extracted
with a permissive regex (book name + chapter[+verse]). Keywords are
distinct lemma-ish tokens of 2+ Hangul characters that occur more than
once. Proper-noun candidates are sequences of CamelCase or capitalised
words plus quoted strings.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from sermonscript.core.postprocess.lexicon import (
    DEFAULT_BIBLE_BOOKS,
    DEFAULT_SERMON_TERMS,
)

SUPPORTED_REFERENCE_EXTENSIONS: frozenset[str] = frozenset({".txt", ".md", ".markdown"})

_BOOK_PATTERN = "(?:" + "|".join(
    re.escape(name) for name in sorted(DEFAULT_BIBLE_BOOKS.keys(), key=len, reverse=True)
) + ")"
_BIBLE_REF_RE = re.compile(
    rf"{_BOOK_PATTERN}\s*(\d+)\s*장(?:\s*(\d+)\s*(?:절(?:\s*[-~]\s*(\d+)\s*절)?)?)?"
)

_HANGUL_WORD_RE = re.compile(r"[가-힣]{2,}")
_PROPER_NOUN_RE = re.compile(
    r"[A-Z][A-Za-z0-9]+(?:\s+[A-Z][A-Za-z0-9]+)*"
)
_QUOTED_RE = re.compile(r"[\"'“”‘’]([^\"'“”‘’\n]{2,30})[\"'“”‘’]")

# Words we never want to surface as "keywords" — too generic to help STT.
_STOPWORDS: frozenset[str] = frozenset(
    {
        "그리고",
        "그러나",
        "그래서",
        "그러므로",
        "하지만",
        "또한",
        "또는",
        "오늘",
        "우리",
        "여러분",
        "말씀",
        "그것",
        "이것",
        "저것",
        "있는",
        "있다",
        "없다",
        "합니다",
        "있습니다",
        "없습니다",
        "되었습니다",
        "되었다",
        "위해",
        "통해",
        "사람",
        "하나",
        "정말",
        "다시",
        "이런",
        "저런",
        "어떤",
        "모든",
    }
)


@dataclass
class ParsedReference:
    """Structured view of a sermon reference document."""

    source_path: Path
    title: str | None
    content: str
    paragraphs: list[str] = field(default_factory=list)
    bible_refs: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    proper_nouns: list[str] = field(default_factory=list)


def read_reference_file(path: Path | str) -> str:
    """Read a TXT/Markdown file with UTF-8 (BOM-tolerant) decoding."""

    p = Path(path)
    if not p.exists() or not p.is_file():
        raise FileNotFoundError(f"원문 파일을 찾을 수 없습니다: {p}")
    ext = p.suffix.lower()
    if ext not in SUPPORTED_REFERENCE_EXTENSIONS:
        raise ValueError(
            f"원문 파일은 .txt / .md 형식이어야 합니다 (현재: {ext or '확장자 없음'})"
        )
    # utf-8-sig transparently strips BOMs Windows editors add.
    return p.read_text(encoding="utf-8-sig")


def _split_paragraphs(text: str) -> list[str]:
    blocks = re.split(r"\n\s*\n", text)
    paragraphs: list[str] = []
    for block in blocks:
        cleaned = block.strip()
        if not cleaned:
            continue
        # Drop Markdown header markup ("# Title").
        cleaned = re.sub(r"^#{1,6}\s*", "", cleaned)
        paragraphs.append(cleaned)
    return paragraphs


def _extract_title(text: str, fallback: str) -> str | None:
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        m = re.match(r"^#{1,6}\s*(.+)$", stripped)
        if m:
            return m.group(1).strip()
        return stripped[:120]
    return fallback or None


def _extract_bible_refs(text: str) -> list[str]:
    found: list[str] = []
    for m in _BIBLE_REF_RE.finditer(text):
        book_match = re.match(_BOOK_PATTERN, m.group(0))
        if book_match is None:
            continue
        book = book_match.group(0)
        chapter = m.group(1)
        verse_start = m.group(2)
        verse_end = m.group(3)
        if verse_start and verse_end:
            ref = f"{book} {chapter}장 {verse_start}-{verse_end}절"
        elif verse_start:
            ref = f"{book} {chapter}장 {verse_start}절"
        else:
            ref = f"{book} {chapter}장"
        if ref not in found:
            found.append(ref)
    return found


def _extract_keywords(text: str, *, top_k: int = 30) -> list[str]:
    tokens = _HANGUL_WORD_RE.findall(text)
    counts = Counter(tok for tok in tokens if tok not in _STOPWORDS)
    # Bias toward terms the postprocess lexicon already knows about — they
    # are exactly the kind of vocabulary we want to anchor STT against.
    for canonical in DEFAULT_SERMON_TERMS:
        if canonical in text and canonical not in counts:
            counts[canonical] = 1
    return [tok for tok, n in counts.most_common(top_k) if n >= 1]


def _extract_proper_nouns(text: str) -> list[str]:
    candidates: list[str] = []
    for m in _PROPER_NOUN_RE.finditer(text):
        token = m.group(0).strip()
        if 2 <= len(token) <= 40 and token not in candidates:
            candidates.append(token)
    for m in _QUOTED_RE.finditer(text):
        token = m.group(1).strip()
        if 2 <= len(token) <= 40 and token not in candidates:
            candidates.append(token)
    return candidates


def parse_reference(path: Path | str) -> ParsedReference:
    """Read and parse a reference document into :class:`ParsedReference`."""

    p = Path(path)
    content = read_reference_file(p)
    paragraphs = _split_paragraphs(content)
    title = _extract_title(content, fallback=p.stem)
    bible_refs = _extract_bible_refs(content)
    keywords = _extract_keywords(content)
    proper_nouns = _extract_proper_nouns(content)
    return ParsedReference(
        source_path=p,
        title=title,
        content=content,
        paragraphs=paragraphs,
        bible_refs=bible_refs,
        keywords=keywords,
        proper_nouns=proper_nouns,
    )
