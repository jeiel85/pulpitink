"""SRT subtitle exporter."""

from __future__ import annotations

from pathlib import Path

from pulpit_ink.core.export.base import Exporter, ExportFormat, ExportRequest
from pulpit_ink.core.export.timestamps import format_srt_timestamp
from pulpit_ink.core.transcription.base import segment_display_text


class SrtExporter(Exporter):
    format = ExportFormat.SRT

    def export(self, request: ExportRequest) -> Path:
        request.output_dir.mkdir(parents=True, exist_ok=True)
        target = request.output_dir / f"{request.base_name}.srt"

        lines: list[str] = []
        for idx, seg in enumerate(request.result.segments, start=1):
            start = format_srt_timestamp(seg.start)
            end = format_srt_timestamp(max(seg.end, seg.start))
            text = segment_display_text(seg).strip()
            lines.append(str(idx))
            lines.append(f"{start} --> {end}")
            lines.append(text)
            lines.append("")

        target.write_text("\n".join(lines), encoding="utf-8")
        return target
