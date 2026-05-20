"""Pipeline that ties preprocessing + STT + export together.

The CLI is intentionally a thin shell on top of this module — the GUI in a
later milestone will call the same entry points.
"""

from __future__ import annotations

import logging
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from sermonscript.app.exceptions import (
    SermonScriptError,
    UnsupportedFormatError,
)
from sermonscript.core.audio.enhancement_presets import get_preset
from sermonscript.core.audio.ffmpeg_runner import DEFAULT_PRESET, FFmpegRunner
from sermonscript.core.export.base import ExportFormat
from sermonscript.core.export.pipeline import ExportPipeline
from sermonscript.core.transcription.base import (
    TranscriptionEngine,
    TranscriptionOptions,
    TranscriptionResult,
    TranscriptSegment,
)

logger = logging.getLogger("sermonscript.services.transcribe")

SUPPORTED_INPUT_EXTENSIONS: frozenset[str] = frozenset(
    {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg", ".mp4"}
)

ProgressCallback = Callable[[str], None]


@dataclass
class TranscribeRequest:
    input_path: Path
    output_dir: Path
    language: str | None = "ko"
    model: str = "small"
    preset: str = DEFAULT_PRESET
    formats: tuple[ExportFormat, ...] = (
        ExportFormat.TXT,
        ExportFormat.JSON,
        ExportFormat.MD,
        ExportFormat.SRT,
        ExportFormat.VTT,
    )
    device: str = "auto"
    compute_type: str = "int8"
    beam_size: int = 5
    vad_filter: bool = True
    initial_prompt: str | None = None
    cache_root: Path = Path("cache") / "jobs"
    job_id: str | None = None


@dataclass
class TranscribeResult:
    job_id: str
    processed_audio: Path
    exports: list[Path] = field(default_factory=list)
    transcription: TranscriptionResult | None = None
    elapsed_seconds: float = 0.0


def new_job_id() -> str:
    """Return a short, filesystem-safe identifier for one transcription run."""

    return uuid.uuid4().hex[:12]


def validate_input_path(path: Path) -> Path:
    """Resolve and validate a user-supplied audio path."""

    if not path.exists():
        raise SermonScriptError(f"입력 파일을 찾을 수 없습니다: {path}")
    if not path.is_file():
        raise SermonScriptError(f"입력 경로가 파일이 아닙니다: {path}")

    suffix = path.suffix.lower()
    if suffix not in SUPPORTED_INPUT_EXTENSIONS:
        supported = ", ".join(sorted(SUPPORTED_INPUT_EXTENSIONS))
        raise UnsupportedFormatError(
            f"지원하지 않는 확장자입니다: {suffix or '(확장자 없음)'}. 지원: {supported}"
        )
    return path.resolve()


def _build_engine(model: str, device: str, compute_type: str) -> TranscriptionEngine:
    # Local import keeps the heavy CT2 dependency optional at module-load time.
    from sermonscript.core.transcription.faster_whisper_engine import FasterWhisperEngine

    return FasterWhisperEngine(model_name=model, device=device, compute_type=compute_type)


def run_transcribe(
    request: TranscribeRequest,
    *,
    engine: TranscriptionEngine | None = None,
    ffmpeg: FFmpegRunner | None = None,
    progress: ProgressCallback | None = None,
) -> TranscribeResult:
    """Execute the preprocessing → STT → export pipeline.

    ``engine`` and ``ffmpeg`` can be injected for tests. Otherwise sensible
    defaults are used.
    """

    started = time.monotonic()

    def emit(msg: str) -> None:
        logger.info(msg)
        if progress is not None:
            progress(msg)

    source = validate_input_path(request.input_path)
    preset_obj = get_preset(request.preset)
    job_id = request.job_id or new_job_id()

    job_dir = (request.cache_root / job_id).resolve()
    job_dir.mkdir(parents=True, exist_ok=True)
    processed_audio = job_dir / "processed.wav"

    emit(f"[1/3] 전처리 시작 (preset={preset_obj.name}, job={job_id})")
    runner = ffmpeg or FFmpegRunner()
    runner.preprocess(source, processed_audio, preset_obj)
    emit(f"      전처리 완료: {processed_audio}")

    emit(f"[2/3] STT 변환 시작 (model={request.model}, language={request.language or 'auto'})")
    active_engine = engine or _build_engine(request.model, request.device, request.compute_type)
    options = TranscriptionOptions(
        language=request.language,
        model_name=request.model,
        device=request.device,
        compute_type=request.compute_type,
        beam_size=request.beam_size,
        vad_filter=request.vad_filter,
        initial_prompt=request.initial_prompt,
    )

    segments: list[TranscriptSegment] = []
    for seg in active_engine.transcribe(processed_audio, options):
        segments.append(seg)
        if progress is not None:
            progress(f"      세그먼트 {len(segments):>4d}: [{seg.start:7.2f}s] {seg.text[:40]}")

    duration = segments[-1].end if segments else None
    transcription = TranscriptionResult(
        source_path=source,
        audio_path=processed_audio,
        language=request.language,
        model_name=request.model,
        preset=preset_obj.name,
        segments=segments,
        duration=duration,
    )
    emit(f"      STT 완료: 세그먼트 {len(segments)}개")

    emit("[3/3] Export 시작")
    pipeline = ExportPipeline(request.formats)
    base_name = source.stem
    exports = pipeline.run(transcription, request.output_dir, base_name)
    for path in exports:
        emit(f"      생성: {path}")

    elapsed = time.monotonic() - started
    emit(f"완료: {elapsed:.2f}초")

    return TranscribeResult(
        job_id=job_id,
        processed_audio=processed_audio,
        exports=exports,
        transcription=transcription,
        elapsed_seconds=elapsed,
    )
