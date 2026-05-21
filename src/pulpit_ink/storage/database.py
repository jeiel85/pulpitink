"""SQLite database bootstrap for pulpit_ink.

The DB lives under the user data directory (``platformdirs``) by default so
tests can override the path with an explicit ``db_path`` and never touch the
real user database.

Schema overview (see ``docs/storage-schema.md`` for the rationale):

* ``jobs``                  — one row per transcription run (status, model, etc.)
* ``segments``              — per-segment STT output; ``raw_text`` is immutable
* ``exports``               — one row per generated output file
* ``reference_documents``   — sermon reference TXT/MD attached to a job (Goal 3)
* ``alignment_pairs``       — STT segment ↔ reference paragraph similarity links
* ``correction_suggestions``— pending bible-ref / proper-noun / lexicon hints

A ``schema_meta`` table records the current schema version so we can grow it
later with explicit migrations without losing user data. Goal 3 bumps the
version to 2 — :func:`initialise_database` upgrades existing v1 databases in
place by adding the new tables (no destructive change).
"""

from __future__ import annotations

import logging
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from pulpit_ink.app.paths import get_app_paths

logger = logging.getLogger("pulpit_ink.storage")

DEFAULT_DB_FILENAME = "pulpit_ink.db"
SCHEMA_VERSION = 2

_SCHEMA_SQL: tuple[str, ...] = (
    """
    CREATE TABLE IF NOT EXISTS schema_meta (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS jobs (
        id TEXT PRIMARY KEY,
        source_path TEXT NOT NULL,
        title TEXT NOT NULL,
        duration_sec REAL,
        language TEXT,
        model_name TEXT NOT NULL,
        engine TEXT NOT NULL,
        preset TEXT NOT NULL,
        status TEXT NOT NULL,
        error_message TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS segments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id TEXT NOT NULL,
        start_sec REAL NOT NULL,
        end_sec REAL NOT NULL,
        raw_text TEXT NOT NULL,
        clean_text TEXT NOT NULL DEFAULT '',
        edited_text TEXT NOT NULL DEFAULT '',
        avg_logprob REAL,
        no_speech_prob REAL,
        needs_review INTEGER NOT NULL DEFAULT 0,
        speaker TEXT,
        FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS exports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id TEXT NOT NULL,
        format TEXT NOT NULL,
        output_path TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS reference_documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id TEXT NOT NULL,
        source_path TEXT NOT NULL,
        title TEXT,
        content TEXT NOT NULL,
        bible_refs TEXT NOT NULL DEFAULT '[]',
        keywords TEXT NOT NULL DEFAULT '[]',
        proper_nouns TEXT NOT NULL DEFAULT '[]',
        created_at TEXT NOT NULL,
        FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS alignment_pairs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id TEXT NOT NULL,
        segment_id INTEGER NOT NULL,
        reference_document_id INTEGER NOT NULL,
        reference_index INTEGER NOT NULL,
        score REAL NOT NULL,
        FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE,
        FOREIGN KEY (segment_id) REFERENCES segments(id) ON DELETE CASCADE,
        FOREIGN KEY (reference_document_id) REFERENCES reference_documents(id)
            ON DELETE CASCADE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS correction_suggestions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id TEXT NOT NULL,
        segment_id INTEGER NOT NULL,
        kind TEXT NOT NULL,
        original_text TEXT NOT NULL,
        suggested_text TEXT NOT NULL,
        source TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'pending',
        created_at TEXT NOT NULL,
        FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE,
        FOREIGN KEY (segment_id) REFERENCES segments(id) ON DELETE CASCADE
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at DESC)",
    "CREATE INDEX IF NOT EXISTS idx_segments_job_id ON segments(job_id)",
    "CREATE INDEX IF NOT EXISTS idx_exports_job_id ON exports(job_id)",
    "CREATE INDEX IF NOT EXISTS idx_reference_documents_job_id "
    "ON reference_documents(job_id)",
    "CREATE INDEX IF NOT EXISTS idx_alignment_pairs_job_id ON alignment_pairs(job_id)",
    "CREATE INDEX IF NOT EXISTS idx_alignment_pairs_segment_id "
    "ON alignment_pairs(segment_id)",
    "CREATE INDEX IF NOT EXISTS idx_correction_suggestions_job_id "
    "ON correction_suggestions(job_id)",
    "CREATE INDEX IF NOT EXISTS idx_correction_suggestions_status "
    "ON correction_suggestions(status)",
)


def default_db_path() -> Path:
    """Return ``<user_data_dir>/pulpit_ink.db``."""

    paths = get_app_paths().ensure()
    return paths.data_dir / DEFAULT_DB_FILENAME


def _row_factory(cursor: sqlite3.Cursor, row: tuple) -> dict:
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}


def connect(db_path: Path | None = None) -> sqlite3.Connection:
    """Open a SQLite connection with sensible defaults.

    The DB file (and parent directory) is created on first use. ``foreign_keys``
    is enabled so cascading deletes work as advertised.
    """

    path = Path(db_path) if db_path is not None else default_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, isolation_level=None, check_same_thread=False)
    conn.row_factory = _row_factory
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def initialise_database(db_path: Path | None = None) -> Path:
    """Create tables/indices if missing and stamp the schema version.

    Existing v1 databases (jobs/segments/exports only) are upgraded in place by
    re-running every ``CREATE TABLE IF NOT EXISTS`` statement — no destructive
    operation required for the Goal 3 additions.

    Returns the resolved DB path so callers can log or reuse it.
    """

    resolved = Path(db_path) if db_path is not None else default_db_path()
    with connect(resolved) as conn:
        with _transaction(conn):
            for stmt in _SCHEMA_SQL:
                conn.execute(stmt)
            conn.execute(
                "INSERT OR REPLACE INTO schema_meta(key, value) VALUES('schema_version', ?)",
                (str(SCHEMA_VERSION),),
            )
    logger.debug("Initialised PulpitInk DB at %s", resolved)
    return resolved


@contextmanager
def _transaction(conn: sqlite3.Connection) -> Iterator[sqlite3.Connection]:
    """Wrap a block in BEGIN/COMMIT, rolling back on error."""

    conn.execute("BEGIN")
    try:
        yield conn
    except Exception:
        conn.execute("ROLLBACK")
        raise
    else:
        conn.execute("COMMIT")


def get_schema_version(conn: sqlite3.Connection) -> int | None:
    row = conn.execute(
        "SELECT value FROM schema_meta WHERE key = 'schema_version'"
    ).fetchone()
    if row is None:
        return None
    return int(row["value"])
