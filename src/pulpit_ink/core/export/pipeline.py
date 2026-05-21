"""Pipeline orchestrating multiple exporters in one shot."""

from __future__ import annotations

import logging
from collections.abc import Iterable
from pathlib import Path

from pulpit_ink.app.exceptions import ExportError
from pulpit_ink.core.export.base import Exporter, ExportFormat, ExportRequest
from pulpit_ink.core.export.csv_exporter import CsvExporter
from pulpit_ink.core.export.docx_exporter import DocxExporter
from pulpit_ink.core.export.json_exporter import JsonExporter
from pulpit_ink.core.export.markdown_exporter import MarkdownExporter
from pulpit_ink.core.export.srt_exporter import SrtExporter
from pulpit_ink.core.export.txt_exporter import TxtExporter
from pulpit_ink.core.export.vtt_exporter import VttExporter
from pulpit_ink.core.transcription.base import TranscriptionResult

logger = logging.getLogger("pulpit_ink.export")

EXPORTERS: dict[ExportFormat, type[Exporter]] = {
    ExportFormat.TXT: TxtExporter,
    ExportFormat.JSON: JsonExporter,
    ExportFormat.MD: MarkdownExporter,
    ExportFormat.SRT: SrtExporter,
    ExportFormat.VTT: VttExporter,
    ExportFormat.CSV: CsvExporter,
    ExportFormat.DOCX: DocxExporter,
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
        bible_refs: list[str] | None = None,
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
                    ExportRequest(
                        result=result,
                        output_dir=output_dir,
                        base_name=base_name,
                        bible_refs=bible_refs or []
                    )
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
    bible_refs: list[str] | None = None,
) -> list[Path]:
    return ExportPipeline(formats).run(result, output_dir, base_name, bible_refs=bible_refs)
