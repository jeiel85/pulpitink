"""JSON exporter producing a structured transcript file."""

from __future__ import annotations

import json
from pathlib import Path

from pulpitink.core.export.base import Exporter, ExportFormat, ExportRequest


class JsonExporter(Exporter):
    format = ExportFormat.JSON

    def export(self, request: ExportRequest) -> Path:
        request.output_dir.mkdir(parents=True, exist_ok=True)
        target = request.output_dir / f"{request.base_name}.json"

        result = request.result
        payload = {
            "source_path": str(result.source_path),
            "audio_path": str(result.audio_path),
            "language": result.language,
            "model": result.model_name,
            "preset": result.preset,
            "duration": result.duration,
            "segments": [seg.to_dict() for seg in result.segments],
        }
        target.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return target
