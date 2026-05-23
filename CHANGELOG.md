# CHANGELOG.md

## Unreleased - 2026-05-23

### Changed
- GitHub 저장소 URL을 `jeiel85/pulpit-ink-desktop` 기준으로 갱신했습니다.
- README 배지, 릴리즈/이슈/Pages 링크, 소스 설치 안내, Inno Setup URL, 앱 업데이트 확인용 GitHub Releases API URL을 새 저장소로 전환했습니다.

## [0.5.0] - 2026-05-23

### Added — Tauri 하이브리드 UI 기능 parity 2차 포팅
- **네이티브 파일/폴더 다이얼로그**: `tauri-plugin-dialog` 도입. 오디오/원문/사용자 사전/모델 캐시 경로 입력을 절대경로 직접 입력 대신 OS 네이티브 다이얼로그로 선택할 수 있는 `PathPicker` 컴포넌트 신설.
- **Wavesurfer.js 기반 2단 대조 편집기**: `wavesurfer.js`를 React 편집기 상단에 도킹하여 오디오 파형을 실시간 렌더링. 타임스탬프 클릭/더블클릭으로 해당 구간 이동/구간 재생, Tauri `convertFileSrc` + asset 프로토콜로 로컬 미디어 스트리밍. 세그먼트별 Fuzzy 교정 후보를 팝오버 형태로 노출하고 클릭 한 번에 `edited_text`에 반영 및 SQLite에 영속화.
- **배치 큐 UI**: 새 STT 변환 시 큐에 누적되고 순차적으로 사이드카에 위임. 개별 항목 진행률·상태 표시, 실패 시에도 다음 항목 계속 진행, 완료/실패 일괄 정리 버튼 제공.
- **YouTube opt-in 동의 모달**: 저작권 고지 + 동의 체크박스 + URL 검증 + yt-dlp 진단/원클릭 자동 설치를 묶은 모달. 동의 후 큐에 추가하고 사이드카 `transcribe`가 URL을 처리.
- **Glossary(사용자 용어 사전) 탭**: 사전 항목 추가/수정/삭제/검색 + CSV import/export. 사이드카 `user-dict` 서브명령으로 위임하며 기본 위치는 `%LOCALAPPDATA%/PulpitInk/user_dict.json`.
- **업데이트 알림 배너**: 앱 부팅 시 사이드카 `update-check --json`을 호출해 GitHub Releases 최신 버전을 확인하고, 신규 버전 존재 시 상단 배너로 표시. 사용자 dismiss는 버전 단위로 `localStorage`에 기록.

### Added — 사이드카 IPC 보강
- `pulpit-ink user-dict list/add/remove/import/export/path [--json]` — 사용자 사전 CRUD 및 CSV 입출력.
- `pulpit-ink update-check [--force] [--json]` — 24시간 캐시 적용된 GitHub Releases 비교.
- `pulpit-ink youtube check/install [--json]` — yt-dlp 설치 여부 진단 및 pip 자동 설치.
- `pulpit-ink segments update <id> [--edited-text/--clean-text/--speaker] [--json]` — React 편집기가 호출하는 세그먼트 영속화 엔드포인트.

### Changed
- `frontend/package.json` / `Cargo.toml` / `tauri.conf.json` / `pyproject.toml` / `src/pulpit_ink/__init__.py` 버전을 `0.5.0`으로 일제히 범프.
- Tauri 윈도우 기본 크기를 1180×760 → 1280×820으로 확장 (편집기 + 파형 도킹용 여유 확보).
- `tauri.conf.json`의 `security.assetProtocol.enable = true`로 로컬 미디어 스트리밍 활성화.

### Tests
- `tests/test_cli_tauri_helpers.py` 신규 8건: user-dict CRUD/CSV 라운드트립, update-check JSON, youtube check/install JSON 게이트 검증.
- 전체 회귀: pytest 144/144 PASS, ruff 0건.

## [0.4.7-tauri.1] - 2026-05-21 (사전 단계)

### Tauri
- `feat/tauri-hybrid` 브랜치를 현재 `main` 기능 위로 병합하여 PulpitInk Python 코어와 React/Tauri 셸을 다시 연결.
- Tauri 사이드카 명칭과 앱 메타데이터를 `PulpitInk` / `pulpit-ink-sidecar` / `com.jeiel85.pulpitink` 기준으로 정리.
- Tauri UI에 첫 실행 온보딩 패널, 라이트/다크 테마 전환, 더 큰 기본 버튼 크기, PulpitInk 브랜딩 반영.
- Tauri IPC에서 작업 목록과 설정을 안정적으로 읽을 수 있도록 `jobs list --json`, `jobs show --json`, `settings show --json` 출력 추가.

### CI
- GitHub Actions의 Node.js 20 deprecation 경고에 대응하기 위해 워크플로우 전역에 `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24=true` 설정.
- `windows-latest` 리디렉션 공지에 대응해 `Test` 및 `Build Windows Portable` 워크플로우 runner를 `windows-2025-vs2026`으로 명시 고정.
- 공식 Actions를 Node 24 기반 최신 stable(`checkout@v6`, `setup-python@v6.2.0`, `upload-artifact@v7`, `download-artifact@v8`)로 업데이트.

## [0.4.7] - 2026-05-21

### Added
- **프로 검수 단축키 시스템 구현 (QShortcut 기반)**:
  - `Ctrl+Space`: 오디오 재생/일시정지 토글 기능 바인딩. 한글/영어 타이핑 텍스트 입력과 충돌을 방지하기 위한 안전 조합 키 적용.
  - `Ctrl+←` / `Ctrl+→`: 테이블의 이전/다음 세그먼트(행)로 즉각 행 포커스를 이동하고, 오디오 싱크 플레이어도 해당 세그먼트의 시작 시각으로 즉시 seek 및 자동 재생 처리.
  - `Ctrl+P`: 현재 활성화된 세그먼트(행)의 오디오 구간만을 정밀 반복 재생.
  - `Ctrl+↑` / `Ctrl+↓`: 재생 속도를 0.5배속에서 2.0배속 범위(0.1배속 단위)로 동적으로 제어.
  - **속도 배지 UI 피드백**: 재생 속도 조절 시 플레이어 조작부 옆에 배지(Badge) 스타일로 현재 속도 값을 직관적으로 시각화.
- **Markdown 실시간 HTML 리치 뷰어 도킹**:
  - 편집 테이블 하단에 텍스트 편집 영역과 함께 병렬로 작동하는 `QTextBrowser` 기반 실시간 리치 뷰어 구성.
  - 별도 무거운 외부 파서 라이브러리 없이 Windows SmartScreen 백신 오탐을 차단하고 바이너리 용량을 가볍게 유지하기 위해, 순수 Python 정규식 헬퍼(`_markdown_to_html`)로 HTML 변환 파이프라인(Bold, Italic, Strikethrough, Inline Code, 개행 및 이스케이프) 구축.
  - 세그먼트 테이블 행 포커스 변경(`itemSelectionChanged`) 및 사용자의 텍스트 수정(`itemChanged`) 즉시 실시간 Markdown 파서가 뷰어 내용을 동조/갱신하도록 신호-슬롯(Signal-Slot) 연결.
  - 하단부에 검수 단축키 목록과 속도 단축키 정보를 안내하는 미니 가이드 범례 표시줄 탑재.

### Documentation
- **차기 에이전트 세션용 기술 이관 로드맵 수립**:
  - `docs/roadmap-tasks.md` 및 `docs/decision-log.md` 문서 내에 v0.4.7 마일스톤 작업을 전원 완료로 업데이트.
  - GitHub Issue #1 `"실시간 마이크 녹음 및 실시간 오프라인 Whisper 스트리밍 STT 연동"`에 대비하여, 차기 에이전트 세션이 그대로 이관받아 즉각 개발을 시작할 수 있도록 아주 정밀하고 완벽한 오프라인 아키텍처 가이드라인(sounddevice/PyAudio 하드웨어 드라이버 격리, PCM 링 버퍼 스레드 큐, Whisper 비동기 스트리밍 디코딩 및 10초 주기 원자적 플러시 세이브 세이프 가드) 설계 이관 가이드를 수립.

### Tests
- `tests/test_editor_hotkeys.py` 신규 추가: `Ctrl+Space` 재생/일시정지 토글, `Ctrl+Up/Down` 재생 배속 상/하한선 예외 가드 제어, `Ctrl+Left/Right` 행 경계 예외 가드 및 순환 제어를 철저히 검증하는 단위 테스트 3건 작성 완료.
- `pytest` 전체 회귀 테스트 스위트 100% 통과 완료 (**136/136 PASS**).
- `ruff check .` 정적 린트 경고 **0건 (Perfect Clean)** 달성.

## [0.4.6] - 2026-05-21

### Added
- **Word (.docx) 3대 맞춤형 템플릿 내보내기 엔진**:
  - `python-docx` 라이브러리를 연동하여, 사용자의 목적에 맞게 Word 문서 레이아웃을 생성하는 내보내기 엔진(`DocxExporter`)을 구축하였습니다.
  - **강대인쇄용**: 14pt 바탕체, 1.8 줄간격, 넉넉한 여백 설계 및 가독성 극대화.
  - **주보배포용**: 10.5pt 돋움체, 1.3 줄간격, 화자명 볼드 및 소형 타임스탬프(`[00:01:23]`) 삽입.
  - **표 검수용**: 동적 테이블 컴포넌트, 감청색(Dark Navy) 헤더 스타일 및 격자 회색 그리드 외곽선 구성.
  - **성경 구절 하이라이트 박스**: DB에서 파싱된 대조 성경 구절(`bible_refs`)이 있을 경우, 문서 최상단에 미색 배경 음영 및 좌측 3pt Dark-Navy 굵은 테두리(Blockquote style)가 들어간 특별 하이라이트 박스 단락을 자동 생성합니다.
- **사용자 맞춤 Glossary 사전 GUI 탭 및 백엔드 지능형 자동 연동**:
  - **용어 사전 탭 신설 (`GlossaryTab`)**: PySide6 기반 네 번째 탭을 추가하여 `[올바른 어휘 (Canonical)]` | `[오인식 발음 패턴들 (Wrong Spellings)]` 카드 테이블 목록 편집기를 제공합니다.
  - **디스크 세이브 및 예외 백업 복구 엔진**: `save_user_lexicon`을 백엔드에 설계하여, 저장 실패 시 복구용 `.bak` 파일을 구성하고 데이터 유실을 완벽히 방지합니다.
  - **지능형 자동 사전 바인딩**: `transcribe_service.py` 내부 `_build_lexicon`을 정밀화하여 사용자가 CLI/GUI 상에서 사전 경로를 입력하지 않더라도 데이터 폴더 내 `user_dict.json`이 감지되면 자동으로 1차 STT 정제에 녹여내도록 구현했습니다.
  - **CSV 일괄 가져오기/내보내기**: 엑셀에서 바로 편집할 수 있도록 헤더 없는 표준 CSV 어휘 목록 파일 가져오기 및 내보내기 팝업 UI를 완비했습니다.
- **GitHub API 연동 실시간 자동/수동 업데이트 알리미 (Update Checker)**:
  - **무의존성 설계**: 무거운 외부 라이브러리(`requests` 등) 대신 순수 파이썬 표준 라이브러리 `urllib.request` 및 `json`을 활용하여 빌드 용량과 SmartScreen 백신 오탐 리스크를 원천 배제하였습니다.
  - **24시간 로컬 캐싱 체계**: IP당 시간당 60회로 제약되는 GitHub API Rate Limit 도달 및 앱 기동 딜레이를 방지하기 위해, `update_cache.json`을 통해 마지막 검사 후 24시간 동안은 API 요청을 생략하는 로컬 캐싱 엔진을 구축하였습니다.
  - **수동 업데이트 확인**: 도움말 메뉴를 통해 사용자가 직접 수동 검사를 요청할 때에는 24시간 캐시 제한을 바이패스(force=True)하고 실시간으로 GitHub API를 강제 조회하도록 설계하였습니다.
  - **HTTP User-Agent 헤더 필수 주입** 및 5초 타임아웃 지정을 통해 보안 및 네트워크 단절 시 GUI 멈춤을 완벽하게 방지하였습니다.
  - **Semantic Versioning Parser**: 접두사 v 제거 및 튜플 정수 파싱을 기반으로 한 정밀 버전 크기 비교 알고리즘 구현.
  - **예외 처리 및 무소음 폴백 (Silent Fallback)**: 자동 백그라운드 검사 중 통신 실패/장애 발생 시 팝업 창을 띄우지 않고 로그만 남기는 설계 준수.
- **모던 프리미엄 GUI 업데이트 알림 위젯 및 메뉴 연동**:
  - `MainWindow` 상단 툴바 아래 영역에 세련되고 아름다운 그라데이션(`qlineargradient` 딥 블루)이 가미된 `UpdateBannerWidget` 탑재.
  - 마우스 호버 효과를 지닌 [다운로드] 플랫 버튼(클릭 시 시스템 브라우저 연동) 및 [✕] 닫기 버튼(클릭 시 위젯 hide 및 레이아웃 유연 축소) 구현.
  - 도움말(`Help`) 메뉴바 추가 및 하단에 `"업데이트 확인... (Check for Updates...)"` 메뉴 액션 신규 배치.
  - 수동 업데이트 확인 시 `QMessageBox` 모달 안내 팝업을 연계하여, 사용자 상태별 명시적 피드백(신버전 발견/이미 최신/통신 오류)을 완벽 제공하도록 구축하였습니다.

### Documentation
- 현재 구현 상태에 맞춰 YouTube URL 입력을 “저작권/이용 권한 고지 동의 기반 opt-in 기능”으로 문서화하고, 일반 온라인 다운로드·클라우드·우회성 다운로드는 v1.0 제외 범위로 명확히 구분했습니다.
- Heuristic 화자 분리와 편집기 화자 열이 구현 완료 상태임을 README, 제품 명세, 사용자 가이드, 릴리즈 체크리스트에 반영했습니다.
- 현재 Windows 11 PC에서 캡처한 GUI 메인 화면 및 편집기 스크린샷을 `docs/assets/`에 추가했습니다.

### Tests
- `tests/test_docx_exporter.py`를 신규 추가하여 3대 템플릿 스타일 및 성경 구절 하이라이트 박스 단락 생성을 검증하는 단위 테스트 4건 작성 완료.
- `tests/test_update_checker.py`를 신규 추가하여 신버전 발견, 동일/하위 버전, 예외 무소음 폴백, 캐시 유지, 캐시 만료 갱신, 수동 강제 API 요청을 검증하는 핵심 단위 테스트 8건 작성 완료.
- `tests/test_glossary_service.py`를 신규 추가하여 JSON 단어장 안전 디스크 쓰기, Lexicon 병합 및 STT 텍스트 정제 치환, transcribe 기본 경로 자동 바인딩을 검증하는 단위 테스트 4건 작성 완료.
- `pytest` 전체 회귀 테스트 통과 완료: **133/133 PASS** (100% 성공).
- `ruff check .`: PASS

## [0.4.5] - 2026-05-20

### Added
- **yt-dlp 자동 진단/원클릭 설치 UI**: YouTube 저작권 Disclaimer 다이얼로그에 `yt-dlp` 라이브러리 설치 상태를 자동 진단하는 상태 라벨과 백그라운드 워커 스레드(`YtdlpInstallWorker`) 기반의 원클릭 자동 설치 버튼을 추가하여, 사용자가 터미널 명령 없이 GUI에서 직접 `pip install yt-dlp`를 안전하게 실행할 수 있도록 통합하였습니다. 설치 진행 중에도 UI가 프리즈되지 않습니다.
- **1시간 오디오 스트레스 테스트 및 실측 성능 프로파일 보고서**: `scripts/stress_test.py`로 3600초 무음 WAV를 합성하여 전체 STT 파이프라인을 구동하고 `psutil`로 CPU/RSS를 샘플링한 뒤 `docs/performance-profile.md`로 결과를 자동 출력합니다. tiny 모델 기준 실측 결과는 14.07x 실시간, 평균 CPU 11.84%, 피크 RSS 1014.32 MB입니다.
- **Inno Setup 기반 Windows 인스톨러 빌드 스크립트**: `scripts/pulpit-ink.iss`(다국어 한국어/영어, 데스크탑 아이콘 옵션, 64bit Program Files 설치)와 `scripts/create_installer.ps1`(pyproject.toml 버전 자동 감지 후 ISCC.exe 호출, 미설치 시 다운로드 안내)을 추가하여 Portable ZIP 외에 정식 설치 관리자(.exe) 산출물을 생성할 수 있게 되었습니다. 단, 코드 서명은 미적용입니다.

### Tests
- `tests/test_youtube.py`에 `install_yt_dlp` 성공/실패 및 `is_yt_dlp_available` 진단 경로 단위 테스트 4건 추가.
- `tests/test_i18n.py`에 yt-dlp 자동 설치 흐름용 신규 ko↔en 번역 키 회귀 테스트 1건 추가.
- `python -m pytest`: 115/115 PASS
- `python -m ruff check .`: PASS

## [0.4.4] - 2026-05-20

### Added
- **Heuristic 화자 분리(Diarization) 파이프라인 구현**: 무음구간 갭(gap > 1.5s) 기반 `HeuristicDiarizer`를 구현하고, CLI `--diarize` 옵션 및 GUI 변환 설정 체크박스를 연동하여 STT 변환 시 자동으로 화자 태그("화자 1", "화자 2")가 분리되어 할당되도록 구축하였습니다.
- **GUI 편집기 화자 열 연동 및 영속성 저장**: `TranscriptEditorWidget`에 "화자" 편집 열(Column)을 추가하여 사용자가 테이블에서 직접 화자를 수정할 수 있게 하고, 수정 시 즉시 SQLite DB의 `segments` 테이블 내 `speaker` 컬럼에 실시간으로 영속화되도록 연동하였습니다.
- **경량 i18n 번역 프레임워크 구축**: `src/pulpit_ink/core/utils/i18n.py`에 경량 영한 번역 Dictionary 및 실시간 UI retranslate 기능을 구현하여, GUI "인터페이스 언어" 변경 시 실시간으로 영한 UI 언어가 매끄럽게 토글되도록 구축하였습니다.
- **YouTube URL 비동기 다운로드 및 저작권 Disclaimer UI**: `yt-dlp` 기반의 비동기 오디오 다운로드 파이프라인을 구축하고, GUI 메인 화면에 "YouTube 주소 추가" 버튼 및 저작권 Disclaimer 동의 팝업 창을 추가하여, 동의 후 URL 입력 시 백그라운드 워커 스레드에서 무정지 비동기 다운로드 및 STT 변환이 순차 진행되도록 연동하였습니다.

### Tests
- `tests/test_diarizer.py`를 신규 추가하여 무음구간 기반 화자 전환 및 예외/빈 입력 처리를 검증하는 단위 테스트 3건 작성 완료.
- `tests/test_youtube.py`를 신규 추가하여 `yt-dlp` 라이브러리 존재 여부별 안전 폴백 및 Mock 기반 비동기 오디오 다운로드 정확도를 검증하는 단위 테스트 2건 작성 완료.
- `tests/test_i18n.py`를 신규 추가하여 전역 언어 설정 전환 및 번역/폴백 매핑 정확도를 검증하는 단위 테스트 4건 작성 완료.
- `python -m pytest`: 110/110 PASS (총 110개 테스트 완료)
- `python -m ruff check .`: PASS

## [0.4.3] - 2026-05-20

### Added
- **PulpitInk 프리미엄 공식 아이콘 탑재**: 강대상, 깃펜, 잉크 및 소리 파형을 미니멀하게 형상화한 고유의 앱 로고 png 리소스를 생성하고, 다중 규격의 `pulpit-ink.ico` 파일로 변환하여 `src/pulpit_ink/resources` 디렉토리에 통합 탑재하였습니다.
- **PyInstaller 아이콘 연동**: `pulpit-ink.spec` 및 `pulpit-ink-sidecar.spec` 스펙 파일의 `EXE` 정의부에 고유 아이콘 리소스를 바인딩하여, 윈도우용 실행 파일 패키징 시 아이콘이 엠베딩되도록 지정하였습니다.

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
- Python 패키지명: `sermonscript` → `pulpit-ink`, CLI 명령: `pulpit-ink`
- GUI 타이틀바: `설교필기 (PulpitInk)`, QMessageBox 다이얼로그: `설교필기`
- 클래스: `SermonScriptError` → `PulpitInkError`
- PyInstaller spec: `pulpit-ink.spec`, `pulpit-ink-sidecar.spec`
- 빌드 산출물: `PulpitInk_Portable_*.zip`, EXE: `PulpitInk.exe`
- GitHub 저장소: `jeiel85/sermon-script` → `jeiel85/pulpit-ink-desktop`
- 데이터 경로: `%LOCALAPPDATA%\PulpitInk\PulpitInk\`
- DB/로그: `pulpit_ink.db`, `pulpit_ink.log`
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
- README와 프로젝트 홈페이지 URL을 `https://jeiel85.github.io/pulpit-ink-desktop/` 기준으로 갱신했습니다.

### Documentation: GitHub landing page

### Changed
- `README.md`를 GitHub 랜딩 페이지 역할에 맞게 갱신했습니다.
  사용자가 제공한 랜딩 이미지를 상단에 배치하고, 현재 구현된 GUI/CLI/STT/편집/Export/배포 상태를 기준으로 빠른 시작과 기능표를 정리했습니다.
- 프로젝트 메타데이터의 GitHub URL을 실제 저장소인 `https://github.com/jeiel85/pulpit-ink-desktop`로 정정했습니다.

### Added
- `docs/assets/pulpit-ink-landing.png` 랜딩 이미지를 추가했습니다.

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
- GitHub Actions `build-windows.yml` 수동 실행에서 `pulpit-ink.spec`가 저장소에 포함되지 않아
  PyInstaller 단계가 `Spec file "pulpit-ink.spec" not found!`로 실패하던 문제를 수정했습니다.
  `.gitignore`의 일반 `*.spec` 제외는 유지하되 루트 `pulpit-ink.spec`만 추적 대상으로 허용했습니다.

### Changed
- `ruff check .`가 로컬 실험/번들 산출물인 untracked `frontend/` 디렉터리를 스캔하지 않도록 Ruff 제외 목록에 `frontend`를 추가했습니다.
- 한국어 Jamo fuzzy 유틸이 `rapidfuzz` 미설치 환경에서도 표준 라이브러리 `difflib` fallback으로 동작하도록 보완했습니다.
- `tests/integration/verify_fuzzy.py`의 import 정렬과 공백을 Ruff 기준에 맞게 정리했습니다.
- `docs/release/release-checklist.md`에 2026-05-20 로컬 품질 검사 및 Windows Portable ZIP 생성 결과를 반영했습니다.

### Tests
- `python -m ruff check .`: PASS
- `python -m pytest`: 91/91 PASS
- `python -m pulpit_ink.cli.main doctor`: PASS
- `./scripts/build_windows.ps1 -SkipChecks`: PASS, `dist/PulpitInk_Portable_0.3.0.zip` 생성 확인.

### Feature: Korean Jamo-based Fuzzy Matching

### Added
- **한국어 자모(Jamo) Fuzzy 매칭 구현** (`src/pulpit_ink/core/postprocess/jamo.py`):
  - 한글 유니코드 NFD 자모 분해(`jamo_seq`) 및 초성 추출(`choseong`) 헬퍼 구현.
  - 자모 매칭 비율(60%) 및 초성 매칭 비율(40%)을 결합한 **Hybrid 유사도 Scorer** 탑재.
  - 슬라이딩 윈도우 스캔 및 Double-pass Jamo ratio 검사(>= 50%)를 통한 거짓 양성(False Positive) 방지 및 최소 음절 길이 3 미만 게이트 적용.
- **CorrectionEngine 연동** (`src/pulpit_ink/core/reference/corrections.py`):
  - `CorrectionEngine` 파라미터로 `fuzzy_matching_enabled`와 `fuzzy_threshold` 추가.
  - `suggestions_for`에서 고유명사 및 lexicon 단어들을 대상으로 Fuzzy 매치 수행 후 `reference+fuzzy:<score>` 소스의 `proper_noun` 제안 생성.
- **설정 및 영속화 확장**:
  - `Settings` 데이터클래스에 `fuzzy_matching_enabled`와 `fuzzy_threshold` 기본값(True, 0.70) 적용.
  - `SettingsService` 및 `TranscribeRequest` 필드 연동 완료.
- **CLI/GUI 제어 패널**:
  - `pulpit-ink transcribe` CLI 인자 `--fuzzy/--no-fuzzy` 및 `--fuzzy-threshold` 추가.
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
- 후처리 파이프라인 (`pulpit_ink.core.postprocess`):
  - 기본 설교/성경 용어 사전 + 사용자 사전(JSON) 누적 적용.
  - 성경 구절 정규화: `로마서 일장 일절` → `로마서 1장 1절`, `고린도 전서` → `고린도전서`.
  - `clean_text` 채움(라우 텍스트는 절대 변경하지 않음).
- 원문 대조 파이프라인 (`pulpit_ink.core.reference`):
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
- CLI 옵션 `pulpit-ink transcribe --reference sermon.md --user-dict dict.json`.
- CLI 서브커맨드 `pulpit-ink corrections list/apply/ignore`.
- Windows 패키징 일체:
  - `pulpit-ink.spec` (PyInstaller).
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
- SQLite 기반 영속 계층 (`pulpit_ink.storage`): `jobs`, `segments`, `exports` 테이블과
  `JobRepository` CRUD 헬퍼. DB 경로는 `platformdirs`로 사용자 데이터 디렉터리 아래에 자동 생성.
- `SettingsService`로 기본 언어/모델/전처리 프리셋/출력 폴더/모델 캐시 경로를 JSON에 저장·로드.
- `model_service`에서 지원 STT 모델 목록과 캐시 경로를 노출.
- `transcribe_service.run_transcribe`에 `persist` 옵션 추가: 작업·세그먼트·export를 DB에 기록하고,
  실패 시 `status=failed` + `error_message`를 남깁니다. `raw_text`는 항상 보존됩니다.
- CLI 서브커맨드: `jobs list/show/export`, `settings show/set`, `models list/cache-dir`, `db-path`.
  `transcribe`는 기본적으로 DB에 결과를 기록합니다.
- PySide6 GUI (`python -m pulpit_ink.app.main`): 파일 추가/드래그 앤 드롭, 작업 큐, 언어·모델·
  프리셋·출력 폴더 설정, 변환 시작, 진행률·로그, 결과 미리보기, 최근 작업 목록.
  변환은 QThread 워커에서 실행되어 UI가 멈추지 않습니다.

### Changed
- `tests/conftest.py`에서 `get_app_paths`를 임시 디렉터리로 패치하여 테스트가 실제
  사용자 DB·설정을 건드리지 않도록 격리.

### Notes
- 스키마는 `schema_meta`에 버전(현재 `1`)을 기록합니다. 사용자 데이터 손실 가능성이
  있는 변경은 별도 마이그레이션 단계로 진행할 예정입니다.
- PySide6는 옵션 의존성입니다. `pip install "pulpit-ink[gui]"`로 설치하세요.

## Unreleased - 2026-05-19

### Changed
- `/goal` 입력 제한 4000자에 맞춰 Goal 2 프롬프트를 축약했습니다.
- SQLite, 설정, 모델 관리, PySide6 GUI, 작업 큐 구현 범위는 유지하되 중복 설명을 제거했습니다.

### Documentation
- 3-Goal 바이브 코딩 프롬프트 문서를 갱신했습니다.
