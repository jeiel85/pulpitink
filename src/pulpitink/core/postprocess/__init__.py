"""Sermon postprocessing — produces ``clean_text`` from STT ``raw_text``.

The postprocess layer is intentionally conservative: it normalises a small
set of bible-reference phrasings and applies a curated lexicon (default
sermon/bible terms + an optional user dictionary). It never touches
``raw_text`` — the original STT output is immutable.

Public API:

* :class:`Lexicon` — a (preferred → original) mapping with default entries
  for common sermon/bible vocabulary plus optional user terms.
* :func:`normalise_bible_reference` — turns "로마서 일장 일절" into
  "로마서 1장 1절" and collapses spaces in book names like "고린도 전서".
* :func:`postprocess_text` — full pipeline: bible ref normalisation +
  lexicon substitution + whitespace cleanup.

Note: ``postprocess_text`` is what callers should use when filling
``clean_text``. Apply user-approved corrections separately into
``edited_text``.
"""

from pulpitink.core.postprocess.bible_refs import normalise_bible_reference
from pulpitink.core.postprocess.lexicon import (
    DEFAULT_BIBLE_BOOKS,
    DEFAULT_SERMON_TERMS,
    Lexicon,
    load_user_lexicon,
)
from pulpitink.core.postprocess.pipeline import postprocess_text

__all__ = [
    "DEFAULT_BIBLE_BOOKS",
    "DEFAULT_SERMON_TERMS",
    "Lexicon",
    "load_user_lexicon",
    "normalise_bible_reference",
    "postprocess_text",
]
