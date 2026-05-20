"""Pipeline orchestrating multiple exporters in one shot."""

from __future__ import annotations

import logging
from collections.abc import Iterable
from pathlib import Path

from sermonscript.app.exceptions import ExportError
from sermonscript.core.export.base import Exporter, ExportFormat, ExportRequest
from sermonscript.core.export.json_exporter import JsonExporter
from sermonscript.core.export.markdown_exporter import MarkdownExporter
from sermonscript.core.export.srt_exporter import SrtExporter
from sermonscript.core.export.txt_exporter import TxtExporter
from sermonscript.core.export.vtt_exporter import VttExporter
from sermonscript.core.transcription.base import TranscriptionResult

logger = logging.getLogger("sermonscript.export")

EXPORTERS: dict[ExportFormat, type[Exporter]] = {
    ExportFormat.TXT: TxtExporter,
    ExportFormat.JSON: JsonExporter,
    ExportFormat.MD: MarkdownExporter,
    ExportFormat.SRT: SrtExporter,
    ExportFormat.VTT: VttExporter,
}


class ExportPipeline:
    """Run a set of exporters against the same transcription result."""

    def __init__(self, formats: Iterable[ExportFormat | str]) -> None:
        normalised: list[ExportFormat] = []
        for fmt in formats:
            normalised.append(fmt if isinstance(fmt, ExportFormat) else ExportFormat.parse(fmt))
        # de-duplicate while preserving order
        self.formats: list[ExportFormat] = list(dict.fromkeys(normalised))

    def run(
        self,
        result: TranscriptionResult,
        output_dir: Path,
        base_name: str,
    ) -> list[Path]:
        output_dir.mkdir(parents=True, exist_ok=True)
        produced: list[Path] = []
        for fmt in self.formats:
            exporter_cls = EXPORTERS.get(fmt)
            if exporter_cls is None:
                raise ExportError(f"등록되지 않은 export 포맷입니다: {fmt}")
            exporter = exporter_cls()
            try:
                path = exporter.export(
                    ExportRequest(result=result, output_dir=output_dir, base_name=base_name)
                )
            except OSError as exc:
                raise ExportError(
                    f"{fmt.value.upper()} export 중 입출력 오류가 발생했습니다: {exc}"
                ) from exc
            logger.info("Exported %s -> %s", fmt.value, path)
            produced.append(path)
        return produced


def run_exports(
    result: TranscriptionResult,
    output_dir: Path,
    base_name: str,
    formats: Iterable[ExportFormat | str],
) -> list[Path]:
    return ExportPipeline(formats).run(result, output_dir, base_name)
