"""Generate pending correction suggestions for review.

The correction layer is **never** allowed to silently rewrite ``edited_text``.
Each suggestion is recorded as ``pending`` in the DB; the user explicitly
applies or ignores it from the editor.

Three kinds of suggestions are produced:

* ``bible_ref`` — Whisper wrote ``로마서 일장 일절``; we suggest
  ``로마서 1장 1절``.
* ``proper_noun`` — A proper noun from the reference document (or the
  user dictionary) appears as a near-match in the segment with the wrong
  spacing/spelling.
* ``user_dict`` — A canonical term from the user dictionary appears in
  its known wrong form inside the segment.

The engine compares **raw_text** to its postprocessed counterpart and
only emits a suggestion when the two differ. That keeps the loop honest:
if postprocess could not improve the text, we have nothing to suggest.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from pulpitink.core.postprocess.bible_refs import normalise_bible_reference
from pulpitink.core.postprocess.lexicon import (
    DEFAULT_BIBLE_BOOKS,
    Lexicon,
    default_lexicon,
)
from pulpitink.core.reference.parser import ParsedReference


@dataclass(frozen=True)
class CorrectionCandidate:
    """A single suggestion produced by :class:`CorrectionEngine`."""

    segment_index: int
    kind: str
    original_text: str
    suggested_text: str
    source: str


_BIBLE_BOOK_NAMES: frozenset[str] = frozenset(DEFAULT_BIBLE_BOOKS.keys())


def _has_bible_book(text: str) -> bool:
    return any(book in text for book in _BIBLE_BOOK_NAMES)


class CorrectionEngine:
    """Produce ``CorrectionCandidate`` objects for a transcript.

    Parameters
    ----------
    lexicon:
        Sermon/bible lexicon, optionally merged with a user dictionary.
        Defaults to :func:`default_lexicon`.
    proper_nouns:
        Extra proper nouns (typically from the reference document) that
        should also drive ``proper_noun``-kind suggestions when a
        slightly mangled form shows up in the STT output.
    """

    def __init__(
        self,
        *,
        lexicon: Lexicon | None = None,
        proper_nouns: Iterable[str] = (),
        fuzzy_matching_enabled: bool = True,
        fuzzy_threshold: float = 0.70,
    ) -> None:
        self._lexicon = lexicon if lexicon is not None else default_lexicon()
        self._proper_nouns: tuple[str, ...] = tuple(
            sorted({n.strip() for n in proper_nouns if n and n.strip()}, key=len, reverse=True)
        )
        self.fuzzy_matching_enabled = fuzzy_matching_enabled
        self.fuzzy_threshold = fuzzy_threshold

    @classmethod
    def from_reference(
        cls,
        parsed: ParsedReference | None,
        *,
        lexicon: Lexicon | None = None,
        fuzzy_matching_enabled: bool = True,
        fuzzy_threshold: float = 0.70,
    ) -> CorrectionEngine:
        """Build an engine seeded with the reference's proper nouns."""

        if parsed is None:
            return cls(
                lexicon=lexicon,
                fuzzy_matching_enabled=fuzzy_matching_enabled,
                fuzzy_threshold=fuzzy_threshold,
            )
        return cls(
            lexicon=lexicon,
            proper_nouns=parsed.proper_nouns,
            fuzzy_matching_enabled=fuzzy_matching_enabled,
            fuzzy_threshold=fuzzy_threshold,
        )

    def suggestions_for(self, segment_index: int, text: str) -> list[CorrectionCandidate]:
        """Return correction candidates for a single segment's raw text.

        The engine emits at most one suggestion per (kind, original_text)
        pair so the GUI doesn't drown the user in duplicates.
        """

        if not text or not text.strip():
            return []

        out: list[CorrectionCandidate] = []
        seen: set[tuple[str, str]] = set()

        def add(kind: str, original: str, suggested: str, source: str) -> None:
            if original == suggested:
                return
            key = (kind, original)
            if key in seen:
                return
            seen.add(key)
            out.append(
                CorrectionCandidate(
                    segment_index=segment_index,
                    kind=kind,
                    original_text=original,
                    suggested_text=suggested,
                    source=source,
                )
            )

        # 1) Bible-reference normalisation. The numerals regex is already
        # narrow (it only matches Sino-Korean digits immediately followed
        # by 장 / 절), which is essentially always a bible reference in a
        # sermon transcript. Whisper sometimes splits the book name with
        # a space, so we also check the lex-substituted form before
        # deciding the text "looks like" a bible reference.
        lex_text = self._lexicon.apply(text)
        normalised = normalise_bible_reference(text)
        if normalised != text and (
            _has_bible_book(text) or _has_bible_book(lex_text) or normalised != lex_text
        ):
            add("bible_ref", text, normalised, "postprocess")

        # 2) Lexicon-driven substitutions (default lexicon + user dict).
        for canonical, wrong_forms in self._lexicon.items():
            for wrong in wrong_forms:
                if wrong and wrong in text:
                    add("user_dict", wrong, canonical, "lexicon")

        # 3) Proper-noun fuzzy match. Specifically: if the reference doc
        # mentions "John Smith" and the STT wrote "John  smith" (extra
        # spaces / different case), we propose the canonical spelling.
        lowered = text.lower()
        for name in self._proper_nouns:
            if not name:
                continue
            if name in text:
                continue  # already correct
            squeezed = "".join(name.split()).lower()
            if not squeezed:
                continue
            if squeezed in lowered.replace(" ", ""):
                # Find the snippet in ``text`` that maps to ``name``.
                snippet = _locate_proper_noun_snippet(text, name)
                if snippet:
                    add("proper_noun", snippet, name, "reference")

        # 4) Korean Jamo-based Fuzzy match (Proper Nouns and Lexicon Canonical terms)
        if self.fuzzy_matching_enabled:
            from pulpitink.core.postprocess.jamo import find_fuzzy_matches
            candidates = list(self._proper_nouns) + list(self._lexicon.entries.keys())
            matches = find_fuzzy_matches(
                text=text,
                candidates=candidates,
                threshold=self.fuzzy_threshold,
            )
            for snippet, candidate, score in matches:
                if candidate in text:
                    continue
                add("proper_noun", snippet, candidate, f"reference+fuzzy:{score:.2f}")

        return out


def _locate_proper_noun_snippet(text: str, name: str) -> str | None:
    """Find the substring of ``text`` that corresponds to ``name``.

    We strip whitespace from both sides and compare lowercase to lowercase.
    Returns ``None`` when we can't pin down the exact span.
    """

    squeezed_name = "".join(name.split()).lower()
    n = len(squeezed_name)
    if n == 0:
        return None
    lowered = text.lower()
    flat = lowered.replace(" ", "")
    if squeezed_name not in flat:
        return None
    # Walk over ``text`` and accumulate non-space characters until we hit
    # ``n`` characters that match ``squeezed_name``.
    start: int | None = None
    matched = 0
    for i, ch in enumerate(lowered):
        if ch.isspace():
            if start is not None and matched > 0 and squeezed_name.startswith(
                lowered[start:i].replace(" ", "")
            ):
                continue
            continue
        if start is None:
            if ch == squeezed_name[0]:
                start = i
                matched = 1
                if matched == n:
                    return text[start : i + 1]
            continue
        if ch == squeezed_name[matched]:
            matched += 1
            if matched == n:
                return text[start : i + 1]
        else:
            start = i if ch == squeezed_name[0] else None
            matched = 1 if start is not None else 0
    return None


def apply_correction_to_segment(
    *,
    raw_text: str,
    clean_text: str,
    edited_text: str,
    original: str,
    suggested: str,
) -> str:
    """Apply an accepted correction to ``edited_text``.

    Decision tree:

    1. If the *base* (``edited_text`` → ``clean_text`` → ``raw_text``)
       contains ``original``, replace the first occurrence in place.
    2. Otherwise, if ``suggested`` is already present in the base, the
       postprocess pipeline (or a prior application) has already done
       the work — keep the base unchanged. Applying the suggestion is
       still useful: it materialises the existing clean form into
       ``edited_text`` at the caller level.
    3. Otherwise, if ``original`` is in ``raw_text``, rebuild the
       corrected form from ``raw_text`` so we don't drop the surrounding
       sentence.
    4. Final fallback: return ``suggested`` alone (the caller is
       intentionally swapping the entire segment).
    """

    base = edited_text or clean_text or raw_text
    if original and original in base:
        return base.replace(original, suggested, 1)
    if suggested and suggested in base:
        return base
    if original and original in raw_text:
        return raw_text.replace(original, suggested, 1)
    return suggested
