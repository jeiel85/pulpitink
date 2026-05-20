# CHANGELOG.md

## [0.4.3] - 2026-05-20

### Added
- **PulpitInk 프리미엄 공식 아이콘 탑재**: 강대상, 깃펜, 잉크 및 소리 파형을 미니멀하게 형상화한 고유의 앱 로고 png 리소스를 생성하고, 다중 규격의 `pulpitink.ico` 파일로 변환하여 `src/pulpitink/resources` 디렉토리에 통합 탑재하였습니다.
- **PyInstaller 아이콘 연동**: `pulpitink.spec` 및 `pulpitink-sidecar.spec` 스펙 파일의 `EXE` 정의부에 고유 아이콘 리소스를 바인딩하여, 윈도우용 실행 파일 패키징 시 아이콘이 엠베딩되도록 지정하였습니다.

### Fixed
- **자모 Fuzzy 매칭 2글자 오탐 스톱워드(Stop-words) 가드 도입**: 한글 자모 Fuzzy 매칭 스캔 과정 중 "에서", "하고", "그리고", "우리", "그의" 등 단순 조사 및 접속사가 임계값을 넘겨 거짓 양성(False Positive)을 유발하는 문제를 방지하기 위해 `DEFAULT_STOP_WORDS` 제외 가드를 설계하여 postprocess 로직의 정확도를 대폭 상향시켰습니다.

## [0.4.2] - 2026-05-20

### Added
- **CI 빌드 및 테스트 자동화 고도화**: GitHub Actions `Test` 워크플로우 실행 시 GUI 테스트에 필수적인 `PySide6` 및 `rapidfuzz`를 포함한 옵셔널 의존성을 일괄 설치하도록 구성 (`test.yml` 수정).

### Fixed
- **PySide6 환경 가드 설계**: 로컬 및 CLI 가상환경 중 PySide6가 누락된 환경에서도 배치 큐 관련 유닛 테스트 수집(collection) 시 크래시가 발생하지 않고, 정상적으로 스킵 처리되도록 임포트 안전장치 탑재 (`tests/test_batch_queue.py` 수정).

## [0.4.1] - 2026-05-20

### Added
- **실험용/임시 디렉터리 무시 설정**: Git 추적 관리를 위해 루트 내 `.antigravitycli/` 및 `frontend/` 디렉터리를 `.gitignore`에 등록 완료.

### Changed
- **알려진 제한사항 문서 최신화**: `docs/known-limitations.md` 문서에서 0.4.0에 기구현된 최근 작업 기록 비활성화, 오디오 싱크 플레이어, 다중 작업 큐 항목을 "구현 완료 (v0.4.0 완비)" 상태로 정비.
- **릴리즈 체크리스트 최신화**: `docs/release/release-checklist.md` 문서에서 0.4.0 및 0.4.1 기능들에 대해 완료 체크리스트 항목을 업데이트 처리.

## [0.4.0] - 2026-05-20

### Added
- **편집기 탭 내 오디오 싱크 플레이어 연동 (Audio Sync Player)**:
  - `TranscriptEditorWidget` 내에 `PySide6.QtMultimedia` 기반 `QMediaPlayer` 및 `QAudioOutput` 객체 탑재.
  - 플레이어 제어 바 UI 추가: 재생/일시정지 버튼, 수평 방향 `QSlider` 진행 바, 재생 시간 표시 레이블, 선택 구간 재생 버튼, 재생 싱크 스크롤 활성화 체크박스.
  - 작업 오디오 소스 자동 매핑: `load_job(job_id)` 호출 시 `cache/jobs/<job_id>/processed.wav` (전처리 캐시) 존재를 최우선 점검하고, 미발견 시 SQLite DB에서 job의 `source_path`를 쿼리하여 원본 미디어 재생 소스로 대체 재생.
  - 세그먼트 테이블 행 더블클릭(`cellDoubleClicked`) 및 "선택 구간 재생" 시 해당 세그먼트의 `start_sec`로 플레이어 seek 및 자동 재생.
  - 플레이어 재생 시간 변화(`positionChanged`) 시 현재 위치에 해당하는 테이블 행을 하이라이트(Select) 처리하며, 스크롤 싱크 옵션이 활성화된 경우 해당 행이 중앙에 오도록 자동 스크롤(`scrollToItem`) 연동.
- **메인 화면 다중 작업 배치 큐 UX 개선 (Batch Queue UX)**:
  - 파일 큐 처리 상태 머신 구현: 대기 목록 내 아이템들에 대기 상태 문자열(`[대기]`, `[진행 중]`, `[완료]`, `[실패]`)을 추가하여 실시간 시각화.
  - 순차 처리 기동 루프(`_start_next_queue_item`): 스레드가 완전히 해제된 시점(`_on_thread_finished`)에 다음 파일의 변환을 기동시켜 리소스 경합 방지.
  - 연속성 정책 반영: 다중 파일 변환 도중 특정 개별 파일 변환이 실패하더라도 전체 배치 처리를 멈추지 않고, 해당 행만 `[실패]` 표기 후 다음 작업을 연쇄 변환.
  - 변환 중단(Cancel) 기능: 진행 중 "변환 중단" 버튼 클릭 시 확인 다이얼로그를 통해 대기 중인 모든 큐를 일괄 파기하고 워커 스레드를 정지(`terminate()`).
  - 변환 진행 중 파일 추가/제거/비우기 동작 시도에 대한 안전 가드 팝업 경고 추가.

### Tests
- `tests/test_batch_queue.py`를 신규 추가하여, 다중 파일 배치 큐 가동, 순차 변환, 실패 시의 연속성 기동, 변환 중환 및 큐 일괄 파기 등 상태 머신 시뮬레이션 테스트 3건 작성 완료.
- `python -m pytest`: 100/100 PASS (총 100개 테스트)
- `python -m ruff check .`: PASS

### Feature: Delete UX & Privacy Control & Doc Alignment

### Added
- **작업/캐시 삭제 기능 보강 (Delete UX)**:
  - CLI `jobs delete <job_id>` 명령어 추가: 지정된 작업 ID의 DB 데이터와 캐시 오디오 디렉터리(`cache/jobs/<job_id>`)를 재확인 절차를 거쳐 영구 연쇄 삭제합니다.
  - CLI `jobs clean-cache` 명령어 추가: DB 내 활성 작업 목록과 대조하여 등록되지 않은 방치 캐시 디렉터리(고스트 캐시)만 안전하게 일괄 정리합니다.
  - GUI 최근 작업 목록(`recent_list`)에 우클릭 컨텍스트 메뉴 및 "작업 및 캐시 삭제" 액션 추가: `QMessageBox` 대화상자로 안전하게 재확인 후 DB 레코드와 물리 캐시를 연쇄 삭제 처리하고 목록을 자동 갱신합니다.
- **최근 작업 기록 저장 비활성화 옵션 (Privacy Control)**:
  - `Settings` 데이터클래스에 `keep_history` (기본값: True) 필드를 탑재하고 JSON 설정 파일 연동 및 형변환 가드 처리를 추가했습니다.
  - STT 변환 시(`run_transcribe`), `keep_history`가 False이면 `persist` 매개변수를 강제 비활성화하여 DB 영속화 저장을 전면 우회하도록 처리했습니다.
  - GUI 설정 그룹에 "최근 작업 기록 저장 및 표시" 체크박스 위젯을 추가하여 즉시 저장 및 리프레시되도록 했습니다. 기능 비활성화 시 목록에 고지 문구 노출 및 컨텍스트 메뉴 진입을 차단합니다.

### Changed
- **Jamo Fuzzy 매칭 문서 상태 갱신 (Doc Alignment)**:
  - `docs/design/jamo-fuzzy-matching.md` 설계 노트의 상태를 `구현 완료 (v1.0 완비)`로 변경하고 6절에 2글자 단어 한계와 임계값 0.75~0.80 상향 조정 가이드를 보완했습니다.

### Tests
- `tests/test_settings_service.py`에 `keep_history` 형변환 및 역직렬화 단위 테스트 추가.
- `tests/test_transcribe_persistence.py`에 `keep_history`가 False일 때 DB 트랜잭션 및 영속화를 생략하는지에 대한 Mocking 기반 통합 테스트 추가.
- `python -m pytest`: 97/97 PASS
- `python -m ruff check .`: PASS

### Branding: 설교필기 PulpitInk 전체 리네이밍

### Changed
- 프로젝트 전체 브랜딩을 **SermonScript**에서 **설교필기 (PulpitInk)** 로 변경했습니다.
- Python 패키지명: `sermonscript` → `pulpitink`, CLI 명령: `pulpitink`
- GUI 타이틀바: `설교필기 (PulpitInk)`, QMessageBox 다이얼로그: `설교필기`
- 클래스: `SermonScriptError` → `PulpitInkError`
- PyInstaller spec: `pulpitink.spec`, `pulpitink-sidecar.spec`
- 빌드 산출물: `PulpitInk_Portable_*.zip`, EXE: `PulpitInk.exe`
- GitHub 저장소: `jeiel85/sermon-script` → `jeiel85/pulpitink`
- 데이터 경로: `%LOCALAPPDATA%\PulpitInk\PulpitInk\`
- DB/로그: `pulpitink.db`, `pulpitink.log`
- 환경변수: `PULPITINK_ROOT`

### Tests
- `ruff check .`: All checks passed
- `pytest`: 95/95 passed

### Documentation: README repository guide

### Changed
- GitHub Pages 랜딩 페이지가 별도로 생긴 뒤 README를 저장소 안내 문서 역할에 맞게 재정비했습니다.
- 상단 대형 랜딩 이미지를 제거하고 설치, 사용, 데이터 저장 위치, 개발 검증, 프로젝트 구조 중심으로 구성했습니다.

### Documentation: GitHub Pages landing

### Added
- GitHub Pages용 정적 랜딩 페이지 `docs/index.html`을 추가했습니다.
- GitHub Pages에서 정적 파일을 그대로 제공하도록 `docs/.nojekyll`을 추가했습니다.

### Changed
- README와 프로젝트 홈페이지 URL을 `https://jeiel85.github.io/pulpitink/` 기준으로 갱신했습니다.

### Documentation: GitHub landing page

### Changed
- `README.md`를 GitHub 랜딩 페이지 역할에 맞게 갱신했습니다.
  사용자가 제공한 랜딩 이미지를 상단에 배치하고, 현재 구현된 GUI/CLI/STT/편집/Export/배포 상태를 기준으로 빠른 시작과 기능표를 정리했습니다.
- 프로젝트 메타데이터의 GitHub URL을 실제 저장소인 `https://github.com/jeiel85/pulpitink`로 정정했습니다.

### Added
- `docs/assets/pulpitink-landing.png` 랜딩 이미지를 추가했습니다.

## [0.3.0] - 2026-05-20

### Added
- GitHub 태그(`v*`) push 시 Windows Portable ZIP을 빌드한 뒤 GitHub Release를 자동 생성하도록
  `build-windows.yml`을 정비했습니다.
- 릴리즈 산출물과 함께 `SHA256SUMS.txt`를 생성해 GitHub Release에 첨부합니다.

### Changed
- 참고 프로젝트(`claude-usage-tray-windows`)와 동일하게 태그를 릴리즈 트리거로 삼고,
  릴리즈 본문은 `CHANGELOG.md`의 해당 버전 섹션에서 추출합니다.
- 태그 버전과 `pyproject.toml` 버전이 다르면 릴리즈 빌드를 중단하도록 검증 단계를 추가했습니다.

### Tests
- 워크플로우 변경은 GitHub Actions 태그 push에서 검증됩니다.

### Release validation

### Fixed
- GitHub Actions `build-windows.yml` 수동 실행에서 `pulpitink.spec`가 저장소에 포함되지 않아
  PyInstaller 단계가 `Spec file "pulpitink.spec" not found!`로 실패하던 문제를 수정했습니다.
  `.gitignore`의 일반 `*.spec` 제외는 유지하되 루트 `pulpitink.spec`만 추적 대상으로 허용했습니다.

### Changed
- `ruff check .`가 로컬 실험/번들 산출물인 untracked `frontend/` 디렉터리를 스캔하지 않도록 Ruff 제외 목록에 `frontend`를 추가했습니다.
- 한국어 Jamo fuzzy 유틸이 `rapidfuzz` 미설치 환경에서도 표준 라이브러리 `difflib` fallback으로 동작하도록 보완했습니다.
- `tests/integration/verify_fuzzy.py`의 import 정렬과 공백을 Ruff 기준에 맞게 정리했습니다.
- `docs/release/release-checklist.md`에 2026-05-20 로컬 품질 검사 및 Windows Portable ZIP 생성 결과를 반영했습니다.

### Tests
- `python -m ruff check .`: PASS
- `python -m pytest`: 91/91 PASS
- `python -m pulpitink.cli.main doctor`: PASS
- `./scripts/build_windows.ps1 -SkipChecks`: PASS, `dist/PulpitInk_Portable_0.3.0.zip` 생성 확인.

### Feature: Korean Jamo-based Fuzzy Matching

### Added
- **한국어 자모(Jamo) Fuzzy 매칭 구현** (`src/pulpitink/core/postprocess/jamo.py`):
  - 한글 유니코드 NFD 자모 분해(`jamo_seq`) 및 초성 추출(`choseong`) 헬퍼 구현.
  - 자모 매칭 비율(60%) 및 초성 매칭 비율(40%)을 결합한 **Hybrid 유사도 Scorer** 탑재.
  - 슬라이딩 윈도우 스캔 및 Double-pass Jamo ratio 검사(>= 50%)를 통한 거짓 양성(False Positive) 방지 및 최소 음절 길이 3 미만 게이트 적용.
- **CorrectionEngine 연동** (`src/pulpitink/core/reference/corrections.py`):
  - `CorrectionEngine` 파라미터로 `fuzzy_matching_enabled`와 `fuzzy_threshold` 추가.
  - `suggestions_for`에서 고유명사 및 lexicon 단어들을 대상으로 Fuzzy 매치 수행 후 `reference+fuzzy:<score>` 소스의 `proper_noun` 제안 생성.
- **설정 및 영속화 확장**:
  - `Settings` 데이터클래스에 `fuzzy_matching_enabled`와 `fuzzy_threshold` 기본값(True, 0.70) 적용.
  - `SettingsService` 및 `TranscribeRequest` 필드 연동 완료.
- **CLI/GUI 제어 패널**:
  - `pulpitink transcribe` CLI 인자 `--fuzzy/--no-fuzzy` 및 `--fuzzy-threshold` 추가.
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

### Hotfix: bible_refs colon notation

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

### Integration regression #1

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

### Documentation

### Added
- `docs/user-guide.md` — 일반 사용자용 한국어 가이드 신규 작성 (설치, `doctor`,
  CLI/GUI 변환, 편집기, 원문 대조, 사용자 사전, 문제 해결, 데이터 저장 위치).
- `docs/known-limitations.md` — v1.0 범위 제외/플랫폼/데이터 정책 SSOT.

### Changed
- `README.md` 를 번들 안내 문서에서 PulpitInk 본 프로젝트의 진입점으로 재작성
  (빠른 시작, 주요 기능, 데이터 저장 위치, v1.0 제외 항목, 라이선스/문서 링크).
- `docs/release/release-checklist.md` — Documentation 섹션의 README/사용자 가이드/
  알려진 제한사항 항목을 완료로 표시. 스크린샷 갱신만 남김.

### Notes
- 코드 변경은 없습니다. 기존 `pytest` / `ruff` 결과는 유지됩니다.

## Unreleased - 2026-05-20 (Goal 3)

### Added
- 후처리 파이프라인 (`pulpitink.core.postprocess`):
  - 기본 설교/성경 용어 사전 + 사용자 사전(JSON) 누적 적용.
  - 성경 구절 정규화: `로마서 일장 일절` → `로마서 1장 1절`, `고린도 전서` → `고린도전서`.
  - `clean_text` 채움(라우 텍스트는 절대 변경하지 않음).
- 원문 대조 파이프라인 (`pulpitink.core.reference`):
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
- CLI 옵션 `pulpitink transcribe --reference sermon.md --user-dict dict.json`.
- CLI 서브커맨드 `pulpitink corrections list/apply/ignore`.
- Windows 패키징 일체:
  - `pulpitink.spec` (PyInstaller).
  - `scripts/build_windows.ps1` (ruff + pytest + PyInstaller + ZIP).
  - `scripts/make_portable_zip.ps1` → `dist/PulpitInk_Portable_{version}.zip`.
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
- SQLite 기반 영속 계층 (`pulpitink.storage`): `jobs`, `segments`, `exports` 테이블과
  `JobRepository` CRUD 헬퍼. DB 경로는 `platformdirs`로 사용자 데이터 디렉터리 아래에 자동 생성.
- `SettingsService`로 기본 언어/모델/전처리 프리셋/출력 폴더/모델 캐시 경로를 JSON에 저장·로드.
- `model_service`에서 지원 STT 모델 목록과 캐시 경로를 노출.
- `transcribe_service.run_transcribe`에 `persist` 옵션 추가: 작업·세그먼트·export를 DB에 기록하고,
  실패 시 `status=failed` + `error_message`를 남깁니다. `raw_text`는 항상 보존됩니다.
- CLI 서브커맨드: `jobs list/show/export`, `settings show/set`, `models list/cache-dir`, `db-path`.
  `transcribe`는 기본적으로 DB에 결과를 기록합니다.
- PySide6 GUI (`python -m pulpitink.app.main`): 파일 추가/드래그 앤 드롭, 작업 큐, 언어·모델·
  프리셋·출력 폴더 설정, 변환 시작, 진행률·로그, 결과 미리보기, 최근 작업 목록.
  변환은 QThread 워커에서 실행되어 UI가 멈추지 않습니다.

### Changed
- `tests/conftest.py`에서 `get_app_paths`를 임시 디렉터리로 패치하여 테스트가 실제
  사용자 DB·설정을 건드리지 않도록 격리.

### Notes
- 스키마는 `schema_meta`에 버전(현재 `1`)을 기록합니다. 사용자 데이터 손실 가능성이
  있는 변경은 별도 마이그레이션 단계로 진행할 예정입니다.
- PySide6는 옵션 의존성입니다. `pip install "pulpitink[gui]"`로 설치하세요.

## Unreleased - 2026-05-19

### Changed
- `/goal` 입력 제한 4000자에 맞춰 Goal 2 프롬프트를 축약했습니다.
- SQLite, 설정, 모델 관리, PySide6 GUI, 작업 큐 구현 범위는 유지하되 중복 설명을 제거했습니다.

### Documentation
- 3-Goal 바이브 코딩 프롬프트 문서를 갱신했습니다.
