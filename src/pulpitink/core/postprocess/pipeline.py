"""Top-level postprocess pipeline.

The pipeline fills ``clean_text`` for each segment without mutating
``raw_text``. Steps (in order):

1. Bible-reference normalisation (Sino-Korean numerals → arabic; collapse
   spaces between book name and chapter).
2. Lexicon substitution (default sermon/bible terms + user dictionary).
3. Whitespace cleanup (collapse repeated whitespace, strip).

Each step is idempotent so running the pipeline twice is safe.
"""

from __future__ import annotations

import re

from pulpitink.core.postprocess.bible_refs import normalise_bible_reference
from pulpitink.core.postprocess.lexicon import Lexicon, default_lexicon

_WHITESPACE_RE = re.compile(r"[ \t]{2,}")


def postprocess_text(text: str, *, lexicon: Lexicon | None = None) -> str:
    """Return the cleaned form of ``text``.

    Pass an explicit :class:`Lexicon` to layer a user dictionary on top of
    the defaults; omitting it uses :func:`default_lexicon`.
    """

    if not text or not text.strip():
        return ""
    lex = lexicon if lexicon is not None else default_lexicon()
    step1 = normalise_bible_reference(text)
    step2 = lex.apply(step1)
    step3 = _WHITESPACE_RE.sub(" ", step2).strip()
    return step3
