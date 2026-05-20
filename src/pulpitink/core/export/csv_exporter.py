"""CSV exporter producing a spreadsheet-friendly transcript file."""

from __future__ import annotations

import csv
import io
from pathlib import Path

from pulpitink.core.export.base import Exporter, ExportFormat, ExportRequest
from pulpitink.core.export.timestamps import format_vtt_timestamp
from pulpitink.core.transcription.base import segment_display_text

CSV_COLUMNS = (
    "index",
    "start_sec",
    "end_sec",
    "start",
    "end",
    "text",
    "raw_text",
    "clean_text",
    "edited_text",
    "speaker",
)


class CsvExporter(Exporter):
    format = ExportFormat.CSV

    def export(self, request: ExportRequest) -> Path:
        request.output_dir.mkdir(parents=True, exist_ok=True)
        target = request.output_dir / f"{request.base_name}.csv"

        buffer = io.StringIO(newline="")
        writer = csv.writer(buffer, quoting=csv.QUOTE_MINIMAL, lineterminator="\r\n")
        writer.writerow(CSV_COLUMNS)
        for idx, seg in enumerate(request.result.segments, start=1):
            writer.writerow(
                [
                    idx,
                    f"{seg.start:.3f}",
                    f"{max(seg.end, seg.start):.3f}",
                    format_vtt_timestamp(seg.start),
                    format_vtt_timestamp(max(seg.end, seg.start)),
                    segment_display_text(seg),
                    seg.raw_text,
                    seg.clean_text,
                    seg.edited_text,
                    seg.speaker or "",
                ]
            )

        # UTF-8 BOM so Excel renders Korean text correctly.
        target.write_text(buffer.getvalue(), encoding="utf-8-sig", newline="")
        return target
