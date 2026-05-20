"""Tests for the SQLite storage layer."""

from __future__ import annotations

from pathlib import Path

import pytest

from sermonscript.storage.database import (
    SCHEMA_VERSION,
    connect,
    get_schema_version,
    initialise_database,
)
from sermonscript.storage.job_repository import (
    AlignmentPairRecord,
    CorrectionSuggestionRecord,
    ExportRecord,
    JobRepository,
    ReferenceDocumentRecord,
    SegmentRecord,
)


def _make_db(tmp_path: Path) -> Path:
    db = tmp_path / "test.db"
    initialise_database(db)
    return db


def test_initialise_creates_tables_and_meta(tmp_path: Path) -> None:
    db = _make_db(tmp_path)
    assert db.exists()
    with connect(db) as conn:
        names = {
            row["name"]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        expected = {
            "jobs",
            "segments",
            "exports",
            "schema_meta",
            "reference_documents",
            "alignment_pairs",
            "correction_suggestions",
        }
        assert expected <= names
        assert get_schema_version(conn) == SCHEMA_VERSION


def test_initialise_is_idempotent(tmp_path: Path) -> None:
    db = _make_db(tmp_path)
    initialise_database(db)
    initialise_database(db)
    with connect(db) as conn:
        assert get_schema_version(conn) == SCHEMA_VERSION


def test_job_repository_roundtrip(tmp_path: Path) -> None:
    db = _make_db(tmp_path)
    with connect(db) as conn:
        repo = JobRepository(conn)
        job = repo.create_job(
            job_id="abc123",
            source_path=tmp_path / "input.wav",
            title="input",
            language="ko",
            model_name="small",
            engine="StubEngine",
            preset="sermon",
        )
        assert job.status == "running"

        repo.add_segments(
            [
                SegmentRecord(
                    job_id="abc123",
                    start_sec=0.0,
                    end_sec=1.5,
                    raw_text="첫 번째",
                    avg_logprob=-0.1,
                    no_speech_prob=0.05,
                ),
                SegmentRecord(
                    job_id="abc123",
                    start_sec=1.5,
                    end_sec=3.0,
                    raw_text="두 번째",
                ),
            ]
        )
        repo.add_exports(
            [
                ExportRecord(job_id="abc123", format="txt", output_path="/tmp/a.txt"),
                ExportRecord(job_id="abc123", format="json", output_path="/tmp/a.json"),
            ]
        )
        repo.update_job_status(
            "abc123", status="completed", duration_sec=3.0
        )

        fetched = repo.get_job("abc123")
        assert fetched is not None
        assert fetched.status == "completed"
        assert fetched.duration_sec == 3.0

        segs = repo.list_segments("abc123")
        assert [s.raw_text for s in segs] == ["첫 번째", "두 번째"]
        assert segs[0].avg_logprob == pytest.approx(-0.1)

        exports = repo.list_exports("abc123")
        assert {e.format for e in exports} == {"txt", "json"}


def test_update_segment_text_preserves_raw(tmp_path: Path) -> None:
    db = _make_db(tmp_path)
    with connect(db) as conn:
        repo = JobRepository(conn)
        repo.create_job(
            job_id="seg1",
            source_path="x.wav",
            title="x",
            language="ko",
            model_name="small",
            engine="StubEngine",
            preset="sermon",
        )
        repo.add_segments(
            [
                SegmentRecord(
                    job_id="seg1",
                    start_sec=0.0,
                    end_sec=1.0,
                    raw_text="원본 문장",
                )
            ]
        )
        seg = repo.list_segments("seg1")[0]
        repo.update_segment_text(
            seg.id,
            clean_text="정리된 문장",
            edited_text="편집된 문장",
            needs_review=True,
        )
        updated = repo.list_segments("seg1")[0]
        assert updated.raw_text == "원본 문장"  # raw_text never overwritten
        assert updated.clean_text == "정리된 문장"
        assert updated.edited_text == "편집된 문장"
        assert updated.needs_review is True


def test_reference_alignment_suggestion_roundtrip(tmp_path: Path) -> None:
    db = _make_db(tmp_path)
    with connect(db) as conn:
        repo = JobRepository(conn)
        repo.create_job(
            job_id="ref1",
            source_path="x.wav",
            title="x",
            language="ko",
            model_name="small",
            engine="StubEngine",
            preset="sermon",
        )
        repo.add_segments(
            [SegmentRecord(job_id="ref1", start_sec=0.0, end_sec=1.0, raw_text="seg")]
        )
        seg = repo.list_segments("ref1")[0]
        doc = repo.add_reference_document(
            ReferenceDocumentRecord(
                job_id="ref1",
                source_path="sermon.md",
                title="제목",
                content="본문",
                bible_refs=["로마서 1장 1절"],
                keywords=["복음"],
                proper_nouns=["John"],
            )
        )
        assert doc.id is not None

        repo.add_alignment_pairs(
            [
                AlignmentPairRecord(
                    job_id="ref1",
                    segment_id=seg.id,
                    reference_document_id=doc.id,
                    reference_index=0,
                    score=88.5,
                )
            ]
        )
        repo.add_correction_suggestions(
            [
                CorrectionSuggestionRecord(
                    job_id="ref1",
                    segment_id=seg.id,
                    kind="bible_ref",
                    original_text="로마서 일장 일절",
                    suggested_text="로마서 1장 1절",
                    source="postprocess",
                )
            ]
        )

        loaded_docs = repo.list_reference_documents("ref1")
        assert len(loaded_docs) == 1
        assert loaded_docs[0].bible_refs == ["로마서 1장 1절"]

        pairs = repo.list_alignment_pairs("ref1")
        assert len(pairs) == 1
        assert pairs[0].score == pytest.approx(88.5)

        pending = repo.list_correction_suggestions("ref1", status="pending")
        assert len(pending) == 1
        suggestion = pending[0]

        repo.update_correction_status(suggestion.id, status="applied")
        applied = repo.list_correction_suggestions("ref1", status="applied")
        assert len(applied) == 1


def test_correction_status_rejects_unknown(tmp_path: Path) -> None:
    db = _make_db(tmp_path)
    with connect(db) as conn:
        repo = JobRepository(conn)
        with pytest.raises(ValueError):
            repo.update_correction_status(999, status="bogus")


def test_cascade_delete_removes_children(tmp_path: Path) -> None:
    db = _make_db(tmp_path)
    with connect(db) as conn:
        repo = JobRepository(conn)
        repo.create_job(
            job_id="zzz",
            source_path="x.wav",
            title="x",
            language="ko",
            model_name="small",
            engine="StubEngine",
            preset="sermon",
        )
        repo.add_segments(
            [SegmentRecord(job_id="zzz", start_sec=0.0, end_sec=1.0, raw_text="a")]
        )
        repo.add_exports(
            [ExportRecord(job_id="zzz", format="txt", output_path="/tmp/x.txt")]
        )
        repo.delete_job("zzz")
        assert repo.list_segments("zzz") == []
        assert repo.list_exports("zzz") == []
