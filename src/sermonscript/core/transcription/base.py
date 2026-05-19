from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterable


@dataclass
class TranscriptSegment:
    start: float
    end: float
    text: str
    avg_logprob: float | None = None
    no_speech_prob: float | None = None
    speaker: str | None = None


@dataclass
class TranscriptionOptions:
    language: str | None = "ko"
    model_name: str = "medium"
    device: str = "auto"
    compute_type: str = "int8"
    beam_size: int = 5
    vad_filter: bool = True
    initial_prompt: str | None = None


class TranscriptionEngine(ABC):
    @abstractmethod
    def transcribe(
        self,
        audio_path: str,
        options: TranscriptionOptions,
    ) -> Iterable[TranscriptSegment]:
        raise NotImplementedError
