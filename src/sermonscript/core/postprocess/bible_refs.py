"""Normalise Korean bible references inside transcribed text.

Whisper tends to spell numerals in Sino-Korean readings:

    로마서 일장 일절   →  로마서 1장 1절
    창세기 삼장 십육절 →  창세기 3장 16절

It also occasionally splits compound book names with a space (e.g.
*고린도 전서*). The lexicon handles those — this module focuses on the
numeral side, plus the *장 N절* / *N절 ~ M절* range form.

The normaliser only fires on contexts that already look like a bible
reference (book name nearby, or 장/절 markers present). Free text is left
alone.
"""

from __future__ import annotations

import re

from sermonscript.core.postprocess.lexicon import BIBLE_REF_RE

# Sino-Korean numeral atoms. We deliberately keep the mapping short and
# build composite numbers (e.g. 이십삼 = 23) with the helper below.
_SINO_DIGITS: dict[str, int] = {
    "영": 0,
    "공": 0,
    "일": 1,
    "이": 2,
    "삼": 3,
    "사": 4,
    "오": 5,
    "육": 6,
    "칠": 7,
    "팔": 8,
    "구": 9,
}

_TENS_PIECE = "(?:[일이삼사오육칠팔구]?십)"  # 십, 일십…구십
_ONES_PIECE = "(?:[일이삼사오육칠팔구])"
_HUNDREDS_PIECE = "(?:[일이삼사오육칠팔구]?백)"

# Up to "삼백이십일" — sufficient for any bible chapter/verse.
SINO_NUMBER_RE = re.compile(
    rf"(?:{_HUNDREDS_PIECE})?(?:{_TENS_PIECE})?(?:{_ONES_PIECE})?"
)


def _sino_to_int(token: str) -> int | None:
    """Convert a contiguous Sino-Korean numeral token into ``int``.

    Returns ``None`` if the token has no recognised digits (so we don't
    rewrite plain Hangul like "일"/"이" that wasn't part of a number
    phrase).
    """

    if not token:
        return None

    total = 0
    rest = token

    # Hundreds
    m = re.match(rf"({_ONES_PIECE})?백", rest)
    if m:
        prefix = m.group(1)
        total += (_SINO_DIGITS[prefix] if prefix else 1) * 100
        rest = rest[m.end():]

    # Tens
    m = re.match(rf"({_ONES_PIECE})?십", rest)
    if m:
        prefix = m.group(1)
        total += (_SINO_DIGITS[prefix] if prefix else 1) * 10
        rest = rest[m.end():]

    # Ones
    if rest:
        digit = _SINO_DIGITS.get(rest)
        if digit is None:
            return None
        total += digit

    return total if total > 0 or token in {"영", "공"} else None


# Matches a Sino-Korean numeral attached to a 장/절 unit (with optional spaces).
_CHAPTER_RE = re.compile(
    r"([일이삼사오육칠팔구십백]+)\s*장"
)
_VERSE_RE = re.compile(
    r"([일이삼사오육칠팔구십백]+)\s*절"
)


def _replace_chapter(match: re.Match[str]) -> str:
    token = match.group(1)
    value = _sino_to_int(token)
    if value is None:
        return match.group(0)
    return f"{value}장"


def _replace_verse(match: re.Match[str]) -> str:
    token = match.group(1)
    value = _sino_to_int(token)
    if value is None:
        return match.group(0)
    return f"{value}절"


# Catches "로마서  1장 1절" (extra whitespace) and tightens it.
_BOOK_SPACING_RE = re.compile(rf"({BIBLE_REF_RE.pattern})\s+(\d+\s*장)")


def normalise_bible_reference(text: str) -> str:
    """Return ``text`` with bible references normalised.

    Behaviour:

    * Sino-Korean numerals immediately before *장* or *절* are rewritten to
      arabic numerals (예: ``일장 일절`` → ``1장 1절``).
    * Book name → chapter spacing is collapsed to a single space.
    * Numeric chapter/verse already in arabic form is left as-is.

    The transformation is conservative: stand-alone numerals never get
    rewritten — they must be attached to 장/절 to count.
    """

    if not text:
        return text

    out = _CHAPTER_RE.sub(_replace_chapter, text)
    out = _VERSE_RE.sub(_replace_verse, out)
    out = _BOOK_SPACING_RE.sub(lambda m: f"{m.group(1)} {m.group(2).replace(' ', '')}", out)
    return out
