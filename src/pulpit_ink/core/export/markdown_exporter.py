"""Markdown exporter with header metadata and transcript body."""

from __future__ import annotations

from pathlib import Path

from pulpit_ink.core.export.base import Exporter, ExportFormat, ExportRequest
from pulpit_ink.core.export.timestamps import format_vtt_timestamp
from pulpit_ink.core.transcription.base import segment_display_text


class MarkdownExporter(Exporter):
    format = ExportFormat.MD

    def export(self, request: ExportRequest) -> Path:
        request.output_dir.mkdir(parents=True, exist_ok=True)
        target = request.output_dir / f"{request.base_name}.md"

        result = request.result
        lines: list[str] = []
        lines.append(f"# {request.base_name}")
        lines.append("")
        lines.append("## 파일 정보")
        lines.append(f"- 원본 파일: `{result.source_path}`")
        lines.append(f"- 전처리 파일: `{result.audio_path}`")
        lines.append(f"- 언어: {result.language or '자동 감지'}")
        if result.duration is not None:
            lines.append(f"- 길이: {result.duration:.2f}s")
        lines.append("")
        lines.append("## 모델 정보")
        lines.append(f"- 모델: {result.model_name}")
        lines.append(f"- 전처리 프리셋: {result.preset}")
        lines.append("")
        lines.append("## 본문")
        lines.append("")

        for seg in result.segments:
            stamp = format_vtt_timestamp(seg.start)
            text = segment_display_text(seg)
            lines.append(f"[{stamp}] {text}")

        target.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return target
