# CHANGELOG.md

## Unreleased - 2026-05-20 (Feature: Korean Jamo-based Fuzzy Matching)

### Added
- **한국어 자모(Jamo) Fuzzy 매칭 구현** (`src/sermonscript/core/postprocess/jamo.py`):
  - 한글 유니코드 NFD 자모 분해(`jamo_seq`) 및 초성 추출(`choseong`) 헬퍼 구현.
  - 자모 매칭 비율(60%) 및 초성 매칭 비율(40%)을 결합한 **Hybrid 유사도 Scorer** 탑재.
  - 슬라이딩 윈도우 스캔 및 Double-pass Jamo ratio 검사(>= 50%)를 통한 거짓 양성(False Positive) 방지 및 최소 음절 길이 3 미만 게이트 적용.
- **CorrectionEngine 연동** (`src/sermonscript/core/reference/corrections.py`):
  - `CorrectionEngine` 파라미터로 `fuzzy_matching_enabled`와 `fuzzy_threshold` 추가.
  - `suggestions_for`에서 고유명사 및 lexicon 단어들을 대상으로 Fuzzy 매치 수행 후 `reference+fuzzy:<score>` 소스의 `proper_noun` 제안 생성.
- **설정 및 영속화 확장**:
  - `Settings` 데이터클래스에 `fuzzy_matching_enabled`와 `fuzzy_threshold` 기본값(True, 0.70) 적용.
  - `SettingsService` 및 `TranscribeRequest` 필드 연동 완료.
- **CLI/GUI 제어 패널**:
  - `sermonscript transcribe` CLI 인자 `--fuzzy/--no-fuzzy` 및 `--fuzzy-threshold` 추가.
  - PySide6 GUI 설정 영역에 체크박스 및 더블 스핀박스(0.60~0.90) 위젯 연동 완료.

### Improved
- **문서화 갱신**:
  - `docs/known-limitations.md`에 v1.0 릴리즈 패치 포함 및 작동 한계/우회방법 명시.
  - `docs/user-guide.md`에 Fuzzy 매칭 원리, CLI/GUI 제어, 권장 임계값 가이드 추가.
  - `tests/integration/results.md`에 통합 회차 #2 결과 기록 추가.

### Tests
- `tests/test_jamo_matching.py` 신규 작성 (자모 분해, 초성 추출, hybrid 유사도, 슬라이딩 윈도우 스캔 단위 테스트 5건).
- `tests/integration/verify_fuzzy.py` 신규 작성 (실제 DB 세그먼트 데이터 641개에 대한 Fuzzy 효과 측정 검증 스크립트).
- `python -m pytest`: 90/90 테스트 통과 완료.

## Unreleased - 2026-05-20 (Hotfix: bible_refs colon notation)

### Fixed
- `core.reference.parser._BIBLE_REF_RE` 는 `장` 키워드를 강제해서 인쇄된
  설교 원문에 흔한 콜론 표기(`로마서 3: 21~22`, `요한복음 3:16-17`)를 인식하지
  못했습니다. 신규 `_BIBLE_REF_COLON_RE` 와 통합된 `_extract_bible_refs` 가
  두 표기를 모두 `BOOK C장 S(-E)절` 캐노니컬 형태로 정규화합니다.
- 통합 회귀 회차 #1 에서 bible_refs=0 로 관찰된 회귀가 해소됩니다. 같은
  fixture (`로마서 1장 1-15절` 설교 원문) 재파싱 결과: `['로마서 3장 21-22절']`.

### Tests
- `tests/test_reference_parser.py` 에 콜론 표기 추출/중복 제거 테스트 2건 추가.
  전체 스위트 85/85 PASS, `ruff check` 그린.

## Unreleased - 2026-05-20 (Integration regression #1)

### Added
- `tests/integration/` 디렉터리: 수동 회귀 시나리오 정의(README), docx → md
  추출 유틸(extract_docx.py), 결과 검증 스크립트(verify_run.py),
  회차 누적 로그(results.md). 사용자 콘텐츠는 gitignore 로 분리.
- `docs/known-limitations.md` §10 — 35분 실설교 회귀에서 관찰된 원문 대조 /
  자동 교정 적중률 한계와 우회 안내.

### Findings
- 회차 #1: 35분 45초 한국어 설교 + Markdown 원문으로 end-to-end 변환 성공.
  파이프라인(전처리 → STT → 후처리 → Export → DB) 자체는 정상.
- 자동 교정 후보가 0건으로 발견됨. 원인 2가지: (1) bible_refs 정규식이 콜론
  표기를 못 잡음(`로마서 3: 21~22`), (2) lexicon wrong_forms 가 사전등록형이라
  실제 STT 자모 변형(이에수/그리시도/보궁 등)에 무력. v1.x 후속 작업 후보.

### Notes
- 코드 변경 없음. 통합 시나리오/문서/검증 도구만 추가. 기존 `pytest`/`ruff` 결과 유지.

## Unreleased - 2026-05-20 (Documentation)

### Added
- `docs/user-guide.md` — 일반 사용자용 한국어 가이드 신규 작성 (설치, `doctor`,
  CLI/GUI 변환, 편집기, 원문 대조, 사용자 사전, 문제 해결, 데이터 저장 위치).
- `docs/known-limitations.md` — v1.0 범위 제외/플랫폼/데이터 정책 SSOT.

### Changed
- `README.md` 를 번들 안내 문서에서 SermonScript 본 프로젝트의 진입점으로 재작성
  (빠른 시작, 주요 기능, 데이터 저장 위치, v1.0 제외 항목, 라이선스/문서 링크).
- `docs/release/release-checklist.md` — Documentation 섹션의 README/사용자 가이드/
  알려진 제한사항 항목을 완료로 표시. 스크린샷 갱신만 남김.

### Notes
- 코드 변경은 없습니다. 기존 `pytest` / `ruff` 결과는 유지됩니다.

## Unreleased - 2026-05-20 (Goal 3)

### Added
- 후처리 파이프라인 (`sermonscript.core.postprocess`):
  - 기본 설교/성경 용어 사전 + 사용자 사전(JSON) 누적 적용.
  - 성경 구절 정규화: `로마서 일장 일절` → `로마서 1장 1절`, `고린도 전서` → `고린도전서`.
  - `clean_text` 채움(라우 텍스트는 절대 변경하지 않음).
- 원문 대조 파이프라인 (`sermonscript.core.reference`):
  - TXT/Markdown 설교 원문에서 제목, 성경 본문, 주요 용어, 고유명사 추출.
  - faster-whisper `initial_prompt` 를 핵심 용어 위주로 짧게 구성 (≤ 280자).
  - STT 세그먼트와 원문 문단을 `rapidfuzz` 기반 유사도 매칭(없을 시 difflib).
  - 성경구절/사용자 사전/고유명사 기반 `CorrectionEngine` — pending 후보로만 저장.
- DB 스키마 v2: `reference_documents`, `alignment_pairs`,
  `correction_suggestions` 테이블 + 기존 DB 자동 마이그레이션.
- `JobRepository.update_segment_text` 로 `clean_text`/`edited_text`/`needs_review`
  단일 패치 (raw_text 는 거부).
- 신뢰도 기반 `needs_review` 플래그: `avg_logprob` 또는 `no_speech_prob` 임계값 초과.
- `transcript_editor` PySide6 위젯:
  - 시작/종료/확인/텍스트 컬럼 + 검색·치환.
  - edited_text 저장(즉시 영속), needs_review 토글, 교정 후보 패널 적용/무시 버튼.
  - Export 우선순위: edited_text > clean_text > raw_text.
- CLI 옵션 `sermonscript transcribe --reference sermon.md --user-dict dict.json`.
- CLI 서브커맨드 `sermonscript corrections list/apply/ignore`.
- Windows 패키징 일체:
  - `sermonscript.spec` (PyInstaller).
  - `scripts/build_windows.ps1` (ruff + pytest + PyInstaller + ZIP).
  - `scripts/make_portable_zip.ps1` → `dist/SermonScript_Portable_{version}.zip`.
  - GitHub Actions `build-windows.yml` (태그 푸시 / 수동 트리거).
- `docs/deferred-youtube-import.md` (v1.0 비포함 정책 SSOT).

### Changed
- `THIRD_PARTY_NOTICES.md` 갱신: PySide6 LGPL, FFmpeg / 모델 / CUDA 미번들 정책.
- `docs/release/release-checklist.md` 갱신: 편집기/교정/PyInstaller/ZIP 항목 추가.
- `transcribe_service` 가 reference + user-dict 를 받아 initial_prompt 와 교정 후보를
  생성하고 DB 에 영속화. 모든 세그먼트는 postprocess 를 거쳐 clean_text 가 채워집니다.

### Notes
- 자동 교정은 보수적으로만 적용합니다. 일반 문장은 자동 교체 대상이 아닙니다.
- 실제 발화가 원문과 다르면 raw_text 가 우선이며, 사용자는 편집기에서 수동으로
  edited_text 를 작성합니다.
- YouTube/온라인 다운로드 기능은 v1.0 범위에서 제외이며 문서화만 유지합니다.

## Unreleased - 2026-05-20

### Added
- SQLite 기반 영속 계층 (`sermonscript.storage`): `jobs`, `segments`, `exports` 테이블과
  `JobRepository` CRUD 헬퍼. DB 경로는 `platformdirs`로 사용자 데이터 디렉터리 아래에 자동 생성.
- `SettingsService`로 기본 언어/모델/전처리 프리셋/출력 폴더/모델 캐시 경로를 JSON에 저장·로드.
- `model_service`에서 지원 STT 모델 목록과 캐시 경로를 노출.
- `transcribe_service.run_transcribe`에 `persist` 옵션 추가: 작업·세그먼트·export를 DB에 기록하고,
  실패 시 `status=failed` + `error_message`를 남깁니다. `raw_text`는 항상 보존됩니다.
- CLI 서브커맨드: `jobs list/show/export`, `settings show/set`, `models list/cache-dir`, `db-path`.
  `transcribe`는 기본적으로 DB에 결과를 기록합니다.
- PySide6 GUI (`python -m sermonscript.app.main`): 파일 추가/드래그 앤 드롭, 작업 큐, 언어·모델·
  프리셋·출력 폴더 설정, 변환 시작, 진행률·로그, 결과 미리보기, 최근 작업 목록.
  변환은 QThread 워커에서 실행되어 UI가 멈추지 않습니다.

### Changed
- `tests/conftest.py`에서 `get_app_paths`를 임시 디렉터리로 패치하여 테스트가 실제
  사용자 DB·설정을 건드리지 않도록 격리.

### Notes
- 스키마는 `schema_meta`에 버전(현재 `1`)을 기록합니다. 사용자 데이터 손실 가능성이
  있는 변경은 별도 마이그레이션 단계로 진행할 예정입니다.
- PySide6는 옵션 의존성입니다. `pip install "sermonscript[gui]"`로 설치하세요.

## Unreleased - 2026-05-19

### Changed
- `/goal` 입력 제한 4000자에 맞춰 Goal 2 프롬프트를 축약했습니다.
- SQLite, 설정, 모델 관리, PySide6 GUI, 작업 큐 구현 범위는 유지하되 중복 설명을 제거했습니다.

### Documentation
- 3-Goal 바이브 코딩 프롬프트 문서를 갱신했습니다.
