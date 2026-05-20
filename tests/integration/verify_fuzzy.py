"""Verify fuzzy matching suggestions on the existing integration database."""

from __future__ import annotations

import json
from sermonscript.storage.database import connect, initialise_database
from sermonscript.storage.job_repository import JobRepository
from sermonscript.core.reference.corrections import CorrectionEngine
from sermonscript.core.postprocess.lexicon import default_lexicon

def run_fuzzy_verification():
    initialise_database()
    conn = connect()
    repo = JobRepository(conn)
    
    try:
        rows = repo.list_jobs(limit=1)
        if not rows:
            print("DB에 작업 기록이 없습니다.")
            return
        
        job = repo.get_job(rows[0].id)
        print(f"=== 검증 대상 작업: ID={job.id}, 모델={job.model_name}, 프리셋={job.preset} ===")
        
        # 1. Reference 정보 가져오기
        ref_row = conn.execute(
            "SELECT bible_refs, keywords, proper_nouns FROM reference_documents WHERE job_id = ?",
            (job.id,),
        ).fetchone()
        
        if not ref_row:
            print("작업에 연동된 reference_document가 없습니다.")
            return
            
        proper_nouns = json.loads(ref_row["proper_nouns"] or "[]")
        keywords = json.loads(ref_row["keywords"] or "[]")
        print(f"원문 proper_nouns 개수: {len(proper_nouns)}")
        print(f"원문 keywords 개수: {len(keywords)}")
        
        # 2. 세그먼트 데이터 가져오기
        segments = repo.list_segments(job.id)
        print(f"전체 세그먼트 개수: {len(segments)}")
        
        # 3. Fuzzy 매칭 미활성화 시 제안
        engine_no_fuzzy = CorrectionEngine(
            lexicon=default_lexicon(),
            proper_nouns=proper_nouns,
            fuzzy_matching_enabled=False,
        )
        
        suggestions_no_fuzzy = []
        for s in segments:
            res = engine_no_fuzzy.suggestions_for(s.id if s.id is not None else 0, s.raw_text)
            suggestions_no_fuzzy.extend(res)
            
        # 4. Fuzzy 매칭 활성화 시 제안 (Threshold = 0.70)
        engine_fuzzy_70 = CorrectionEngine(
            lexicon=default_lexicon(),
            proper_nouns=proper_nouns,
            fuzzy_matching_enabled=True,
            fuzzy_threshold=0.70,
        )
        
        suggestions_fuzzy_70 = []
        for s in segments:
            res = engine_fuzzy_70.suggestions_for(s.id if s.id is not None else 0, s.raw_text)
            suggestions_fuzzy_70.extend(res)
            
        # 5. Fuzzy 매칭 활성화 시 제안 (Threshold = 0.65)
        engine_fuzzy_65 = CorrectionEngine(
            lexicon=default_lexicon(),
            proper_nouns=proper_nouns,
            fuzzy_matching_enabled=True,
            fuzzy_threshold=0.65,
        )
        
        suggestions_fuzzy_65 = []
        for s in segments:
            res = engine_fuzzy_65.suggestions_for(s.id if s.id is not None else 0, s.raw_text)
            suggestions_fuzzy_65.extend(res)

        print("\n=== 결과 비교 ===")
        print(f"1. Fuzzy 비활성화 시 제안 수: {len(suggestions_no_fuzzy)}건")
        print(f"2. Fuzzy 활성화(0.70) 시 제안 수: {len(suggestions_fuzzy_70)}건")
        print(f"3. Fuzzy 활성화(0.65) 시 제안 수: {len(suggestions_fuzzy_65)}건")
        
        print("\n=== Fuzzy 활성화(0.70)로 감지된 신규 제안 목록 (최대 30건) ===")
        diff_suggestions = [
            s for s in suggestions_fuzzy_70 
            if not any(ns.original_text == s.original_text and ns.suggested_text == s.suggested_text for ns in suggestions_no_fuzzy)
        ]
        
        print(f"신규 추가된 Fuzzy 제안 수: {len(diff_suggestions)}건")
        for i, s in enumerate(diff_suggestions[:30]):
            seg = next(seg for seg in segments if seg.id == s.segment_index)
            print(f"[{i+1}] 세그먼트 {s.segment_index} (시간: {seg.start_sec:.1f}s):")
            print(f"  - 원문 발화: {seg.raw_text!r}")
            print(f"  - 제안: {s.original_text!r} -> {s.suggested_text!r} (출처: {s.source})")
            
    finally:
        conn.close()

if __name__ == "__main__":
    run_fuzzy_verification()
