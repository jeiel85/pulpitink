"""Shared exception hierarchy for pulpit_ink."""

from __future__ import annotations


class PulpitInkError(Exception):
    """Base class for PulpitInk domain errors."""


class UnsupportedFormatError(PulpitInkError):
    """The provided input file format is not supported."""


class FFmpegError(PulpitInkError):
    """FFmpeg is missing or failed while running."""


class TranscriptionError(PulpitInkError):
    """The STT engine failed to produce a transcript."""


class ExportError(PulpitInkError):
    """A transcript export step failed."""
