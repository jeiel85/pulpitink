from dataclasses import dataclass

from rapidfuzz import fuzz


@dataclass
class AlignmentPair:
    segment_index: int
    reference_index: int
    score: float


def align_segments_to_reference(
    stt_segments: list[str],
    reference_paragraphs: list[str],
    min_score: float = 60.0,
) -> list[AlignmentPair]:
    pairs: list[AlignmentPair] = []

    for i, segment in enumerate(stt_segments):
        best_index = -1
        best_score = 0.0

        for j, paragraph in enumerate(reference_paragraphs):
            score = fuzz.partial_ratio(segment, paragraph)
            if score > best_score:
                best_score = score
                best_index = j

        if best_score >= min_score:
            pairs.append(AlignmentPair(i, best_index, best_score))

    return pairs
