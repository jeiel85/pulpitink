"""Persistence layer (SQLite via stdlib).

DB schema lives in :mod:`sermonscript.storage.database`. Job/segment/export
persistence is exposed by :mod:`sermonscript.storage.job_repository`.
"""

from sermonscript.storage.database import (
    DEFAULT_DB_FILENAME,
    SCHEMA_VERSION,
    connect,
    default_db_path,
    initialise_database,
)

__all__ = [
    "DEFAULT_DB_FILENAME",
    "SCHEMA_VERSION",
    "connect",
    "default_db_path",
    "initialise_database",
]
