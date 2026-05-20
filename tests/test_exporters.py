import json
from pathlib import Path

from sermonscript.core.export import (
    ExportFormat,
    JsonExporter,
    MarkdownExporter,
    SrtExporter,
    TxtExporter,
    VttExporter,
)
from sermonscript.core.export.base import ExportRequest
from sermonscript.core.export.pipeline import ExportPipeline
from sermonscript.core.transcription.base import (
    TranscriptionResult,
    TranscriptSegment,
    segment_display_text,
)


def _sample_result(tmp_path: Path) -> TranscriptionResult:
    return TranscriptionResult(
        source_path=Path("sermon.mp3"),
        audio_path=tmp_path / "processed.wav",
        language="ko",
        model_name="small",
        preset="sermon",
        segments=[
            TranscriptSegment(start=0.0, end=2.5, text="첫 문장입니다."),
            TranscriptSegment(start=2.5, end=5.0, text="두 번째 문장입니다."),
        ],
        duration=5.0,
    )


def _make_request(result, tmp_path: Path) -> ExportRequest:
    return ExportRequest(result=result, output_dir=tmp_path / "out", base_name="sermon")


def test_txt_exporter_outputs_each_segment_per_line(tmp_path: Path):
    result = _sample_result(tmp_path)
    path = TxtExporter().export(_make_request(result, tmp_path))
    text = path.read_text(encoding="utf-8")
    assert "첫 문장입니다." in text
    assert "두 번째 문장입니다." in text
    assert text.count("\n") >= 2


def test_json_exporter_includes_required_fields(tmp_path: Path):
    result = _sample_result(tmp_path)
    path = JsonExporter().export(_make_request(result, tmp_path))
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["language"] == "ko"
    assert data["model"] == "small"
    assert data["preset"] == "sermon"
    assert data["source_path"].endswith("sermon.mp3")
    assert len(data["segments"]) == 2
    assert data["segments"][0]["raw_text"] == "첫 문장입니다."


def test_markdown_exporter_contains_metadata_and_timestamps(tmp_path: Path):
    result = _sample_result(tmp_path)
    path = MarkdownExporter().export(_make_request(result, tmp_path))
    md = path.read_text(encoding="utf-8")
    assert md.startswith("# sermon")
    assert "## 파일 정보" in md
    assert "## 모델 정보" in md
    assert "[00:00:00.000]" in md


def test_srt_exporter_uses_srt_timestamp_format(tmp_path: Path):
    result = _sample_result(tmp_path)
    path = SrtExporter().export(_make_request(result, tmp_path))
    srt = path.read_text(encoding="utf-8")
    assert "1\n00:00:00,000 --> 00:00:02,500" in srt
    assert "2\n00:00:02,500 --> 00:00:05,000" in srt


def test_vtt_exporter_starts_with_webvtt(tmp_path: Path):
    result = _sample_result(tmp_path)
    path = VttExporter().export(_make_request(result, tmp_path))
    vtt = path.read_text(encoding="utf-8")
    assert vtt.startswith("WEBVTT\n")
    assert "00:00:00.000 --> 00:00:02.500" in vtt


def test_export_pipeline_runs_all_formats(tmp_path: Path):
    result = _sample_result(tmp_path)
    formats = [
        ExportFormat.TXT,
        ExportFormat.JSON,
        ExportFormat.MD,
        ExportFormat.SRT,
        ExportFormat.VTT,
    ]
    produced = ExportPipeline(formats).run(result, tmp_path / "out", "sermon")
    suffixes = {p.suffix for p in produced}
    assert suffixes == {".txt", ".json", ".md", ".srt", ".vtt"}
    for path in produced:
        assert path.exists() and path.stat().st_size > 0


def test_segment_display_text_priority():
    seg = TranscriptSegment(start=0, end=1, text="raw", clean_text="clean", edited_text="edited")
    assert segment_display_text(seg) == "edited"
    seg.edited_text = ""
    assert segment_display_text(seg) == "clean"
    seg.clean_text = ""
    assert segment_display_text(seg) == "raw"


def test_export_format_parse_normalises():
    assert ExportFormat.parse("TXT") is ExportFormat.TXT
    assert ExportFormat.parse(".md") is ExportFormat.MD
    assert ExportFormat.parse("vtt") is ExportFormat.VTT
