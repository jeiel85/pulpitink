"""faster-whisper backed STT engine."""

from __future__ import annotations

import logging
from collections.abc import Iterable
from pathlib import Path

from pulpit_ink.app.exceptions import TranscriptionError
from pulpit_ink.core.transcription.base import (
    TranscriptionEngine,
    TranscriptionOptions,
    TranscriptSegment,
)

logger = logging.getLogger("pulpit_ink.transcription.faster_whisper")


class FasterWhisperEngine(TranscriptionEngine):
    """Wraps :class:`faster_whisper.WhisperModel` behind the engine interface."""

    def __init__(
        self,
        model_name: str = "small",
        *,
        device: str = "auto",
        compute_type: str = "int8",
        download_root: str | Path | None = None,
    ) -> None:
        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:
            raise TranscriptionError(
                "faster-whisper 패키지를 불러올 수 없습니다. "
                "'pip install faster-whisper' 또는 'pip install -e .' 후 다시 시도하세요."
            ) from exc

        try:
            self.model = WhisperModel(
                model_name,
                device=device,
                compute_type=compute_type,
                download_root=str(download_root) if download_root else None,
            )
        except Exception as exc:  # noqa: BLE001 - surface as domain error
            raise TranscriptionError(
                f"Whisper 모델 '{model_name}' 로드에 실패했습니다: {exc}"
            ) from exc

        self.model_name = model_name

    def transcribe(
        self,
        audio_path: str | Path,
        options: TranscriptionOptions,
    ) -> Iterable[TranscriptSegment]:
        try:
            segments, _info = self.model.transcribe(
                str(audio_path),
                language=options.language,
                beam_size=options.beam_size,
                vad_filter=options.vad_filter,
                initial_prompt=options.initial_prompt,
            )
        except Exception as exc:  # noqa: BLE001
            raise TranscriptionError(f"STT 변환 중 오류가 발생했습니다: {exc}") from exc

        for seg in segments:
            yield TranscriptSegment(
                start=float(getattr(seg, "start", 0.0) or 0.0),
                end=float(getattr(seg, "end", 0.0) or 0.0),
                text=(getattr(seg, "text", "") or "").strip(),
                avg_logprob=getattr(seg, "avg_logprob", None),
                no_speech_prob=getattr(seg, "no_speech_prob", None),
            )
