"""Plain-text exporter."""

from __future__ import annotations

from pathlib import Path

from pulpit_ink.core.export.base import Exporter, ExportFormat, ExportRequest
from pulpit_ink.core.transcription.base import segment_display_text


class TxtExporter(Exporter):
    format = ExportFormat.TXT

    def export(self, request: ExportRequest) -> Path:
        request.output_dir.mkdir(parents=True, exist_ok=True)
        target = request.output_dir / f"{request.base_name}.txt"

        lines = [segment_display_text(seg) for seg in request.result.segments]
        target.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
        return target
