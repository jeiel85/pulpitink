"""Application-level utilities shared by CLI and (later) GUI."""

from sermonscript.app.exceptions import (
    ExportError,
    FFmpegError,
    SermonScriptError,
    TranscriptionError,
    UnsupportedFormatError,
)
from sermonscript.app.logging_config import configure_logging
from sermonscript.app.paths import (
    AppPaths,
    get_app_paths,
    job_cache_dir,
)

__all__ = [
    "AppPaths",
    "ExportError",
    "FFmpegError",
    "SermonScriptError",
    "TranscriptionError",
    "UnsupportedFormatError",
    "configure_logging",
    "get_app_paths",
    "job_cache_dir",
]
