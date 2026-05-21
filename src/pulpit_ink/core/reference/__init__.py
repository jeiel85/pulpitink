"""Sermon reference handling — parse, align, prompt, suggest.

This package consumes a TXT/Markdown sermon script and produces:

* :class:`~pulpit_ink.core.reference.parser.ParsedReference` — structured
  view (title, bible refs, keywords, proper nouns).
* :func:`build_reference_prompt` — short faster-whisper initial_prompt
  built from the parsed key terms (never the full text).
* :func:`align_segments_to_reference` — best-effort similarity links
  between STT segments and reference paragraphs.
* :class:`~pulpit_ink.core.reference.corrections.CorrectionEngine` —
  pending correction suggestions for the user to apply or ignore.
"""

from pulpit_ink.core.reference.aligner import (
    AlignmentPair,
    align_segments_to_reference,
)
from pulpit_ink.core.reference.corrections import (
    CorrectionCandidate,
    CorrectionEngine,
    apply_correction_to_segment,
)
from pulpit_ink.core.reference.parser import (
    SUPPORTED_REFERENCE_EXTENSIONS,
    ParsedReference,
    parse_reference,
    read_reference_file,
)
from pulpit_ink.core.reference.prompt_builder import (
    ReferencePrompt,
    build_reference_prompt,
    prompt_from_parsed,
)

__all__ = [
    "AlignmentPair",
    "CorrectionCandidate",
    "CorrectionEngine",
    "ParsedReference",
    "ReferencePrompt",
    "SUPPORTED_REFERENCE_EXTENSIONS",
    "align_segments_to_reference",
    "apply_correction_to_segment",
    "build_reference_prompt",
    "parse_reference",
    "prompt_from_parsed",
    "read_reference_file",
]
