"""WebVTT subtitle exporter."""

from __future__ import annotations

from pathlib import Path

from sermonscript.core.export.base import Exporter, ExportFormat, ExportRequest
from sermonscript.core.export.timestamps import format_vtt_timestamp
from sermonscript.core.transcription.base import segment_display_text


class VttExporter(Exporter):
    format = ExportFormat.VTT

    def export(self, request: ExportRequest) -> Path:
        request.output_dir.mkdir(parents=True, exist_ok=True)
        target = request.output_dir / f"{request.base_name}.vtt"

        lines: list[str] = ["WEBVTT", ""]
        for seg in request.result.segments:
            start = format_vtt_timestamp(seg.start)
            end = format_vtt_timestamp(max(seg.end, seg.start))
            text = segment_display_text(seg).strip()
            lines.append(f"{start} --> {end}")
            lines.append(text)
            lines.append("")

        target.write_text("\n".join(lines), encoding="utf-8")
        return target
