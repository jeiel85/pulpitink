"""Heuristic Speaker Diarizer for PulpitInk.

Estimates speakers for transcription segments based on the time gaps between utterances,
avoiding complex and heavy neural models in favor of lightweight local desktop execution.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pulpitink.core.transcription.base import TranscriptSegment

logger = logging.getLogger("pulpitink.diarizer")


class HeuristicDiarizer:
    """Heuristically segments and assigns speaker labels (e.g. '화자 1', '화자 2').

    It assumes a speaker switch when the gap between consecutive utterances is larger
    than a specified threshold (default: 1.5 seconds).
    """

    def __init__(self, gap_threshold: float = 1.5) -> None:
        self.gap_threshold = gap_threshold

    def assign_speakers(self, segments: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Assign speaker IDs to segment list dicts in place.

        Each segment dict is expected to have 'start_sec' and 'end_sec' float values.
        Adds or updates 'speaker' key.
        """
        if not segments:
            return segments

        current_speaker_idx = 1
        last_end = segments[0].get("end_sec", 0.0)

        # Initialize the first segment's speaker
        segments[0]["speaker"] = f"화자 {current_speaker_idx}"

        for i in range(1, len(segments)):
            seg = segments[i]
            start = seg.get("start_sec", 0.0)
            end = seg.get("end_sec", 0.0)

            # Heuristics: if gap is larger than 1.5s, toggle the speaker
            if (start - last_end) > self.gap_threshold:
                current_speaker_idx = 3 - current_speaker_idx  # Switches between 1 and 2

            seg["speaker"] = f"화자 {current_speaker_idx}"
            last_end = end

        logger.info("Heuristic diarizer completed speaker assignments for %d dict segments.", len(segments))
        return segments

    def assign_speakers_to_segments(self, segments: list[TranscriptSegment]) -> list[TranscriptSegment]:
        """Assign speaker IDs to TranscriptSegment objects in place."""
        if not segments:
            return segments

        current_speaker_idx = 1
        last_end = segments[0].end

        segments[0].speaker = f"화자 {current_speaker_idx}"

        for i in range(1, len(segments)):
            seg = segments[i]
            # Heuristics: if gap is larger than 1.5s, toggle the speaker
            if (seg.start - last_end) > self.gap_threshold:
                current_speaker_idx = 3 - current_speaker_idx

            seg.speaker = f"화자 {current_speaker_idx}"
            last_end = seg.end

        logger.info("Heuristic diarizer completed speaker assignments for %d TranscriptSegment objects.", len(segments))
        return segments
