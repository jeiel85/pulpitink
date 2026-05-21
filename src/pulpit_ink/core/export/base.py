"""Common types for transcript exporters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path

from pulpit_ink.core.transcription.base import TranscriptionResult


class ExportFormat(StrEnum):
    TXT = "txt"
    JSON = "json"
    MD = "md"
    SRT = "srt"
    VTT = "vtt"
    CSV = "csv"
    DOCX = "docx"

    @classmethod
    def parse(cls, value: str) -> ExportFormat:
        normalised = value.strip().lower().lstrip(".")
        for fmt in cls:
            if fmt.value == normalised:
                return fmt
        raise ValueError(f"지원하지 않는 export 포맷입니다: '{value}'")


@dataclass(frozen=True)
class ExportRequest:
    """Inputs required to produce a single export file."""

    result: TranscriptionResult
    output_dir: Path
    base_name: str
    bible_refs: list[str] = field(default_factory=list)


class Exporter(ABC):
    """Renders a :class:`TranscriptionResult` to a single file."""

    format: ExportFormat

    @abstractmethod
    def export(self, request: ExportRequest) -> Path:
        raise NotImplementedError
