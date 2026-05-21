"""Pipeline that ties preprocessing + STT + export together.

The CLI is intentionally a thin shell on top of this module — the GUI in
Goal 2 calls the same entry points.

DB persistence (jobs / segments / exports) is opt-in via ``persist=True``
so existing tests that inject a stub engine continue to work without
needing a database. The CLI enables persistence by default.

Goal 3 additions:

* A reference document (``--reference``) can be attached. The parser
  extracts a small set of key terms, which feed ``initial_prompt`` and
  the correction engine.
* Each segment runs through the postprocess pipeline to populate
  ``clean_text`` (``raw_text`` is never mutated).
* Low-confidence segments (``avg_logprob`` low or ``no_speech_prob``
  high) are flagged ``needs_review`` so the editor can highlight them.
* Reference + alignment + correction suggestions are persisted when
  ``persist=True`` and a reference document is attached.
"""

from __future__ import annotations

import logging
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from pulpit_ink.app.exceptions import (
    PulpitInkError,
    UnsupportedFormatError,
)
from pulpit_ink.core.audio.enhancement_presets import get_preset
from pulpit_ink.core.audio.ffmpeg_runner import DEFAULT_PRESET, FFmpegRunner
from pulpit_ink.core.export.base import ExportFormat
from pulpit_ink.core.export.pipeline import ExportPipeline
from pulpit_ink.core.postprocess import Lexicon, load_user_lexicon, postprocess_text
from pulpit_ink.core.reference import (
    CorrectionEngine,
    ParsedReference,
    align_segments_to_reference,
    build_reference_prompt,
    parse_reference,
    prompt_from_parsed,
)
from pulpit_ink.core.transcription.base import (
    TranscriptionEngine,
    TranscriptionOptions,
    TranscriptionResult,
    TranscriptSegment,
)
from pulpit_ink.storage.database import connect, initialise_database
from pulpit_ink.storage.job_repository import (
    AlignmentPairRecord,
    CorrectionSuggestionRecord,
    ExportRecord,
    JobRepository,
    ReferenceDocumentRecord,
    SegmentRecord,
)

logger = logging.getLogger("pulpit_ink.services.transcribe")

SUPPORTED_INPUT_EXTENSIONS: frozenset[str] = frozenset(
    {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg", ".mp4"}
)

# Confidence thresholds for flagging a segment as ``needs_review``.
LOW_AVG_LOGPROB_THRESHOLD: float = -1.0
HIGH_NO_SPEECH_PROB_THRESHOLD: float = 0.6

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
        ExportFormat.CSV,
    )
    device: str = "auto"
    compute_type: str = "int8"
    beam_size: int = 5
    vad_filter: bool = True
    initial_prompt: str | None = None
    cache_root: Path = Path("cache") / "jobs"
    job_id: str | None = None
    reference_path: Path | None = None
    user_dict_path: Path | None = None
    fuzzy_matching_enabled: bool = True
    fuzzy_threshold: float = 0.70
    diarize: bool = False


@dataclass
class TranscribeResult:
    job_id: str
    processed_audio: Path
    exports: list[Path] = field(default_factory=list)
    transcription: TranscriptionResult | None = None
    elapsed_seconds: float = 0.0
    reference: ParsedReference | None = None
    correction_count: int = 0


def new_job_id() -> str:
    """Return a short, filesystem-safe identifier for one transcription run."""

    return uuid.uuid4().hex[:12]


def validate_input_path(path: Path) -> Path:
    """Resolve and validate a user-supplied audio path."""

    if not path.exists():
        raise PulpitInkError(f"입력 파일을 찾을 수 없습니다: {path}")
    if not path.is_file():
        raise PulpitInkError(f"입력 경로가 파일이 아닙니다: {path}")

    suffix = path.suffix.lower()
    if suffix not in SUPPORTED_INPUT_EXTENSIONS:
        supported = ", ".join(sorted(SUPPORTED_INPUT_EXTENSIONS))
        raise UnsupportedFormatError(
            f"지원하지 않는 확장자입니다: {suffix or '(확장자 없음)'}. 지원: {supported}"
        )
    return path.resolve()


def _build_engine(model: str, device: str, compute_type: str) -> TranscriptionEngine:
    # Local import keeps the heavy CT2 dependency optional at module-load time.
    from pulpit_ink.core.transcription.faster_whisper_engine import FasterWhisperEngine

    return FasterWhisperEngine(model_name=model, device=device, compute_type=compute_type)


def _engine_name(engine: TranscriptionEngine | None) -> str:
    if engine is None:
        return "faster-whisper"
    return type(engine).__name__


def _needs_review(seg: TranscriptSegment) -> bool:
    if seg.avg_logprob is not None and seg.avg_logprob < LOW_AVG_LOGPROB_THRESHOLD:
        return True
    if (
        seg.no_speech_prob is not None
        and seg.no_speech_prob > HIGH_NO_SPEECH_PROB_THRESHOLD
    ):
        return True
    return False


def _resolve_reference(
    request: TranscribeRequest,
) -> tuple[ParsedReference | None, str | None]:
    """Parse the reference doc (if any) and derive the initial_prompt."""

    parsed = None
    prompt = request.initial_prompt
    if request.reference_path is None:
        return parsed, prompt
    parsed = parse_reference(request.reference_path)
    if prompt is None:
        prompt = build_reference_prompt(prompt_from_parsed(parsed))
    return parsed, prompt


def _build_lexicon(request: TranscribeRequest) -> Lexicon:
    path = request.user_dict_path
    if path is None:
        from pulpit_ink.app.paths import get_app_paths
        default_path = get_app_paths().data_dir / "user_dict.json"
        if default_path.exists():
            path = default_path
    return load_user_lexicon(path)


def _enrich_segments(
    segments: list[TranscriptSegment],
    lexicon: Lexicon,
) -> None:
    """Populate ``clean_text`` and ``needs_review``-like hints in place."""

    for seg in segments:
        seg.clean_text = postprocess_text(seg.text, lexicon=lexicon)


def _persist_failure(
    db_path: Path | None,
    job_id: str,
    error: Exception,
    *,
    source: Path,
    request: TranscribeRequest,
    engine_label: str,
) -> None:
    """Record a failed job — best-effort, never re-raises."""

    try:
        initialise_database(db_path)
        with connect(db_path) as conn:
            repo = JobRepository(conn)
            existing = repo.get_job(job_id)
            if existing is None:
                repo.create_job(
                    job_id=job_id,
                    source_path=source,
                    title=source.stem,
                    language=request.language,
                    model_name=request.model,
                    engine=engine_label,
                    preset=request.preset,
                    status="failed",
                )
            repo.update_job_status(
                job_id, status="failed", error_message=str(error)
            )
    except Exception as inner:  # pragma: no cover - logging only
        logger.warning("failed-job 기록 실패: %s", inner)


def _persist_reference_artifacts(
    repo: JobRepository,
    job_id: str,
    parsed: ParsedReference,
    segments: list[TranscriptSegment],
    lexicon: Lexicon,
    fuzzy_matching_enabled: bool = True,
    fuzzy_threshold: float = 0.70,
) -> int:
    """Save reference doc + alignment pairs + correction suggestions.

    Returns the number of correction suggestions written.
    """

    doc = repo.add_reference_document(
        ReferenceDocumentRecord(
            job_id=job_id,
            source_path=str(parsed.source_path),
            title=parsed.title,
            content=parsed.content,
            bible_refs=parsed.bible_refs,
            keywords=parsed.keywords,
            proper_nouns=parsed.proper_nouns,
        )
    )

    seg_rows = repo.list_segments(job_id)
    seg_id_by_index = {idx: row.id for idx, row in enumerate(seg_rows) if row.id is not None}

    if parsed.paragraphs:
        pairs = align_segments_to_reference(
            [seg.text for seg in segments],
            parsed.paragraphs,
        )
        repo.add_alignment_pairs(
            AlignmentPairRecord(
                job_id=job_id,
                segment_id=seg_id_by_index[p.segment_index],
                reference_document_id=doc.id or 0,
                reference_index=p.reference_index,
                score=p.score,
            )
            for p in pairs
            if p.segment_index in seg_id_by_index
        )

    engine = CorrectionEngine.from_reference(
        parsed,
        lexicon=lexicon,
        fuzzy_matching_enabled=fuzzy_matching_enabled,
        fuzzy_threshold=fuzzy_threshold,
    )
    suggestions: list[CorrectionSuggestionRecord] = []
    for idx, seg in enumerate(segments):
        seg_id = seg_id_by_index.get(idx)
        if seg_id is None:
            continue
        for cand in engine.suggestions_for(idx, seg.text):
            suggestions.append(
                CorrectionSuggestionRecord(
                    job_id=job_id,
                    segment_id=seg_id,
                    kind=cand.kind,
                    original_text=cand.original_text,
                    suggested_text=cand.suggested_text,
                    source=cand.source,
                )
            )
    repo.add_correction_suggestions(suggestions)
    return len(suggestions)


def run_transcribe(
    request: TranscribeRequest,
    *,
    engine: TranscriptionEngine | None = None,
    ffmpeg: FFmpegRunner | None = None,
    progress: ProgressCallback | None = None,
    persist: bool = False,
    db_path: Path | None = None,
) -> TranscribeResult:
    """Execute the preprocessing → STT → export pipeline.

    ``engine`` and ``ffmpeg`` can be injected for tests. ``persist=True``
    writes job / segments / exports rows to the SQLite DB at ``db_path``
    (or the user data dir if ``db_path`` is ``None``).
    """

    started = time.monotonic()

    from pulpit_ink.services.settings_service import SettingsService
    try:
        settings = SettingsService().load()
        if not settings.keep_history:
            persist = False
    except Exception:  # noqa: BLE001
        pass

    def emit(msg: str) -> None:
        logger.info(msg)
        if progress is not None:
            progress(msg)

    job_id = request.job_id or new_job_id()
    engine_label = _engine_name(engine)

    # Handle YouTube URL download seamlessly in worker thread
    input_str = str(request.input_path)
    if input_str.startswith(("http://", "https://")):
        emit(f"YouTube URL 감지: {input_str}")
        emit("오디오 다운로드를 진행합니다. (yt-dlp 구동)")
        from pulpit_ink.core.audio.youtube_downloader import download_youtube_audio
        try:
            downloaded_path = download_youtube_audio(input_str, request.output_dir)
            emit(f"YouTube 다운로드 완료: {downloaded_path.name}")
            from dataclasses import replace
            request = replace(request, input_path=downloaded_path)
        except Exception as exc:
            raise PulpitInkError(f"YouTube 다운로드 실패: {exc}") from exc

    try:
        source = validate_input_path(request.input_path)
    except PulpitInkError as exc:
        if persist:
            # We could not even validate the path; record an entry using the
            # path the user provided so they can see what was attempted.
            _persist_failure(
                db_path,
                job_id,
                exc,
                source=request.input_path,
                request=request,
                engine_label=engine_label,
            )
        raise

    parsed_reference, derived_prompt = _resolve_reference(request)
    lexicon = _build_lexicon(request)

    preset_obj = get_preset(request.preset)

    job_dir = (request.cache_root / job_id).resolve()
    job_dir.mkdir(parents=True, exist_ok=True)
    processed_audio = job_dir / "processed.wav"

    if persist:
        initialise_database(db_path)
        with connect(db_path) as conn:
            JobRepository(conn).create_job(
                job_id=job_id,
                source_path=source,
                title=source.stem,
                language=request.language,
                model_name=request.model,
                engine=engine_label,
                preset=preset_obj.name,
                status="running",
            )

    try:
        emit(f"[1/3] 전처리 시작 (preset={preset_obj.name}, job={job_id})")
        runner = ffmpeg or FFmpegRunner()
        runner.preprocess(source, processed_audio, preset_obj)
        emit(f"      전처리 완료: {processed_audio}")

        emit(
            f"[2/3] STT 변환 시작 (model={request.model}, "
            f"language={request.language or 'auto'})"
        )
        active_engine = engine or _build_engine(
            request.model, request.device, request.compute_type
        )
        options = TranscriptionOptions(
            language=request.language,
            model_name=request.model,
            device=request.device,
            compute_type=request.compute_type,
            beam_size=request.beam_size,
            vad_filter=request.vad_filter,
            initial_prompt=derived_prompt,
        )

        segments: list[TranscriptSegment] = []
        for seg in active_engine.transcribe(processed_audio, options):
            segments.append(seg)
            if progress is not None:
                progress(
                    f"      세그먼트 {len(segments):>4d}: "
                    f"[{seg.start:7.2f}s] {seg.text[:40]}"
                )

        _enrich_segments(segments, lexicon)

        if request.diarize:
            emit("      [Heuristic 화자 분리] 화자 태그 할당 중...")
            from pulpit_ink.core.postprocess.diarizer import HeuristicDiarizer
            diarizer = HeuristicDiarizer()
            diarizer.assign_speakers_to_segments(segments)

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
        bible_refs = parsed_reference.bible_refs if parsed_reference else []
        exports = pipeline.run(transcription, request.output_dir, base_name, bible_refs=bible_refs)
        for path in exports:
            emit(f"      생성: {path}")

        elapsed = time.monotonic() - started
        emit(f"완료: {elapsed:.2f}초")

        correction_count = 0
        if persist:
            with connect(db_path) as conn:
                repo = JobRepository(conn)
                repo.add_segments(
                    SegmentRecord(
                        job_id=job_id,
                        start_sec=seg.start,
                        end_sec=seg.end,
                        raw_text=seg.text,
                        clean_text=seg.clean_text,
                        edited_text=seg.edited_text,
                        avg_logprob=seg.avg_logprob,
                        no_speech_prob=seg.no_speech_prob,
                        needs_review=_needs_review(seg),
                        speaker=seg.speaker,
                    )
                    for seg in segments
                )
                repo.add_exports(
                    ExportRecord(
                        job_id=job_id,
                        format=path.suffix.lstrip(".").lower(),
                        output_path=str(path),
                    )
                    for path in exports
                )
                repo.update_job_status(
                    job_id,
                    status="completed",
                    duration_sec=duration,
                )
                if parsed_reference is not None:
                    correction_count = _persist_reference_artifacts(
                        repo,
                        job_id,
                        parsed_reference,
                        segments,
                        lexicon,
                        fuzzy_matching_enabled=request.fuzzy_matching_enabled,
                        fuzzy_threshold=request.fuzzy_threshold,
                    )
                    emit(
                        f"      원문 대조: 교정 후보 {correction_count}개 "
                        "저장(pending)"
                    )

        return TranscribeResult(
            job_id=job_id,
            processed_audio=processed_audio,
            exports=exports,
            transcription=transcription,
            elapsed_seconds=elapsed,
            reference=parsed_reference,
            correction_count=correction_count,
        )
    except Exception as exc:
        if persist:
            _persist_failure(
                db_path,
                job_id,
                exc,
                source=source,
                request=request,
                engine_label=engine_label,
            )
        raise
