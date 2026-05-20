"""CRUD helpers for the ``jobs`` / ``segments`` / ``exports`` tables.

The repository is intentionally framework-free so both the CLI and the
PySide6 GUI can call it. All write paths preserve ``raw_text`` — once a
segment is inserted, only ``clean_text`` / ``edited_text`` /
``needs_review`` may be updated later (Goal 2 principle:
*raw_text는 덮어쓰지 않는다*).

Goal 3 adds reference documents, alignment pairs, and correction
suggestion CRUD. The lifecycle for corrections is pending → applied or
ignored — applying writes the suggested text into the segment's
``edited_text`` so the export pipeline picks it up automatically.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from pulpitink.storage.database import _transaction


def _utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


CORRECTION_STATUSES: frozenset[str] = frozenset({"pending", "applied", "ignored"})


@dataclass
class JobRecord:
    """A row from the ``jobs`` table."""

    id: str
    source_path: str
    title: str
    duration_sec: float | None
    language: str | None
    model_name: str
    engine: str
    preset: str
    status: str
    error_message: str | None
    created_at: str
    updated_at: str


@dataclass
class SegmentRecord:
    """A row from the ``segments`` table."""

    job_id: str
    start_sec: float
    end_sec: float
    raw_text: str
    clean_text: str = ""
    edited_text: str = ""
    avg_logprob: float | None = None
    no_speech_prob: float | None = None
    needs_review: bool = False
    speaker: str | None = None
    id: int | None = None


@dataclass
class ExportRecord:
    """A row from the ``exports`` table."""

    job_id: str
    format: str
    output_path: str
    created_at: str = field(default_factory=_utc_now)
    id: int | None = None


@dataclass
class ReferenceDocumentRecord:
    """A sermon reference document attached to a job."""

    job_id: str
    source_path: str
    content: str
    title: str | None = None
    bible_refs: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    proper_nouns: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=_utc_now)
    id: int | None = None


@dataclass
class AlignmentPairRecord:
    """A similarity link from a segment to a reference paragraph."""

    job_id: str
    segment_id: int
    reference_document_id: int
    reference_index: int
    score: float
    id: int | None = None


@dataclass
class CorrectionSuggestionRecord:
    """A pending correction proposal for a single segment.

    ``kind`` describes *why* we are suggesting the change (e.g. ``bible_ref``,
    ``proper_noun``, ``user_dict``) so the UI can group/filter them. ``source``
    is a short tag indicating where the rule came from (``postprocess``,
    ``reference``, ``user_dict``…).
    """

    job_id: str
    segment_id: int
    kind: str
    original_text: str
    suggested_text: str
    source: str
    status: str = "pending"
    created_at: str = field(default_factory=_utc_now)
    id: int | None = None


class JobRepository:
    """Encapsulates DB access for transcription jobs.

    Pass in a sqlite3.Connection (typically from :func:`storage.connect`).
    The repository never closes the connection — that is the caller's job.
    """

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    # ---------- jobs ----------

    def create_job(
        self,
        *,
        job_id: str,
        source_path: Path | str,
        title: str,
        language: str | None,
        model_name: str,
        engine: str,
        preset: str,
        status: str = "running",
        duration_sec: float | None = None,
    ) -> JobRecord:
        now = _utc_now()
        record = JobRecord(
            id=job_id,
            source_path=str(source_path),
            title=title,
            duration_sec=duration_sec,
            language=language,
            model_name=model_name,
            engine=engine,
            preset=preset,
            status=status,
            error_message=None,
            created_at=now,
            updated_at=now,
        )
        with _transaction(self._conn):
            self._conn.execute(
                """
                INSERT INTO jobs (
                    id, source_path, title, duration_sec, language, model_name,
                    engine, preset, status, error_message, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.id,
                    record.source_path,
                    record.title,
                    record.duration_sec,
                    record.language,
                    record.model_name,
                    record.engine,
                    record.preset,
                    record.status,
                    record.error_message,
                    record.created_at,
                    record.updated_at,
                ),
            )
        return record

    def update_job_status(
        self,
        job_id: str,
        *,
        status: str,
        error_message: str | None = None,
        duration_sec: float | None = None,
    ) -> None:
        now = _utc_now()
        with _transaction(self._conn):
            self._conn.execute(
                """
                UPDATE jobs
                SET status = ?, error_message = ?, updated_at = ?,
                    duration_sec = COALESCE(?, duration_sec)
                WHERE id = ?
                """,
                (status, error_message, now, duration_sec, job_id),
            )

    def get_job(self, job_id: str) -> JobRecord | None:
        row = self._conn.execute(
            "SELECT * FROM jobs WHERE id = ?", (job_id,)
        ).fetchone()
        if row is None:
            return None
        return JobRecord(**row)

    def list_jobs(self, *, limit: int = 50) -> list[JobRecord]:
        rows = self._conn.execute(
            "SELECT * FROM jobs ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [JobRecord(**row) for row in rows]

    def delete_job(self, job_id: str) -> None:
        with _transaction(self._conn):
            self._conn.execute("DELETE FROM jobs WHERE id = ?", (job_id,))

    # ---------- segments ----------

    def add_segments(self, segments: Iterable[SegmentRecord]) -> int:
        rows = list(segments)
        if not rows:
            return 0
        with _transaction(self._conn):
            self._conn.executemany(
                """
                INSERT INTO segments (
                    job_id, start_sec, end_sec, raw_text, clean_text, edited_text,
                    avg_logprob, no_speech_prob, needs_review, speaker
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        seg.job_id,
                        seg.start_sec,
                        seg.end_sec,
                        seg.raw_text,
                        seg.clean_text,
                        seg.edited_text,
                        seg.avg_logprob,
                        seg.no_speech_prob,
                        1 if seg.needs_review else 0,
                        seg.speaker,
                    )
                    for seg in rows
                ],
            )
        return len(rows)

    def list_segments(self, job_id: str) -> list[SegmentRecord]:
        rows = self._conn.execute(
            "SELECT * FROM segments WHERE job_id = ? ORDER BY start_sec ASC",
            (job_id,),
        ).fetchall()
        out: list[SegmentRecord] = []
        for row in rows:
            out.append(
                SegmentRecord(
                    id=row["id"],
                    job_id=row["job_id"],
                    start_sec=row["start_sec"],
                    end_sec=row["end_sec"],
                    raw_text=row["raw_text"],
                    clean_text=row["clean_text"],
                    edited_text=row["edited_text"],
                    avg_logprob=row["avg_logprob"],
                    no_speech_prob=row["no_speech_prob"],
                    needs_review=bool(row["needs_review"]),
                    speaker=row["speaker"],
                )
            )
        return out

    def get_segment(self, segment_id: int) -> SegmentRecord | None:
        row = self._conn.execute(
            "SELECT * FROM segments WHERE id = ?", (segment_id,)
        ).fetchone()
        if row is None:
            return None
        return SegmentRecord(
            id=row["id"],
            job_id=row["job_id"],
            start_sec=row["start_sec"],
            end_sec=row["end_sec"],
            raw_text=row["raw_text"],
            clean_text=row["clean_text"],
            edited_text=row["edited_text"],
            avg_logprob=row["avg_logprob"],
            no_speech_prob=row["no_speech_prob"],
            needs_review=bool(row["needs_review"]),
            speaker=row["speaker"],
        )

    def update_segment_text(
        self,
        segment_id: int,
        *,
        clean_text: str | None = None,
        edited_text: str | None = None,
        needs_review: bool | None = None,
    ) -> None:
        """Patch the editable fields of a segment.

        ``raw_text`` is intentionally not accepted here — once written, the
        original STT output is immutable. Pass ``None`` to leave a field
        untouched.
        """

        sets: list[str] = []
        values: list[object] = []
        if clean_text is not None:
            sets.append("clean_text = ?")
            values.append(clean_text)
        if edited_text is not None:
            sets.append("edited_text = ?")
            values.append(edited_text)
        if needs_review is not None:
            sets.append("needs_review = ?")
            values.append(1 if needs_review else 0)
        if not sets:
            return
        values.append(segment_id)
        with _transaction(self._conn):
            self._conn.execute(
                f"UPDATE segments SET {', '.join(sets)} WHERE id = ?",
                values,
            )

    # ---------- exports ----------

    def add_exports(self, exports: Iterable[ExportRecord]) -> int:
        rows = list(exports)
        if not rows:
            return 0
        with _transaction(self._conn):
            self._conn.executemany(
                """
                INSERT INTO exports (job_id, format, output_path, created_at)
                VALUES (?, ?, ?, ?)
                """,
                [
                    (rec.job_id, rec.format, rec.output_path, rec.created_at)
                    for rec in rows
                ],
            )
        return len(rows)

    def list_exports(self, job_id: str) -> list[ExportRecord]:
        rows = self._conn.execute(
            "SELECT * FROM exports WHERE job_id = ? ORDER BY id ASC",
            (job_id,),
        ).fetchall()
        return [
            ExportRecord(
                id=row["id"],
                job_id=row["job_id"],
                format=row["format"],
                output_path=row["output_path"],
                created_at=row["created_at"],
            )
            for row in rows
        ]

    # ---------- reference documents ----------

    def add_reference_document(self, doc: ReferenceDocumentRecord) -> ReferenceDocumentRecord:
        with _transaction(self._conn):
            cursor = self._conn.execute(
                """
                INSERT INTO reference_documents (
                    job_id, source_path, title, content, bible_refs, keywords,
                    proper_nouns, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    doc.job_id,
                    doc.source_path,
                    doc.title,
                    doc.content,
                    json.dumps(doc.bible_refs, ensure_ascii=False),
                    json.dumps(doc.keywords, ensure_ascii=False),
                    json.dumps(doc.proper_nouns, ensure_ascii=False),
                    doc.created_at,
                ),
            )
            doc.id = int(cursor.lastrowid)
        return doc

    def list_reference_documents(self, job_id: str) -> list[ReferenceDocumentRecord]:
        rows = self._conn.execute(
            "SELECT * FROM reference_documents WHERE job_id = ? ORDER BY id ASC",
            (job_id,),
        ).fetchall()
        return [
            ReferenceDocumentRecord(
                id=row["id"],
                job_id=row["job_id"],
                source_path=row["source_path"],
                title=row["title"],
                content=row["content"],
                bible_refs=json.loads(row["bible_refs"] or "[]"),
                keywords=json.loads(row["keywords"] or "[]"),
                proper_nouns=json.loads(row["proper_nouns"] or "[]"),
                created_at=row["created_at"],
            )
            for row in rows
        ]

    # ---------- alignment pairs ----------

    def add_alignment_pairs(self, pairs: Iterable[AlignmentPairRecord]) -> int:
        rows = list(pairs)
        if not rows:
            return 0
        with _transaction(self._conn):
            self._conn.executemany(
                """
                INSERT INTO alignment_pairs (
                    job_id, segment_id, reference_document_id, reference_index, score
                ) VALUES (?, ?, ?, ?, ?)
                """,
                [
                    (
                        rec.job_id,
                        rec.segment_id,
                        rec.reference_document_id,
                        rec.reference_index,
                        rec.score,
                    )
                    for rec in rows
                ],
            )
        return len(rows)

    def list_alignment_pairs(self, job_id: str) -> list[AlignmentPairRecord]:
        rows = self._conn.execute(
            "SELECT * FROM alignment_pairs WHERE job_id = ? ORDER BY id ASC",
            (job_id,),
        ).fetchall()
        return [
            AlignmentPairRecord(
                id=row["id"],
                job_id=row["job_id"],
                segment_id=row["segment_id"],
                reference_document_id=row["reference_document_id"],
                reference_index=row["reference_index"],
                score=row["score"],
            )
            for row in rows
        ]

    # ---------- correction suggestions ----------

    def add_correction_suggestions(
        self, suggestions: Iterable[CorrectionSuggestionRecord]
    ) -> int:
        rows = list(suggestions)
        if not rows:
            return 0
        with _transaction(self._conn):
            self._conn.executemany(
                """
                INSERT INTO correction_suggestions (
                    job_id, segment_id, kind, original_text, suggested_text,
                    source, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        rec.job_id,
                        rec.segment_id,
                        rec.kind,
                        rec.original_text,
                        rec.suggested_text,
                        rec.source,
                        rec.status,
                        rec.created_at,
                    )
                    for rec in rows
                ],
            )
        return len(rows)

    def list_correction_suggestions(
        self,
        job_id: str,
        *,
        status: str | None = None,
    ) -> list[CorrectionSuggestionRecord]:
        if status is None:
            rows = self._conn.execute(
                "SELECT * FROM correction_suggestions WHERE job_id = ? ORDER BY id ASC",
                (job_id,),
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT * FROM correction_suggestions WHERE job_id = ? AND status = ? "
                "ORDER BY id ASC",
                (job_id, status),
            ).fetchall()
        return [
            CorrectionSuggestionRecord(
                id=row["id"],
                job_id=row["job_id"],
                segment_id=row["segment_id"],
                kind=row["kind"],
                original_text=row["original_text"],
                suggested_text=row["suggested_text"],
                source=row["source"],
                status=row["status"],
                created_at=row["created_at"],
            )
            for row in rows
        ]

    def update_correction_status(self, suggestion_id: int, *, status: str) -> None:
        if status not in CORRECTION_STATUSES:
            raise ValueError(
                f"잘못된 correction status: {status!r}. "
                f"허용: {sorted(CORRECTION_STATUSES)}"
            )
        with _transaction(self._conn):
            self._conn.execute(
                "UPDATE correction_suggestions SET status = ? WHERE id = ?",
                (status, suggestion_id),
            )
