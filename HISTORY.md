# HISTORY.md

## 2026-05-20 (핸드오프 정리 — 다음 작업 후보)
- 작업: 최신 CI/릴리즈 검증 상태와 이전 세션의 남은 기능 후보를 확인하고, 다음 세션에서 이어받기 쉬운 우선순위 목록을 `docs/roadmap-tasks.md` 상단에 정리.
- 변경 파일:
  - docs/roadmap-tasks.md
  - HISTORY.md
- 검증:
  - `gh run list --limit 12`: 최신 `Test` 성공, 최신 `Build Windows Portable` 수동 실행 성공 확인
  - `gh run view 26146847983`: `SermonScript-Portable` artifact 업로드 확인
  - 코드 변경 없음 — 테스트/린트는 실행하지 않음
- 결과: 다음 세션 후보를 CSV Export, 캐시 삭제/작업 삭제 UX, 최근 작업 기록 비활성화, Jamo fuzzy 문서 정리, 오디오 싱크 플레이어, 다중 작업 큐, `frontend/` 산출물 정책 순으로 정리.
- 후속 작업:
  - 다음 세션에서 1순위 후보인 CSV Export부터 구현 검토
  - `frontend/` untracked 산출물의 보존/분리/정리 정책 결정

## 2026-05-20 (CI Hotfix #14 — Windows 빌드 workflow spec 누락)
- 작업: 핸드오프 후속 항목 중 GitHub Actions `build-windows.yml` 검증을 진행하고, 수동 실행 실패 원인을 수정.
- 변경 파일:
  - .gitignore (`sermonscript.spec`만 추적 가능하도록 예외 추가)
  - sermonscript.spec (Windows PyInstaller GUI 번들 spec을 저장소에 포함)
  - HISTORY.md
  - CHANGELOG.md
- 검증:
  - `gh workflow run build-windows.yml --ref main`: 실패 재현 (`Spec file "sermonscript.spec" not found!`)
  - `python -m ruff check .`: PASS
  - `python -m pytest`: 91/91 PASS
  - `python -m sermonscript.cli.main doctor`: PASS
- 결과: CI 실패 원인은 PyInstaller spec 파일이 `.gitignore`의 `*.spec`에 의해 미추적 상태였기 때문으로 확인. 루트 `sermonscript.spec`를 추적 대상에 포함하도록 수정.
- 후속 작업:
  - 수정 커밋 푸시 후 GitHub Actions `build-windows.yml` 재실행 결과 확인
  - 깨끗한 Windows VM에서 GUI 실행 수동 검증
  - `frontend/` untracked 산출물의 보존/정리 정책 결정

## 2026-05-20 (릴리즈 검증 #13 — 로컬 품질/패키징 체크)
- 작업: 핸드오프 후보 문서와 릴리즈 체크리스트를 확인하고, 현재 `main` 기준 로컬 품질 검사와 Windows Portable ZIP 생성을 재검증.
- 변경 파일:
  - pyproject.toml (`frontend/` untracked Tauri/번들 산출물이 `ruff check .` 대상에 섞이지 않도록 제외)
  - src/sermonscript/core/postprocess/jamo.py (`rapidfuzz` 미설치 기본 CI 환경에서 `difflib` fallback 사용)
  - tests/integration/verify_fuzzy.py (Ruff import 정렬/공백 정리)
  - docs/release/release-checklist.md (검증 완료 항목 갱신)
  - HISTORY.md
  - CHANGELOG.md
- 검증:
  - `python -m ruff check .`: PASS
  - `python -m pytest`: 91/91 PASS
  - `python -m sermonscript.cli.main doctor`: PASS
  - `./scripts/build_windows.ps1 -SkipChecks`: PASS
  - 산출물: `dist/SermonScript_Portable_0.3.0.zip` (172,800,567 bytes)
- 결과: 로컬 품질 검사와 PyInstaller/Portable ZIP 생성 검증 완료. 기본 설치 CI에서 `rapidfuzz`가 없어도 Jamo fuzzy 유틸이 import 가능하도록 보완.
- 후속 작업:
  - 깨끗한 Windows VM에서 GUI 실행 수동 검증
  - GitHub Actions `build-windows.yml` 태그/수동 실행 검증
  - `frontend/` untracked 산출물의 보존/정리 정책 결정

## 2026-05-20 (구현 #12 — jamo fuzzy matching 통합 및 검증)
- 작업: 회차 #1 에서 발견한 `correction_suggestions=0` 문제(자모 변형 미매칭)의 설계 및 구현 완료. 한글 NFD 자모 분해 및 초성 가중 평균 기반의 Hybrid Scorer를 탑재한 Fuzzy 매칭 알고리즘을 `CorrectionEngine`에 연동. CLI 옵션(`--fuzzy/--no-fuzzy`, `--fuzzy-threshold`) 및 PySide6 GUI(체크박스, 더블 스핀박스)로 완전 노출 및 영속화 파이프라인 통합.
- 변경 파일:
  - src/sermonscript/core/postprocess/jamo.py (신규)
  - src/sermonscript/core/reference/corrections.py (CorrectionEngine 연동)
  - src/sermonscript/services/settings_service.py (Settings schema 확장 및 Coercion 보장)
  - src/sermonscript/services/transcribe_service.py (Fuzzy 파라미터 전파)
  - src/sermonscript/cli/main.py (CLI 인수 추가)
  - src/sermonscript/ui/main_window.py (GUI 설정 컨트롤 셋 연동)
  - tests/test_jamo_matching.py (신규)
  - tests/integration/verify_fuzzy.py (신규: 인메모리 시뮬레이터)
  - tests/integration/results.md (회차 #2 추가)
  - docs/known-limitations.md (§10 갱신)
  - docs/user-guide.md (§6.1, §8.2 갱신)
- 검증:
  - `python -m pytest`: 90/90 PASS (신규 유닛 테스트 5건 포함)
  - `python -m ruff check .`: All checks passed!
  - `verify_fuzzy.py` 641 세그먼트 시뮬레이션 결과:
    - Fuzzy 비활성화 시: 0건
    - Fuzzy 활성화(0.70) 시: 292건 검출 성공 (기존 오인식 "이에수 크리스토리" -> "예수 그리스도", "사도로 부르신을 받아" -> "사도로 부르심을 받아" 완벽 회복!)
- 결과: Jamo Fuzzy 매칭 도입을 통해 0건의 자동 교정 후보 문제를 해결하고 v1.0 정식 마일스톤에 안전하게 통합 완료.

## 2026-05-20 (Hotfix #11 — bible_refs 콜론 표기)
- 작업: 통합 회귀 #1 에서 발견한 `parser._BIBLE_REF_RE` 한계 수정. 원문의
  `로마서 3: 21~22` 콜론 표기를 잡지 못해 reference_documents.bible_refs 가
  0건이 되던 문제.
- 변경 파일:
  - src/sermonscript/core/reference/parser.py (`_BIBLE_REF_COLON_RE` 추가,
    `_extract_bible_refs` 가 두 정규식을 통합·중복 제거)
  - tests/test_reference_parser.py (test_parse_extracts_bible_refs_colon_notation,
    test_parse_deduplicates_jang_and_colon_overlap)
  - docs/known-limitations.md (§10 해당 항목 수정 표시)
  - tests/integration/results.md (Hotfix 노트)
  - CHANGELOG.md
- 검증:
  - `python -m pytest`: 85/85 PASS (신규 2건 포함)
  - `python -m ruff check .`: PASS
  - 실제 fixture (`tests/integration/fixtures/sermon.md`) 직접 파싱:
    `bible_refs = ['로마서 3장 21-22절']` (이전 0건 → 1건)
- 결과: 성공
- 후속 작업:
  - 같은 입력으로 통합 회귀 회차 #2 실행해 DB 영속화 단계까지 회복 재확인 (선택)
  - #12 (자모 변형 매칭) 여부 결정

## 2026-05-20 (통합 회귀 #1)
- 작업: 35분 분량 실설교 MP3 + Markdown 원문으로 end-to-end 통합 회귀 1회 실행.
- 입력:
  - 오디오: `D:\Media\2026-05-13 수요밤설교 _ 로마서 1장 1-15절 _ 로마서의 서론.mp3` (35분 45초)
  - 원문(docx → md): `tests/integration/fixtures/sermon.md` (236문단, ~9.7KB)
  - 모델/프리셋: `small` / CPU `int8` / `--preset sermon`
- 변경 파일:
  - tests/integration/README.md (검증 항목 실제 결과 반영)
  - tests/integration/extract_docx.py (의존성 없는 docx → md 추출 유틸)
  - tests/integration/verify_run.py (실제 reference_documents 스키마에 맞춰 컬럼 수정)
  - tests/integration/results.md (회차 #1 결과/원인 분석)
  - tests/integration/fixtures/README.md, .gitkeep (사용자 콘텐츠 gitignore 정책)
  - docs/known-limitations.md (§10 원문 대조/자동 교정 적중률 보강)
  - .gitignore (tests/integration/out, fixtures/* 제외)
  - CHANGELOG.md
- 검증:
  - 변환 소요 1560.55초 (~26분), 641 세그먼트, Export 5종 모두 생성
  - DB 영속화 정상 (jobs/segments/exports/reference_documents/alignment_pairs)
  - `verify_run.py` 모든 PASS 항목 통과; INFO 로 0건 항목 2개 노출
- 결과: 파이프라인 자체 성공 / 자동 교정 후보 적중률 이슈 2건 발견
- 후속 작업:
  - 버그(#11): `parser._BIBLE_REF_RE` 가 콜론 표기(`로마서 3: 21~22`) 미인식 — 정규식 확장
  - 한계(#12): STT 자모 변형 (이에수/그리시도/보궁 등) 에 대한 lexicon/proper_noun 매칭 무력 — 자모 유사도 매칭 또는 lexicon 자동 확장 검토 (v1.x)
  - GUI 편집기에서 needs_review 10건 직접 검토하며 스크린샷 캡처 (release-checklist Documentation §스크린샷)

## 2026-05-20 (문서)
- 작업: v1.0 릴리즈 준비용 사용자 문서 정비 (README/사용자 가이드/알려진 제한사항).
- 변경 파일:
  - README.md (Goal 1~3 결과 반영한 본 프로젝트 진입점으로 재작성)
  - docs/user-guide.md (신규: 설치/doctor/CLI/GUI/편집기/원문 대조/사용자 사전/문제 해결)
  - docs/known-limitations.md (신규: v1.0 범위 제외/플랫폼/데이터 정책 SSOT)
  - docs/release/release-checklist.md (Documentation 섹션 갱신)
  - CHANGELOG.md
- 검증: 코드 변경 없음 — 문서만 추가/수정. 기존 `python -m pytest` / `ruff check` 결과 유지.
- 결과: 성공
- 후속 작업:
  - GUI 변환/편집기 스크린샷 캡처 후 docs/user-guide.md 와 release-checklist 에 반영
  - 실제 Windows VM 에서 PyInstaller 산출물 수동 검증 (이전 Goal 3 후속 항목 그대로)
  - 30분 분량 MP3 + 원문 대조 시나리오 통합 회귀

## 2026-05-20 (Goal 3)
- 작업: Goal 3 — 편집기/후처리/사용자 사전 + 원문 대조 + Windows 릴리즈 패키징.
- 변경 파일:
  - src/sermonscript/storage/database.py (schema v2 + 신규 테이블)
  - src/sermonscript/storage/job_repository.py (reference/alignment/correction CRUD + 세그먼트 패치)
  - src/sermonscript/core/postprocess/__init__.py
  - src/sermonscript/core/postprocess/bible_refs.py
  - src/sermonscript/core/postprocess/lexicon.py
  - src/sermonscript/core/postprocess/pipeline.py
  - src/sermonscript/core/reference/__init__.py
  - src/sermonscript/core/reference/parser.py
  - src/sermonscript/core/reference/aligner.py (rapidfuzz fallback + 안정성)
  - src/sermonscript/core/reference/prompt_builder.py
  - src/sermonscript/core/reference/corrections.py
  - src/sermonscript/services/transcribe_service.py (reference flow + needs_review + 영속화)
  - src/sermonscript/cli/main.py (transcribe --reference / --user-dict, corrections 서브커맨드)
  - src/sermonscript/ui/transcript_editor.py (편집기 위젯)
  - src/sermonscript/ui/main_window.py (편집기 탭 + 작업 로드 연결)
  - tests/test_postprocess.py
  - tests/test_reference_parser.py
  - tests/test_correction_engine.py
  - tests/test_transcript_editor_repo.py (편집기-DB 헤드리스 검증)
  - tests/test_storage.py (schema v2 회귀)
  - tests/test_transcribe_persistence.py (reference + correction 영속화 회귀)
  - sermonscript.spec
  - scripts/build_windows.ps1
  - scripts/make_portable_zip.ps1
  - .github/workflows/build-windows.yml
  - THIRD_PARTY_NOTICES.md
  - docs/release/release-checklist.md
  - docs/deferred-youtube-import.md
  - CHANGELOG.md
- 검증:
  - `python -m pytest`
  - `python -m ruff check .`
  - CLI: `sermonscript transcribe sermon.mp3 --reference sermon.md --language ko`
  - CLI: `sermonscript corrections list/apply/ignore`
- 결과: 진행 중 (이번 커밋 작성 시점)
- 후속 작업:
  - 실제 Windows VM 에서 PyInstaller 산출물 수동 검증
  - 30분 분량 MP3 + 원문 대조 시나리오 통합 회귀

## 2026-05-20
- 작업: Goal 2 — 로컬 SQLite DB, 설정/모델 서비스, jobs/settings/models CLI, PySide6 GUI 기반 구현
- 변경 파일:
  - src/sermonscript/storage/__init__.py
  - src/sermonscript/storage/database.py
  - src/sermonscript/storage/job_repository.py
  - src/sermonscript/services/settings_service.py
  - src/sermonscript/services/model_service.py
  - src/sermonscript/services/transcribe_service.py
  - src/sermonscript/services/__init__.py
  - src/sermonscript/cli/main.py
  - src/sermonscript/ui/__init__.py
  - src/sermonscript/ui/main_window.py
  - src/sermonscript/ui/worker.py
  - src/sermonscript/app/main.py
  - tests/conftest.py
  - tests/test_storage.py
  - tests/test_settings_service.py
  - tests/test_model_service.py
  - tests/test_transcribe_persistence.py
  - CHANGELOG.md
- 검증:
  - `python -m pytest`: 49 tests passed (신규 17개 포함)
  - `python -m ruff check .`: All checks passed
  - `python -m sermonscript.cli.main --help`: jobs / settings / models / db-path 명령 등록 확인
  - `python -m sermonscript.app.main`: PySide6 미설치 시 친절한 안내 메시지 출력 확인
- 결과: 성공
- 후속 작업:
  - 실제 PySide6 설치 환경에서 GUI 수동 검증
  - segments 편집(`clean_text`/`edited_text`) UI는 Goal 3 범위에서 진행

## 2026-05-19
- 작업: SermonScript 3-Goal 프롬프트 중 Goal 2의 4000자 제한 초과 문제 수정
- 변경 파일:
  - docs/vibe-coding-goal-1.md
  - docs/vibe-coding-goal-2-fixed.md
  - docs/vibe-coding-goal-3.md
  - docs/common-tail-instruction.md
  - docs/vibe-coding-goals-3phase-fixed.md
- 검증: Goal 2 본문을 축약하여 4000자 제한 내 사용 가능하도록 재구성
- 결과: 성공
- 후속 작업: 실제 에이전트 입력칸에서 Goal 2 붙여넣기 검증
