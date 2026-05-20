"""Verify the most recent transcribe job against the integration checklist.

Run after the end-to-end transcribe finishes:

    python tests/integration/verify_run.py [job_id]

Without ``job_id`` we pick the most recently created job. The script
reports each checklist item with PASS/FAIL/INFO so the result is easy to
paste into ``tests/integration/results.md``.
"""

from __future__ import annotations

import sys
from pathlib import Path

from pulpitink.storage.database import connect, default_db_path, initialise_database
from pulpitink.storage.job_repository import JobRepository


def _row(label: str, status: str, detail: str = "") -> str:
    return f"[{status}] {label}{(' — ' + detail) if detail else ''}"


def verify(job_id: str | None = None) -> int:
    initialise_database()
    conn = connect()
    repo = JobRepository(conn)
    try:
        if job_id is None:
            rows = repo.list_jobs(limit=1)
            if not rows:
                print(_row("최근 작업", "FAIL", "DB에 작업 기록이 없습니다."))
                return 1
            job = repo.get_job(rows[0].id)
        else:
            job = repo.get_job(job_id)
        if job is None:
            print(_row("작업 조회", "FAIL", f"job_id={job_id} 없음"))
            return 1
        print(_row("작업 ID", "INFO", job.id))
        print(_row("상태", "PASS" if job.status == "completed" else "FAIL", job.status))
        print(_row(
            "모델/프리셋",
            "INFO",
            f"{job.model_name} / {job.preset} / lang={job.language or 'auto'}",
        ))
        if job.duration_sec:
            print(_row("길이", "INFO", f"{job.duration_sec:.1f}s"))

        segments = repo.list_segments(job.id)
        print(_row("세그먼트 개수", "PASS" if segments else "FAIL", str(len(segments))))

        non_empty_raw = [s for s in segments if s.raw_text.strip()]
        print(_row(
            "raw_text 비어있지 않음",
            "PASS" if non_empty_raw else "FAIL",
            f"{len(non_empty_raw)}/{len(segments)}",
        ))

        clean_diff = [
            s for s in segments
            if s.clean_text and s.clean_text != s.raw_text
        ]
        print(_row(
            "후처리 흔적 (clean_text != raw_text)",
            "PASS" if clean_diff else "INFO",
            f"{len(clean_diff)}건",
        ))

        needs_review = [s for s in segments if s.needs_review]
        print(_row(
            "needs_review 표시",
            "INFO",
            f"{len(needs_review)}건 (신뢰도 낮은 세그먼트)",
        ))

        exports = repo.list_exports(job.id)
        formats = sorted({e.format for e in exports})
        expected = {"txt", "json", "md", "srt", "vtt", "csv"}
        missing = expected - set(formats)
        print(_row(
            "Export 6종",
            "PASS" if not missing else "FAIL",
            f"생성={','.join(formats) or '(없음)'} / 누락={','.join(sorted(missing)) or '없음'}",
        ))
        for e in exports:
            exists = Path(e.output_path).exists()
            print(_row(f"  - {e.format} 파일 존재", "PASS" if exists else "FAIL", e.output_path))

        # Reference workflow
        refs = list(conn.execute(
            "SELECT id, source_path, title, length(content) AS content_len, "
            "       bible_refs, keywords, proper_nouns "
            "FROM reference_documents WHERE job_id = ?",
            (job.id,),
        ).fetchall())
        print(_row(
            "reference_documents",
            "PASS" if refs else "FAIL",
            f"{len(refs)}건",
        ))
        import json as _json
        for r in refs:
            bible = _json.loads(r["bible_refs"] or "[]")
            kws = _json.loads(r["keywords"] or "[]")
            nouns = _json.loads(r["proper_nouns"] or "[]")
            print(_row(
                "  - 원문 메타",
                "INFO",
                f"title={r['title']!r} chars={r['content_len']} "
                f"bible_refs={len(bible)} keywords={len(kws)} proper_nouns={len(nouns)}",
            ))

        pairs = conn.execute(
            "SELECT COUNT(*) AS c FROM alignment_pairs WHERE job_id = ?",
            (job.id,),
        ).fetchone()
        pair_count = pairs["c"] if pairs else 0
        print(_row(
            "alignment_pairs",
            "PASS" if pair_count else "INFO",
            f"{pair_count}건",
        ))

        suggestions = repo.list_correction_suggestions(job.id)
        pending = [s for s in suggestions if s.status == "pending"]
        kinds = sorted({s.kind for s in suggestions})
        print(_row(
            "correction_suggestions",
            "PASS" if suggestions else "INFO",
            f"총 {len(suggestions)}건 / pending {len(pending)} / kinds={','.join(kinds) or '없음'}",
        ))

        print(_row("DB 경로", "INFO", str(default_db_path())))
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else None
    raise SystemExit(verify(arg))
