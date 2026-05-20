"""Persistence-side behaviour of run_transcribe (persist=True branch)."""

from __future__ import annotations

from pathlib import Path

import pytest

from pulpitink.app.exceptions import PulpitInkError
from pulpitink.core.audio.enhancement_presets import AudioEnhancementPreset
from pulpitink.core.export.base import ExportFormat
from pulpitink.core.transcription.base import (
    TranscriptionEngine,
    TranscriptionOptions,
    TranscriptSegment,
)
from pulpitink.services.transcribe_service import (
    TranscribeRequest,
    run_transcribe,
)
from pulpitink.storage.database import connect
from pulpitink.storage.job_repository import JobRepository


class _StubEngine(TranscriptionEngine):
    def transcribe(self, audio_path, options: TranscriptionOptions):
        yield TranscriptSegment(
            start=0.0, end=1.0, text="첫 번째", avg_logprob=-0.2, no_speech_prob=0.1
        )
        yield TranscriptSegment(
            start=1.0, end=2.5, text="두 번째", avg_logprob=-0.3, no_speech_prob=0.05
        )


class _StubFFmpeg:
    def preprocess(self, source: Path, output: Path, preset: AudioEnhancementPreset) -> Path:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(b"\x00\x00")  # placeholder bytes
        return output


def _build_request(tmp_path: Path) -> tuple[TranscribeRequest, Path]:
    src = tmp_path / "sample.wav"
    src.write_bytes(b"RIFF0000WAVE")
    request = TranscribeRequest(
        input_path=src,
        output_dir=tmp_path / "exports",
        preset="stt_basic",
        formats=(ExportFormat.TXT, ExportFormat.JSON),
        cache_root=tmp_path / "cache" / "jobs",
    )
    return request, tmp_path / "db.sqlite"


def test_run_transcribe_persists_success(tmp_path: Path) -> None:
    request, db = _build_request(tmp_path)
    result = run_transcribe(
        request,
        engine=_StubEngine(),
        ffmpeg=_StubFFmpeg(),
        persist=True,
        db_path=db,
    )

    with connect(db) as conn:
        repo = JobRepository(conn)
        job = repo.get_job(result.job_id)
        assert job is not None
        assert job.status == "completed"
        assert job.error_message is None
        assert job.engine == "_StubEngine"
        assert job.preset == "stt_basic"
        assert job.duration_sec == pytest.approx(2.5)

        segments = repo.list_segments(result.job_id)
        assert [s.raw_text for s in segments] == ["첫 번째", "두 번째"]
        assert segments[0].avg_logprob == pytest.approx(-0.2)

        exports = repo.list_exports(result.job_id)
        assert {e.format for e in exports} == {"txt", "json"}


class _BoomEngine(TranscriptionEngine):
    def transcribe(self, audio_path, options: TranscriptionOptions):
        raise RuntimeError("boom — STT failed")
        yield  # pragma: no cover — make this a generator type


def test_run_transcribe_marks_failure(tmp_path: Path) -> None:
    request, db = _build_request(tmp_path)
    with pytest.raises(RuntimeError):
        run_transcribe(
            request,
            engine=_BoomEngine(),
            ffmpeg=_StubFFmpeg(),
            persist=True,
            db_path=db,
        )

    with connect(db) as conn:
        repo = JobRepository(conn)
        jobs = repo.list_jobs(limit=5)
        assert len(jobs) == 1
        assert jobs[0].status == "failed"
        assert jobs[0].error_message and "boom" in jobs[0].error_message


class _BibleEngine(TranscriptionEngine):
    def transcribe(self, audio_path, options: TranscriptionOptions):
        yield TranscriptSegment(
            start=0.0,
            end=2.0,
            text="오늘 본문은 고린도 전서 일장 일절입니다.",
            avg_logprob=-0.3,
            no_speech_prob=0.1,
        )
        yield TranscriptSegment(
            start=2.0,
            end=4.0,
            text="우리는 복음을 살아내야 합니다.",
            avg_logprob=-1.5,  # low confidence → needs_review
            no_speech_prob=0.05,
        )


def test_run_transcribe_with_reference_creates_suggestions(tmp_path: Path) -> None:
    request, db = _build_request(tmp_path)
    ref = tmp_path / "sermon.md"
    ref.write_text(
        "# 고린도전서 1장\n\n오늘 본문은 고린도전서 1장 1절입니다. 복음은 능력입니다.\n",
        encoding="utf-8",
    )
    request.reference_path = ref

    result = run_transcribe(
        request,
        engine=_BibleEngine(),
        ffmpeg=_StubFFmpeg(),
        persist=True,
        db_path=db,
    )

    assert result.reference is not None
    assert result.correction_count >= 1

    with connect(db) as conn:
        repo = JobRepository(conn)
        segments = repo.list_segments(result.job_id)
        assert segments[0].raw_text == "오늘 본문은 고린도 전서 일장 일절입니다."
        # postprocess populates clean_text without touching raw_text
        assert "고린도전서" in segments[0].clean_text
        assert "1장 1절" in segments[0].clean_text
        # low-confidence segment is flagged
        assert segments[1].needs_review is True

        docs = repo.list_reference_documents(result.job_id)
        assert len(docs) == 1
        assert docs[0].title == "고린도전서 1장"

        pending = repo.list_correction_suggestions(result.job_id, status="pending")
        assert any(s.kind == "bible_ref" for s in pending)


def test_run_transcribe_persists_validation_failure(tmp_path: Path) -> None:
    bogus = tmp_path / "missing.wav"
    request = TranscribeRequest(
        input_path=bogus,
        output_dir=tmp_path / "out",
        preset="stt_basic",
        formats=(ExportFormat.TXT,),
        cache_root=tmp_path / "cache" / "jobs",
    )
    db = tmp_path / "db.sqlite"
    with pytest.raises(PulpitInkError):
        run_transcribe(
            request,
            engine=_StubEngine(),
            ffmpeg=_StubFFmpeg(),
            persist=True,
            db_path=db,
        )

    with connect(db) as conn:
        jobs = JobRepository(conn).list_jobs(limit=5)
        assert len(jobs) == 1
        assert jobs[0].status == "failed"
