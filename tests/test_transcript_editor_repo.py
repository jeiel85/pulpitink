"""Headless tests for the editor's storage interactions.

The full :class:`TranscriptEditorWidget` requires a Qt event loop, but the
DB-side operations it triggers (edit segment, apply correction, ignore
correction) are pure repository calls. This module verifies them
end-to-end without needing PySide6 installed.
"""

from __future__ import annotations

from pathlib import Path

from pulpit_ink.core.reference.corrections import apply_correction_to_segment
from pulpit_ink.storage.database import connect, initialise_database
from pulpit_ink.storage.job_repository import (
    CorrectionSuggestionRecord,
    JobRepository,
    SegmentRecord,
)


def _setup(tmp_path: Path) -> tuple[Path, int, int]:
    db = tmp_path / "editor.db"
    initialise_database(db)
    with connect(db) as conn:
        repo = JobRepository(conn)
        repo.create_job(
            job_id="ed1",
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
                    job_id="ed1",
                    start_sec=0.0,
                    end_sec=1.0,
                    raw_text="오늘 본문은 고린도 전서 1장입니다.",
                    clean_text="오늘 본문은 고린도전서 1장입니다.",
                )
            ]
        )
        seg = repo.list_segments("ed1")[0]
        repo.add_correction_suggestions(
            [
                CorrectionSuggestionRecord(
                    job_id="ed1",
                    segment_id=seg.id,
                    kind="user_dict",
                    original_text="고린도 전서",
                    suggested_text="고린도전서",
                    source="lexicon",
                )
            ]
        )
        sug_id = repo.list_correction_suggestions("ed1")[0].id
    return db, seg.id, sug_id


def test_editor_apply_correction_updates_edited_text(tmp_path: Path) -> None:
    db, segment_id, suggestion_id = _setup(tmp_path)
    with connect(db) as conn:
        repo = JobRepository(conn)
        sug = [
            s for s in repo.list_correction_suggestions("ed1") if s.id == suggestion_id
        ][0]
        seg = repo.get_segment(segment_id)
        new_text = apply_correction_to_segment(
            raw_text=seg.raw_text,
            clean_text=seg.clean_text,
            edited_text=seg.edited_text,
            original=sug.original_text,
            suggested=sug.suggested_text,
        )
        repo.update_segment_text(segment_id, edited_text=new_text)
        repo.update_correction_status(suggestion_id, status="applied")

        refreshed = repo.get_segment(segment_id)
        assert refreshed.edited_text == "오늘 본문은 고린도전서 1장입니다."
        assert refreshed.raw_text == "오늘 본문은 고린도 전서 1장입니다."  # immutable
        applied = repo.list_correction_suggestions("ed1", status="applied")
        assert len(applied) == 1


def test_editor_ignore_correction(tmp_path: Path) -> None:
    db, _segment_id, suggestion_id = _setup(tmp_path)
    with connect(db) as conn:
        repo = JobRepository(conn)
        repo.update_correction_status(suggestion_id, status="ignored")
        ignored = repo.list_correction_suggestions("ed1", status="ignored")
        assert len(ignored) == 1


def test_editor_needs_review_toggle(tmp_path: Path) -> None:
    db, segment_id, _ = _setup(tmp_path)
    with connect(db) as conn:
        repo = JobRepository(conn)
        repo.update_segment_text(segment_id, needs_review=True)
        assert repo.get_segment(segment_id).needs_review is True
        repo.update_segment_text(segment_id, needs_review=False)
        assert repo.get_segment(segment_id).needs_review is False
