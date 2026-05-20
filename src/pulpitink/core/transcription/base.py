"""Engine-agnostic interfaces for the STT layer.

The CLI and the GUI both consume this module, so it must not import any
heavyweight engine (faster-whisper, whisper.cpp, …) at module load time.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class TranscriptSegment:
    """A single STT segment.

    The text fields follow the priority described in
    ``docs/transcription-pipeline.md``: when exporting, prefer ``edited_text``
    if present, fall back to ``clean_text`` (post-processed), and finally
    ``raw_text`` (original STT output).
    """

    start: float
    end: float
    text: str
    avg_logprob: float | None = None
    no_speech_prob: float | None = None
    speaker: str | None = None
    clean_text: str = ""
    edited_text: str = ""

    @property
    def raw_text(self) -> str:
        return self.text

    def to_dict(self) -> dict:
        return {
            "start": round(self.start, 3),
            "end": round(self.end, 3),
            "raw_text": self.raw_text,
            "clean_text": self.clean_text,
            "edited_text": self.edited_text,
            "avg_logprob": self.avg_logprob,
            "no_speech_prob": self.no_speech_prob,
            "speaker": self.speaker,
        }


def segment_display_text(seg: TranscriptSegment) -> str:
    """Return the best available text for export.

    Order: edited_text > clean_text > raw_text.
    """

    if seg.edited_text and seg.edited_text.strip():
        return seg.edited_text
    if seg.clean_text and seg.clean_text.strip():
        return seg.clean_text
    return seg.raw_text


@dataclass
class TranscriptionOptions:
    """Options forwarded to the underlying engine."""

    language: str | None = "ko"
    model_name: str = "small"
    device: str = "auto"
    compute_type: str = "int8"
    beam_size: int = 5
    vad_filter: bool = True
    initial_prompt: str | None = None


@dataclass
class TranscriptionResult:
    """A single STT run as consumed by the exporter and CLI."""

    source_path: Path
    audio_path: Path
    language: str | None
    model_name: str
    preset: str
    segments: list[TranscriptSegment] = field(default_factory=list)
    duration: float | None = None

    @property
    def full_text(self) -> str:
        return "\n".join(segment_display_text(seg) for seg in self.segments)


class TranscriptionEngine(ABC):
    """Common interface for STT engines."""

    @abstractmethod
    def transcribe(
        self,
        audio_path: str | Path,
        options: TranscriptionOptions,
    ) -> Iterable[TranscriptSegment]:
        raise NotImplementedError
