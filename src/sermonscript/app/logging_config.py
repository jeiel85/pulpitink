"""Centralised logging setup.

The CLI prints user-facing messages via ``rich``. This module configures the
``sermonscript`` logger tree for developer-oriented diagnostics, with an
optional file handler under the OS-specific log directory.
"""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from sermonscript.app.paths import get_app_paths

_LOGGER_NAME = "sermonscript"
_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"


def configure_logging(level: int = logging.INFO, *, log_to_file: bool = False) -> logging.Logger:
    """Configure the ``sermonscript`` logger.

    Calling more than once is safe; existing handlers are not duplicated.
    """

    logger = logging.getLogger(_LOGGER_NAME)
    logger.setLevel(level)
    logger.propagate = False

    if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
        stream = logging.StreamHandler()
        stream.setFormatter(logging.Formatter(_FORMAT))
        logger.addHandler(stream)

    if log_to_file and not any(isinstance(h, RotatingFileHandler) for h in logger.handlers):
        log_dir: Path = get_app_paths().log_dir
        log_dir.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            log_dir / "sermonscript.log",
            maxBytes=1_000_000,
            backupCount=3,
            encoding="utf-8",
        )
        file_handler.setFormatter(logging.Formatter(_FORMAT))
        logger.addHandler(file_handler)

    return logger
