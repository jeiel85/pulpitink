"""End-to-end smoke test for the transcribe pipeline.

Uses real FFmpeg when available to produce ``processed.wav`` and injects a
stub STT engine so the test does not require a Whisper model download.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from pulpit_ink.core.export.base import ExportFormat
from pulpit_ink.core.transcription.base import (
    TranscriptionEngine,
    TranscriptionOptions,
    TranscriptSegment,
)
from pulpit_ink.services.transcribe_service import (
    TranscribeRequest,
    run_transcribe,
)


class _StubEngine(TranscriptionEngine):
    def transcribe(self, audio_path, options: TranscriptionOptions):
        yield TranscriptSegment(start=0.0, end=1.0, text="첫 번째 문장")
        yield TranscriptSegment(start=1.0, end=2.0, text="두 번째 문장")


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg가 PATH에 없습니다.")
def test_run_transcribe_end_to_end(tmp_path: Path):
    src = tmp_path / "input.wav"
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-nostdin",
        "-loglevel", "error",
        "-y",
        "-f", "lavfi",
        "-i", "sine=frequency=440:duration=1",
        "-ac", "1",
        "-ar", "16000",
        str(src),
    ]
    subprocess.run(cmd, check=True)

    request = TranscribeRequest(
        input_path=src,
        output_dir=tmp_path / "exports",
        preset="stt_basic",
        formats=(
            ExportFormat.TXT,
            ExportFormat.JSON,
            ExportFormat.MD,
            ExportFormat.SRT,
            ExportFormat.VTT,
            ExportFormat.CSV,
        ),
        cache_root=tmp_path / "cache" / "jobs",
    )

    progress: list[str] = []
    result = run_transcribe(request, engine=_StubEngine(), progress=progress.append)

    assert result.processed_audio.exists()
    assert result.processed_audio.stat().st_size > 0
    assert {p.suffix for p in result.exports} == {".txt", ".json", ".md", ".srt", ".vtt", ".csv"}
    assert any("전처리 완료" in line for line in progress)
    assert any("Export" in line for line in progress)
    assert src.exists()  # original must remain untouched
