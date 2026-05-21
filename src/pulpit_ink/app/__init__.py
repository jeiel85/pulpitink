"""Application-level utilities shared by CLI and (later) GUI."""

from pulpit_ink.app.exceptions import (
    ExportError,
    FFmpegError,
    PulpitInkError,
    TranscriptionError,
    UnsupportedFormatError,
)
from pulpit_ink.app.logging_config import configure_logging
from pulpit_ink.app.paths import (
    AppPaths,
    get_app_paths,
    job_cache_dir,
)

__all__ = [
    "AppPaths",
    "ExportError",
    "FFmpegError",
    "PulpitInkError",
    "TranscriptionError",
    "UnsupportedFormatError",
    "configure_logging",
    "get_app_paths",
    "job_cache_dir",
]
