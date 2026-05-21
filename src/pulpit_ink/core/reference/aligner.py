"""Match STT segments to reference paragraphs by fuzzy similarity.

The aligner uses ``rapidfuzz.fuzz.partial_ratio`` so a long reference
paragraph still scores well against a short STT segment that happens to
quote a phrase from it. Pairs below ``min_score`` are dropped — they are
more noise than signal for the correction layer downstream.

``rapidfuzz`` is an optional dependency (the ``reference`` extra). When
it is not installed we fall back to ``difflib`` so the rest of the
pipeline keeps working in a CLI-only install.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

try:  # pragma: no cover - import guarded for optional dependency
    from rapidfuzz import fuzz as _fuzz

    def _similarity(a: str, b: str) -> float:
        return float(_fuzz.partial_ratio(a, b))
except ModuleNotFoundError:  # pragma: no cover - exercised in minimal installs
    from difflib import SequenceMatcher

    def _similarity(a: str, b: str) -> float:
        if not a or not b:
            return 0.0
        return SequenceMatcher(a=a, b=b).ratio() * 100.0


ScoreFn = Callable[[str, str], float]


@dataclass
class AlignmentPair:
    """A scored match between an STT segment and a reference paragraph."""

    segment_index: int
    reference_index: int
    score: float


def align_segments_to_reference(
    stt_segments: list[str],
    reference_paragraphs: list[str],
    min_score: float = 60.0,
    *,
    score_fn: ScoreFn | None = None,
) -> list[AlignmentPair]:
    """Greedy nearest-neighbour matching between segments and paragraphs.

    For each segment we pick the highest-scoring reference paragraph; if
    that score is below ``min_score`` the segment is skipped (no
    alignment forced for noisy STT output). ``score_fn`` exists for tests
    so they can plug in a deterministic comparator without depending on
    rapidfuzz.
    """

    if not stt_segments or not reference_paragraphs:
        return []

    sim: ScoreFn = score_fn or _similarity
    pairs: list[AlignmentPair] = []
    for i, segment in enumerate(stt_segments):
        if not segment or not segment.strip():
            continue
        best_index = -1
        best_score = 0.0
        for j, paragraph in enumerate(reference_paragraphs):
            score = sim(segment, paragraph)
            if score > best_score:
                best_score = score
                best_index = j
        if best_score >= min_score and best_index >= 0:
            pairs.append(AlignmentPair(i, best_index, best_score))
    return pairs
