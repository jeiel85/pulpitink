"""Tests for the HeuristicDiarizer."""

from __future__ import annotations

from pulpit_ink.core.postprocess.diarizer import HeuristicDiarizer
from pulpit_ink.core.transcription.base import TranscriptSegment


def test_diarizer_assigns_speakers_dicts() -> None:
    diarizer = HeuristicDiarizer(gap_threshold=1.5)
    segments = [
        {"start_sec": 0.0, "end_sec": 1.0},
        {"start_sec": 2.0, "end_sec": 3.0},  # gap: 1.0s (<= 1.5s, no switch)
        {"start_sec": 5.0, "end_sec": 6.0},  # gap: 2.0s (> 1.5s, switch to Speaker 2)
        {"start_sec": 7.0, "end_sec": 8.0},  # gap: 1.0s (<= 1.5s, no switch)
        {"start_sec": 10.0, "end_sec": 11.0},  # gap: 2.0s (> 1.5s, switch back to Speaker 1)
    ]

    result = diarizer.assign_speakers(segments)
    assert result[0]["speaker"] == "화자 1"
    assert result[1]["speaker"] == "화자 1"
    assert result[2]["speaker"] == "화자 2"
    assert result[3]["speaker"] == "화자 2"
    assert result[4]["speaker"] == "화자 1"


def test_diarizer_assigns_speakers_transcript_segments() -> None:
    diarizer = HeuristicDiarizer(gap_threshold=1.5)
    segments = [
        TranscriptSegment(start=0.0, end=1.0, text="A"),
        TranscriptSegment(start=2.0, end=3.0, text="B"),  # gap: 1.0s, same
        TranscriptSegment(start=5.0, end=6.0, text="C"),  # gap: 2.0s, switch to 2
        TranscriptSegment(start=7.0, end=8.0, text="D"),  # gap: 1.0s, same
        TranscriptSegment(start=10.0, end=11.0, text="E"),  # gap: 2.0s, switch to 1
    ]

    result = diarizer.assign_speakers_to_segments(segments)
    assert result[0].speaker == "화자 1"
    assert result[1].speaker == "화자 1"
    assert result[2].speaker == "화자 2"
    assert result[3].speaker == "화자 2"
    assert result[4].speaker == "화자 1"


def test_diarizer_handles_empty_inputs() -> None:
    diarizer = HeuristicDiarizer()
    assert diarizer.assign_speakers([]) == []
    assert diarizer.assign_speakers_to_segments([]) == []
