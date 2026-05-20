"""Build a short faster-whisper ``initial_prompt`` from a reference doc.

The principle in Goal 3 is *primer, not script*: we deliberately keep the
prompt small (≤ ~250 chars in practice) so the STT engine learns the
sermon's vocabulary without being tempted to echo the prepared text back
when the speaker improvises.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from pulpitink.core.reference.parser import ParsedReference

MAX_PROMPT_BIBLE_REFS = 5
MAX_PROMPT_TERMS = 25
MAX_PROMPT_CHARS = 280


@dataclass
class ReferencePrompt:
    """Inputs feeding :func:`build_reference_prompt`."""

    title: str | None = None
    bible_refs: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    custom_terms: list[str] = field(default_factory=list)


def prompt_from_parsed(parsed: ParsedReference) -> ReferencePrompt:
    """Project a :class:`ParsedReference` into the prompt input dataclass."""

    return ReferencePrompt(
        title=parsed.title,
        bible_refs=list(parsed.bible_refs),
        keywords=list(parsed.keywords),
        custom_terms=list(parsed.proper_nouns),
    )


def build_reference_prompt(ref: ReferencePrompt) -> str:
    """Return a compact Korean STT prompt with only the essential vocabulary.

    The output is capped at :data:`MAX_PROMPT_CHARS` so it never grows into
    the prepared-text territory. Order: header → title → bible refs →
    terms.
    """

    lines: list[str] = [
        "이 음성은 한국어 설교입니다.",
        "성경책 이름, 장절, 인명, 신학 용어를 정확히 기록합니다.",
    ]
    if ref.title:
        lines.append(f"설교 제목: {ref.title}")
    if ref.bible_refs:
        lines.append("성경 본문: " + ", ".join(ref.bible_refs[:MAX_PROMPT_BIBLE_REFS]))

    terms: list[str] = []
    for term in (*ref.keywords, *ref.custom_terms):
        if term and term not in terms:
            terms.append(term)
    terms = terms[:MAX_PROMPT_TERMS]
    if terms:
        lines.append("주요 용어: " + ", ".join(terms))

    prompt = "\n".join(lines)
    if len(prompt) > MAX_PROMPT_CHARS:
        prompt = prompt[:MAX_PROMPT_CHARS].rstrip()
    return prompt
