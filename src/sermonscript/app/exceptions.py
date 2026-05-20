"""Shared exception hierarchy for SermonScript."""

from __future__ import annotations


class SermonScriptError(Exception):
    """Base class for SermonScript domain errors."""


class UnsupportedFormatError(SermonScriptError):
    """The provided input file format is not supported."""


class FFmpegError(SermonScriptError):
    """FFmpeg is missing or failed while running."""


class TranscriptionError(SermonScriptError):
    """The STT engine failed to produce a transcript."""


class ExportError(SermonScriptError):
    """A transcript export step failed."""
