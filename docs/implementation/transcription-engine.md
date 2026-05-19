# Transcription Engine

## Engine Strategy

The first implementation should use `faster-whisper`.

Reasons:

- Good Python integration
- Faster than baseline Whisper in many setups
- Supports CPU/GPU execution
- Supports quantized compute types
- Compatible with Whisper model families

A later optional engine can use `whisper.cpp` for CPU-friendly and portable builds.

## Engine Interface

```python
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
    def transcribe(self, audio_path: str, options: TranscriptionOptions) -> Iterable[TranscriptSegment]:
        raise NotImplementedError
```

## Model Policy

| Purpose | Model |
|---|---|
| Quick test | tiny |
| Low-spec PC | base |
| Balanced | small |
| Sermon default | medium |
| Accuracy-first | large-v3 |

Do not hard-code accuracy promises. Actual results vary by recording quality, language, speaker, model, preprocessing, and hardware.
