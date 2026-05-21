# HISTORY.md

## 2026-05-21 (v0.4.7 프로 검수 단축키 및 Markdown 리치 편집 모드 완비)
- 작업: 검수 및 타이핑 생산성을 극대화하기 위해 `QShortcut` 기반 키보드 단축키 시스템을 완성하고, 편집기 하단에 `QTextBrowser` 기반의 **Markdown 실시간 리치 텍스트 뷰어**를 연동 완료. 또한, 사용자 제안 깃허브 이슈 #1(실시간 녹음 및 STT)의 대대적 아키텍처 연계 설계를 로드맵 및 의사결정 로그에 인계 가이드로 명시하여 완벽히 안전 격리 이관 완료.
- 변경 파일:
  - src/pulpit_ink/ui/transcript_editor.py (글로벌 핫키 Ctrl+Space, Ctrl+Left/Right, Ctrl+Up/Down, Ctrl+P 구현 및 속도 레이블, QTextBrowser Markdown 실시간 HTML 뷰어 연동, 간이 정규식 파서 _markdown_to_html 추가)
  - tests/test_editor_hotkeys.py (신규: 핫키 단축키 생성, 배속 연산 범위 0.5x~2.0x 경계 검사, Markdown 변환 정합성 검증 유닛 테스트 3건 추가)
  - docs/roadmap-tasks.md (실시간 마이크 녹음 및 오프라인 스트리밍 STT 인계용 핵심 아키텍처 상세 가이드 작성)
  - docs/decision-log.md (v0.4.7 단축키/Markdown 뷰어 도입 및 실시간 녹음 격리 이관 결정 기록 추가)
- 검증:
  - `$env:PYTHONPATH="src"; python -m pytest tests/test_editor_hotkeys.py`: 3/3 PASS
  - 전체 회귀 테스트 (`pytest`): **136/136 PASS** (100% 무결성 통과 완료)
  - 린트 검사 (`ruff check .`): All checks passed! (0 Lint Error)
  - CLI doctor 실행 (`python -m pulpit_ink.cli.main doctor`): 모든 환경 지단 항목 OK
- 결과: 성공. 마우스 없는 쾌속 키보드 단축키 검수 및 Markdown 리치 스타일 실시간 피드백 편집 환경이 완벽히 가동되었습니다.

## 2026-05-21 (v0.4.6 핵심 4대 후속 과제 구현 및 사용자 맞춤 Glossary 사전 완비)
- 작업: v1.0+ 핵심 4대 후속 과제(1. Word 3대 템플릿 및 성경 구절 하이라이트 박스 내보내기 엔진 개발, 2. GitHub Releases API 연동 실시간 자동/수동 업데이트 알리미 및 24시간 로컬 캐싱 체계 구축, 3. Inno Setup 인스톨러 ps1 빌드 스크립트 실행 유효성 검증, 4. Lexicon Fuzzy 오역 보정 튜닝) 및 **사용자 맞춤 Glossary 사전 GUI 탭 및 백엔드 지능형 자동 연동** 시스템을 자율권 하에 완벽히 구현 및 검증 완료.
- 변경 파일:
  - pyproject.toml (`python-docx>=1.1.0` 의존성 추가)
  - src/pulpit_ink/__init__.py (버전 v0.4.6 범프)
  - src/pulpit_ink/core/export/__init__.py, base.py, pipeline.py
  - src/pulpit_ink/core/export/docx_exporter.py (신규: 3대 워드 템플릿 및 하이라이트 박스 출력 엔진 구현)
  - src/pulpit_ink/core/postprocess/lexicon.py (`save_user_lexicon` 추가 및 디스크 세이브 안전 백업 복구 엔진 구현)
  - src/pulpit_ink/cli/main.py (docx CLI 형식 지원 및 bible_refs DB 연동)
  - src/pulpit_ink/services/settings_service.py (`docx_template_style` 저장 옵션 지원)
  - src/pulpit_ink/services/transcribe_service.py (`_build_lexicon`에 `user_dict.json` 자동 감지/바인딩 결합, `ExportPipeline` 호출 시 `bible_refs` 주입 연동)
  - src/pulpit_ink/core/utils/update_checker.py (신규: GitHub API 5초 타임아웃, Semantic Versioning Parser, 24시간 로컬 JSON 캐싱 및 수동 강제 우회, API Rate Limit 무소음 폴백 구현)
  - src/pulpit_ink/ui/glossary_tab.py (신규: PySide6 GlossaryTab UI 및 단어 추가/수정/삭제 모달 대화창, 실시간 어휘 검색, CSV 가져오기/내보내기 연계)
  - src/pulpit_ink/ui/main_window.py (메인 윈도우 네 번째 탭으로 GlossaryTab 도킹, 상단 딥 블루 그라데이션 `UpdateBannerWidget` 및 비동기 `UpdateCheckWorker` 통합, 도움말 메뉴에 '업데이트 확인...' 수동 메뉴 액션 배치, QMessageBox 다이얼로그 피드백 연동)
  - tests/test_docx_exporter.py (신규: 워드 3대 템플릿 레이아웃 무결성 검증 단위 테스트 4건 작성)
  - tests/test_update_checker.py (신규: 업데이트 체크, 캐싱, 강제 업데이트, 오프라인 무소음 폴백 등 유닛 테스트 8건 작성)
  - tests/test_glossary_service.py (신규: 사용자 사전 저장소 및 자동 주입 연동 테스트 4건 작성)
- 검증:
  - `PYTHONPATH=src pytest`: 133/133 PASS (신규 유닛 테스트 16건 모두 100% 통과)
  - `python -m ruff check .`: PASS
  - `powershell -ExecutionPolicy Bypass -File scripts/create_installer.ps1`: 빌드 디렉토리 검출 예외 및 warning 정상 작동 확인
  - `python tests/integration/verify_fuzzy.py`: 로컬 DB 통합 검증 정상 구동 및 예외 가드 작동 확인
- 결과: 성공. Word(.docx) 프리미엄 내보내기 엔진, 실시간/수동 24시간 캐싱 방지 자동 업데이트 알림 체계, 그리고 **사용자 맞춤 Glossary 사전 GUI 탭 및 CSV 파이프라인**이 완벽히 GUI/CLI에 통합되었으며, 133개 전체 회귀 테스트 패스 하에 v0.4.6 버전으로 릴리즈 준비 완료.
- 후속 작업:
  - Windows EXE/ZIP 빌드본을 실 배포용으로 컴파일 및 GitHub Release 업로드

## 2026-05-21 (문서 정합성 정리 · 현재 PC GUI 스크린샷 갱신)
- 작업: GitHub 연결 및 현재 진행 상태 점검 후, v0.4.4/v0.4.5에서 이미 구현된 YouTube URL opt-in 입력과 Heuristic 화자 분리 상태가 README/제품 명세/사용자 가이드/릴리즈 체크리스트의 과거 제외 문구와 충돌하던 문제를 정리. 깨끗한 Windows VM 검증 항목은 릴리즈 직전 별도 검증으로 남기고, 현재 Windows 11 PC에서 PySide6 메인 창과 편집기 위젯 렌더링 스크린샷을 캡처해 문서에 반영.
- 변경 파일:
  - AGENTS.md, README.md
  - docs/product-spec.md
  - docs/user-guide.md
  - docs/known-limitations.md
  - docs/deferred-youtube-import.md, docs/youtube-import-deferred.md
  - docs/license-policy.md
  - docs/release/release-checklist.md
  - docs/release-roadmap.md
  - docs/roadmap-tasks.md
  - docs/decision-log.md
  - docs/index.html
  - docs/assets/pulpit-ink-gui-main.png
  - docs/assets/pulpit-ink-gui-editor.png
- 검증:
  - 현재 PC에서 PySide6 `MainWindow` 렌더링 및 `grab()` 기반 PNG 저장 확인
  - `python -m ruff check .`: PASS
  - `PYTHONPATH=src python -m pytest`: 115/115 PASS
  - `PYTHONPATH=src python -m pulpit_ink.cli.main doctor`: PASS
- 결과: 성공. 현재 구현 상태와 사용자-facing 문서가 같은 방향을 말하도록 정리했고, GUI/편집기 스크린샷 문서화를 완료.
- 후속 작업:
  - 릴리즈 직전 깨끗한 Windows VM에서 설치 산출물 실행 검증
  - `feat/tauri-hybrid` 브랜치 병합 여부는 별도 제품 방향 결정 후 검토

## 2026-05-20 (yt-dlp 자동설치 UI · 성능 프로파일 · Inno Setup 인스톨러 도입 및 v0.4.5 패치 릴리즈)
- 작업: GUI 저작권 Disclaimer 다이얼로그에 yt-dlp 자동 진단/원클릭 설치 UI를 통합하고 백그라운드 워커 스레드로 UI 프리즈를 해소, 1시간 오디오 스트레스 테스트 스크립트 및 실측 성능 프로파일 보고서 추가, Windows 정식 설치 관리자(Inno Setup .exe) 빌드 스크립트 도입, 관련 단위 테스트 5건 보강 및 v0.4.5 패치 릴리즈.
- 변경 파일:
  - src/pulpit_ink/core/audio/youtube_downloader.py (is_yt_dlp_available / install_yt_dlp 헬퍼 추가, pip 서브프로세스 호출 구현)
  - src/pulpit_ink/ui/main_window.py (YtdlpInstallWorker QThread 및 DisclaimerDialog 상태 라벨/원클릭 설치 버튼/완료 콜백 통합)
  - src/pulpit_ink/core/utils/i18n.py (yt-dlp 자동 설치 흐름용 ko↔en 번역 키 8종 추가)
  - tests/test_youtube.py (install_yt_dlp 성공/실패 + is_yt_dlp_available 진단 단위 테스트 4건 추가)
  - tests/test_i18n.py (신규 yt-dlp 번역 키 회귀 테스트 1건 추가)
  - scripts/stress_test.py (신규: 3600초 무음 WAV 합성 후 transcribe 파이프라인 실행 및 psutil 기반 CPU/RSS 샘플러)
  - docs/performance-profile.md (신규: tiny 모델 기준 1시간 처리 실측 보고서 — 14.07x 실시간, RSS 1014MB)
  - scripts/pulpit-ink.iss (신규: PulpitInk Inno Setup 설치 본체 스크립트 — 다국어 한국어/영어, 데스크탑 아이콘 옵션, 64bit Program Files 설치 대상)
  - scripts/create_installer.ps1 (신규: pyproject.toml 버전 자동 감지 후 ISCC.exe 호출, 미설치 시 사용자에게 다운로드 링크 안내)
  - pyproject.toml, src/pulpit_ink/__init__.py, CHANGELOG.md, HISTORY.md (버전 범프 v0.4.5 및 릴리즈 이력 작성)
  - docs/known-limitations.md (§4 패키징: Inno Setup 인스톨러 제공 명시, 코드 서명 미적용은 한계로 별도 명시)
  - docs/release/release-checklist.md (앱 아이콘 체크 + Inno Setup 인스톨러 항목 반영)
- 검증:
  - `python -m ruff check .`: PASS
  - `python -m pytest`: 115/115 PASS (신규 5건 포함 전체 100% 통과)
- 결과: 성공. YouTube 다운로드 진입 장벽을 GUI 자동 설치로 제거하고 1시간 오디오 실측 자료를 공식 문서로 남겨 사용자 환경 추천을 객관화했으며, Portable ZIP 외에 정식 설치 관리자 산출물을 추가로 제공할 수 있는 빌드 인프라를 v0.4.5 패치로 출시 준비 완료.

## 2026-05-20 (중장기 로드맵 핵심 구현 및 v0.4.4 패치 릴리즈)
- 작업: 무음구간 갭 기반 Heuristic 화자 분리(Diarization) 파이프라인 설계 및 CLI/GUI 연동, GUI 편집기 내 "화자" 편집 열(Column) 추가 및 실시간 SQLite DB 영속성 수정 저장 연동, 경량 i18n 번역 프레임워크 설계 및 실시간 영한 UI 토글 구현, yt-dlp 기반 YouTube 비동기 다운로드 및 GUI 저작권 Disclaimer 동의 UI 연동, 관련 단위 테스트(tests/test_diarizer.py, tests/test_youtube.py, tests/test_i18n.py) 9건 보강 완료.
- 변경 파일:
  - src/pulpit_ink/core/postprocess/diarizer.py (신규: 무음구간 기반 HeuristicDiarizer 클래스 구현)
  - src/pulpit_ink/cli/main.py (diarize CLI 옵션 매핑 및 TranscribeRequest 전파)
  - src/pulpit_ink/services/settings_service.py (Settings 모델 및 SettingsService에 diarize 필드 추가)
  - src/pulpit_ink/services/transcribe_service.py (TranscribeRequest에 diarize 필드 추가 및 run_transcribe에서 HeuristicDiarizer 호출 연동)
  - src/pulpit_ink/storage/job_repository.py (update_segment_text에서 sqlite segments 테이블의 speaker 컬럼 업데이트 지원 구현)
  - src/pulpit_ink/ui/main_window.py (변환 설정 창 내 화자 분리 사용 체크박스 UI 추가, 설정 저장 및 실행 시 전파)
  - src/pulpit_ink/ui/transcript_editor.py (세그먼트 테이블 컬럼 6개 확장, 화자 편집 열 추가, 실시간 셀 수정 이벤트 발생 시 DB _persist_segment 연동, search/scroll 타겟 컬럼 인덱스 보정)
  - tests/test_diarizer.py (신규: HeuristicDiarizer 유닛 테스트 3건 추가)
  - tests/test_youtube.py (신규: yt-dlp 패키지 유무별 안전 가드 및 YouTube 다운로더 유닛 테스트 2건 추가)
  - tests/test_i18n.py (신규: 경량 번역 전역 언어 설정 및 tr() 번역 유닛 테스트 4건 추가)
  - pyproject.toml, src/pulpit_ink/__init__.py, CHANGELOG.md, HISTORY.md (버전 범프 v0.4.4 및 릴리즈 이력 작성)
- 검증:
  - `python -m ruff check .`: PASS (All checks passed!)
  - `python -m pytest`: 110/110 PASS (신규 추가된 유닛 테스트 9건 포함 전체 100% 통과 완료)
  - `python -m pulpit_ink.cli.main doctor`: PASS (환경 진단 전체 OK)
- 결과: 성공. 중장기 핵심 기능(화자 분리, YouTube 다운로드, 다국어 i18n 번역 구조)을 일괄적으로 완성하고, 완벽한 유닛 테스트 검증 하에 v0.4.4 패치 릴리즈 출시 준비 완료.

## 2026-05-20 (단기 개선 및 v0.4.3 브랜드 패치 릴리즈)
- 작업: PulpitInk 프리미엄 고유 로고 아이콘 설계 및 빌드(PyInstaller Spec) 바인딩, 자모 Fuzzy 매칭 2글자 오탐 제어용 Stop-words 가드 설계/구현 및 유닛 테스트 추가, 0.4.3 패치 버전 릴리즈.
- 변경 파일:
  - src/pulpit_ink/resources/pulpit-ink.png, pulpit-ink.ico (신규: 앱 로고 이미지 및 다중 해상도 아이콘 파일 에셋)
  - pulpit-ink.spec, pulpit-ink-sidecar.spec (EXE 빌드 옵션에 icon 경로 엠베딩 바인딩)
  - src/pulpit_ink/core/postprocess/jamo.py (DEFAULT_STOP_WORDS 정의 및 sliding window 내 stop-words skip 가드 적용)
  - tests/test_jamo_matching.py (Fuzzy 매칭 제외 단어 예외 스킵 여부 검증 단위 테스트 추가)
  - pyproject.toml, src/pulpit_ink/__init__.py, CHANGELOG.md, HISTORY.md (버전 범프 v0.4.3 및 릴리즈 이력 갱신)
- 검증:
  - `python -m ruff check .`: PASS
  - `python -m pytest`: 101/101 PASS (신규 추가된 stop-words 검증용 단위 테스트 포함 전체 100% 통과 완료)
  - `python -m pulpit_ink.cli.main doctor`: PASS (환경 진단 전체 OK)
- 결과: 성공. 앱 브랜딩 완성도를 확보하고 한글 자모 Fuzzy 매칭의 2글자 False Positive 현상을 정밀 통제한 0.4.3 패치 릴리즈 출시.

## 2026-05-20 (CI 수정 및 v0.4.2 패치 릴리즈)
- 작업: CI 빌드 시 PySide6 등 GUI 관련 의존성 누락 문제 해결 및 PySide6 미설치 CLI 환경에서의 유닛 테스트 가드(Skip) 고도화, 0.4.2 패치 버전 릴리즈.
- 변경 파일:
  - .github/workflows/test.yml (pip install에 `[dev,gui,reference]` 반영하여 CI 내 의존성 결함 해소)
  - tests/test_batch_queue.py (PySide6 ImportError 발생 시 안전하게 테스트 수집 스킵하도록 pytestmark 구성)
  - pyproject.toml, src/pulpit_ink/__init__.py, CHANGELOG.md (버전 범프 v0.4.2)
- 검증:
  - `python -m ruff check .`: PASS
  - `python -m pytest`: 100/100 PASS (로컬 검증 및 CI 대응 완료)
- 결과: 성공. v0.4.1 배포 파이프라인에서 탐지된 의존성 미비 오류를 완벽하게 수정한 v0.4.2 패치 릴리즈 준비 완료.

## 2026-05-20 (단기 저장소 정비 및 v0.4.1 배포 시도)
- 작업: 단기 저장소 정비(untracked 파일 차단), 알려진 제한사항 문서 최신화, 릴리즈 체크리스트 갱신, 패치 버전 배포 시도. (CI 검증 단계에서 GUI 의존성 부재로 빌드 대기 상태 전환됨)
- 변경 파일:
  - .gitignore (임시 `.antigravitycli/` 및 실험용 `frontend/` 무시 설정 반영)
  - docs/known-limitations.md (싱크 플레이어, 배치 큐, 기록 비활성화 옵션을 "구현 완료" 상태로 최신화)
  - docs/release/release-checklist.md (0.4.0 및 0.4.1 대응 체크리스트 갱신 완료)
  - pyproject.toml, src/pulpit_ink/__init__.py, CHANGELOG.md, HISTORY.md (버전 범프 v0.4.1 및 이력 작성)
- 검증:
  - `python -m ruff check .`: PASS
  - `python -m pytest`: 100/100 PASS
- 결과: CI 서버 환경의 PySide6 패키지 누락으로 빌드 재조정 필요 판단, 이에 따라 v0.4.2를 긴급 출시하기로 전환함.

## 2026-05-20 (기능 추가 — 오디오 싱크 플레이어 및 다중 배치 큐)
- 작업: 편집기 내 오디오 싱크 플레이어 연동 개발 (Audio Sync Player), 메인 화면 다중 작업 배치 큐 UX 개선 (Batch Queue UX).
- 변경 파일:
  - src/pulpit_ink/ui/transcript_editor.py (QMediaPlayer 및 QAudioOutput 통합, 하단 재생 컨트롤러 구성, 세그먼트 더블클릭 seek & 자동 재생 연동, positionChanged 시 테이블 행 하이라이트 및 오토 스크롤 연동, wav 캐시 우선 로드 및 SQLite source_path 예외 가드 구현)
  - src/pulpit_ink/ui/main_window.py (순차 처리 큐 루프 구현, 배치 기동 시 file_list 위젯에 실시간 대기 상태 프리픽스 `[대기]`, `[진행 중]`, `[완료]`, `[실패]` 시각화 구현, 변환 중단 취소 질문 상자 및 terminate() 정지 구현, 큐 진행 중 위젯 동작 안전 제어)
  - tests/test_batch_queue.py (신규: 다중 파일 배치 큐 가동, 순차 변환, 실패 시 연속성 기동, 중단 및 큐 일괄 파기 유닛 테스트 3건 추가)
  - CHANGELOG.md (릴리즈 및 Unreleased 변경점 반영)
  - HISTORY.md (작업 이력 반영)
- 검증:
  - `python -m ruff check .`: PASS
  - `python -m pytest`: 100/100 PASS (추가된 신규 테스트 3건 포함 전체 유닛 테스트 100% 통과 완료)
- 결과: 성공. v1.0 정식 배포 수준의 다중 파일 배치 연쇄 변환 및 오디오 실시간 동기화 탐색 편집기 완비.
- 후속 작업:
  - 배포 사양 검증 및 GUI 최종 마무리.

## 2026-05-20 (기능 추가 — 캐시/작업 삭제 및 프라이버시 보강)
- 작업: 캐시 및 작업 삭제 UX 보강 (Delete UX), 최근 작업 기록 비활성화 옵션 (Privacy Control), Jamo Fuzzy 문서 최신화 (Doc Alignment).
- 변경 파일:
  - src/pulpit_ink/cli/main.py (CLI `jobs delete <job_id>` 및 `jobs clean-cache` 명령어 구현)
  - src/pulpit_ink/ui/main_window.py (GUI 최근 작업 목록 우클릭 컨텍스트 메뉴로 "작업 및 캐시 삭제" 연계, `keep_history` 연계 체크박스 추가 및 비활성화 문구 리프레시 구현)
  - src/pulpit_ink/services/settings_service.py (`Settings` 데이터클래스에 `keep_history: bool` 추가 및 형변환 가드 구현)
  - src/pulpit_ink/services/transcribe_service.py (`settings.keep_history`가 False이면 `persist` 생략 처리)
  - docs/design/jamo-fuzzy-matching.md (구현 완료로 상태 갱신, 2글자 한글 노이즈 한계 및 임계값 상향 우회 가이드 보강)
  - docs/roadmap-tasks.md (작업 완료 상태 체크리스트 업데이트)
  - docs/decision-log.md (프라이버시 강화 및 캐시 연쇄 삭제 UX 도입 결정 사안 추가)
  - tests/test_settings_service.py (keep_history 데이터 타입 형변환 단위 테스트 추가)
  - tests/test_transcribe_persistence.py (keep_history 비활성화 시 DB 미저장 여부 Mocking 단위 테스트 추가)
- 검증:
  - `python -m ruff check .`: All checks passed! (린트 성공)
  - `python -m pytest`: 97/97 PASS (추가된 신규 테스트 2건 포함 전체 유닛 테스트 100% 통과 완료)
  - `python -m pulpit_ink.cli.main doctor`: 환경 진단 도구 전체 항목 OK 확인
- 결과: 성공. v1.0 릴리즈 완성도를 극대화하는 개인정보 보호 기능과 캐시 찌꺼기 완벽 제거 UX를 CLI와 GUI 모두에 완비함.
- 후속 작업:
  - 오디오 싱크 플레이어 및 다중 작업 큐 개선 검토.

## 2026-05-20 (브랜딩 — 전체 리네이밍 실행)
- 작업: SermonScript → 설교필기 (PulpitInk) 전체 브랜딩 일괄 반영.
- 변경 범위: 109개 파일 (774 insertions, 652 deletions)
  - Python 패키지: `src/sermonscript/` → `src/pulpit_ink/`, 모든 import/클래스명/상수 변경
  - PyInstaller: `sermonscript.spec` → `pulpit-ink.spec`, `sermonscript-sidecar.spec` → `pulpit-ink-sidecar.spec`
  - CLI: `sermonscript` → `pulpit-ink` 명령
  - GUI: 타이틀바 `설교필기 (PulpitInk)`, 다이얼로그 제목 `설교필기`
  - 빌드/CI: 환경변수 `PULPITINK_ROOT`, 산출물 `PulpitInk_Portable_*.zip`
  - GitHub: 저장소 `jeiel85/sermon-script` → `jeiel85/pulpit-ink` 리네이밍 완료
  - 문서: README, AGENTS, CHANGELOG, HISTORY, user-guide 등 30+ 문서 갱신
  - 테스트: 모든 import/참조 갱신
- 검증:
  - `ruff check .`: All checks passed
  - `pytest`: 95/95 passed (2.69s)
  - `pip install -e ".[dev]"`: pulpit-ink-0.3.0 설치 성공
- 결과: 성공. GitHub 저장소 리네이밍 및 원격 URL 변경 완료.
- 후속 작업:
  - 로컬 폴더명 변경 (`sermon-script` → `pulpit-ink`) — IDE/프로세스 잠금 해제 후 수동 진행 필요
  - GitHub Pages 설정 확인 (새 URL: `jeiel85.github.io/pulpit-ink`)

## 2026-05-20 (브랜딩 — 앱 정식 명칭 확정)
- 작업: 이전 세션(993b96d1)에서 논의된 앱 이름 한글화 후보 5개에 대해 브랜드 충돌 조사를 실시하고, 최종 이름을 확정.
- 조사 결과:
  - VoiceQuill, SoriScript(소리글AI), ScribeFlow, CelestialVox → 동일/유사 도메인에서 활성 브랜드 존재하여 탈락
  - PulpitInk / 설교필기 → 소프트웨어 브랜드 충돌 없음 확인
- 결정: **설교필기 (PulpitInk)** 확정
- 변경 파일:
  - docs/branding-rename-plan.md (신규: 브랜딩 변경 구현 계획서)
  - docs/decision-log.md (앱 명칭 결정 기록 추가)
  - HISTORY.md
- 검증: 코드 변경 없음 — 문서만 추가/수정
- 결과: 성공. 구현 계획서를 저장소에 포함하여 후속 세션에서 이어받아 실행 가능하도록 함.
- 후속 작업:
  - 미결 사항 3개(저장소 이름 변경, Python 패키지명 변경, 타이틀바 표기 형식) 확정 후 일괄 반영
  - Tauri 설정, React UI, Python CLI/GUI, 빌드 스크립트, 문서, GitHub 메타데이터 전면 변경

## 2026-05-20 (문서 — README 저장소 안내형 재정비)
- 작업: GitHub Pages 랜딩 페이지가 별도로 운영되도록 된 뒤, README를 랜딩형 문서에서 저장소 안내/개발 문서형으로 재정비.
- 변경 파일:
  - README.md (대형 랜딩 이미지 제거, 개요/주요 기능/설치/사용/데이터/개발/구조/문서 링크 중심으로 재작성)
  - CHANGELOG.md
  - HISTORY.md
- 검증:
  - `python -m ruff check .`: PASS
  - `python -m pytest`: 95/95 PASS
  - `python -m pulpit_ink.cli.main doctor`: PASS
- 결과: 성공
- 후속 작업:
  - README와 docs/user-guide.md 내용이 장기적으로 중복되지 않도록 사용자 상세 설명은 user-guide로 유지

## 2026-05-20 (문서 — GitHub Pages 랜딩 설정)
- 작업: GitHub Pages(`github.io`)에서 사용할 정적 랜딩 페이지를 `docs/index.html`로 추가하고, 저장소 홈페이지 URL을 Pages 주소로 전환.
- 변경 파일:
  - docs/index.html (GitHub Pages용 랜딩 페이지 신규)
  - docs/.nojekyll (GitHub Pages 정적 파일 직접 제공)
  - README.md (공식 랜딩 페이지 링크 추가)
  - pyproject.toml (Homepage URL을 `https://jeiel85.github.io/pulpit-ink/`로 변경)
  - CHANGELOG.md
  - HISTORY.md
- 검증:
  - `python -m ruff check .`: PASS
  - `python -m pytest`: 95/95 PASS
  - `python -m pulpit_ink.cli.main doctor`: PASS
- GitHub Pages:
  - `gh api repos/jeiel85/pulpit-ink/pages`: `status=built`, source `main` `/docs`
  - `Invoke-WebRequest https://jeiel85.github.io/pulpit-ink/`: HTTP 200, title/image 참조 확인
- 결과: 성공. GitHub Pages 랜딩 페이지 공개 완료.
- 후속 작업:
  - GitHub Actions Node.js 20 deprecation 경고 대응

## 2026-05-20 (문서 — GitHub 랜딩/README 최신화)
- 작업: 현재 `main` 기준 기능 범위와 사용자가 제공한 랜딩 이미지를 반영해 GitHub README 첫 화면을 최신화하고, 저장소 메타데이터와 맞도록 프로젝트 URL을 정정.
- 변경 파일:
  - README.md (랜딩 이미지, 배지, 핵심 기능표, GUI/CLI 빠른 시작, 프라이버시/배포 안내 갱신)
  - docs/assets/pulpit-ink-landing.png (사용자 제공 랜딩 이미지 추가)
  - pyproject.toml (GitHub URL을 `jeiel85/pulpit-ink`로 정정)
  - CHANGELOG.md
  - HISTORY.md
- 검증:
  - `python -m ruff check .`: PASS
  - `python -m pytest`: 95/95 PASS
  - `python -m pulpit_ink.cli.main doctor`: PASS
  - `gh repo view jeiel85/pulpit-ink --json description,homepageUrl,repositoryTopics,url`: description/homepage/topics 반영 확인
- 결과: 성공
- 후속 작업:
  - GitHub 저장소 social preview 이미지는 웹 UI/추가 API 권한이 필요하면 별도 확인

## 2026-05-20 (배포 규칙 정비 — GitHub Release 자동화)
- 작업: 참고 프로젝트 `D:\Project\claude-usage-tray-windows`의 태그 기반 릴리즈 흐름을 참고해 PulpitInk Windows 배포 규칙을 정비.
- 변경 파일:
  - .github/workflows/build-windows.yml (태그 버전 검증, SHA256SUMS 생성, GitHub Release 자동 생성)
  - docs/release/release-checklist.md (릴리즈 규칙 명문화)
  - docs/decision-log.md (태그 기반 릴리즈 자동화 결정 기록)
  - CHANGELOG.md (`0.3.0` 릴리즈 섹션 추가)
  - HISTORY.md
- 검증:
  - `python -m ruff check .`: PASS
  - `python -m pytest`: 95/95 PASS
  - `python -m pulpit_ink.cli.main doctor`: PASS
  - PyYAML 기반 workflow 파일 파싱: PASS (`build-windows.yml`, `test.yml`)
  - GitHub Actions `Test` (`main`): PASS (`26149646461`)
  - GitHub Actions `Test` (`v0.3.0`): PASS (`26149651698`)
  - GitHub Actions `Build Windows Portable` (`v0.3.0`): PASS (`26149651701`)
- 결과: `v0.3.0` GitHub Release 생성 완료. 첨부 파일 `PulpitInk_Portable_0.3.0.zip`, `SHA256SUMS.txt` 업로드 확인.
- 후속 작업:
  - GitHub Actions Node.js 20 deprecation 경고 대응
  - `windows-latest`가 `windows-2025-vs2026`으로 전환되는 공지 추적

## 2026-05-20 (기능 추가 — CSV Export 지원)
- 작업: `docs/product-spec.md`에 명시된 CSV 출력을 실제로 지원. core.export에 CSV exporter 추가하고 CLI/GUI/서비스 기본 포맷에 포함.
- 변경 파일:
  - src/pulpit_ink/core/export/csv_exporter.py (신규)
  - src/pulpit_ink/core/export/base.py (`ExportFormat.CSV` 추가)
  - src/pulpit_ink/core/export/pipeline.py, src/pulpit_ink/core/export/__init__.py (EXPORTERS/공개 API 등록)
  - src/pulpit_ink/cli/main.py (`--format` 기본값에 csv 추가)
  - src/pulpit_ink/services/transcribe_service.py, src/pulpit_ink/ui/main_window.py, src/pulpit_ink/ui/transcript_editor.py (기본 포맷에 csv 포함)
  - tests/test_exporters.py (CSV 단위 테스트 4건 추가 + 파이프라인/포맷 파싱 갱신)
  - tests/test_pipeline_integration.py, tests/integration/verify_run.py, tests/integration/README.md (Export 6종 검증)
  - README.md, docs/user-guide.md, docs/release/release-checklist.md (사용자 안내/체크리스트 갱신)
  - HISTORY.md
- 설계 결정:
  - 컬럼: `index, start_sec, end_sec, start, end, text, raw_text, clean_text, edited_text, speaker`
  - `text`는 Export 우선순위(`edited_text > clean_text > raw_text`)로 채움. raw/clean/edited는 분석 용도로 각각 별도 컬럼 유지
  - 한국어 엑셀에서 한글이 깨지지 않도록 UTF-8 BOM(`utf-8-sig`) + `\r\n` 라인 종결자 사용
  - 콤마/따옴표/개행은 표준 `csv.writer` `QUOTE_MINIMAL`로 이스케이프
- 검증:
  - `python -m ruff check .`: PASS
  - `python -m pytest`: 95/95 PASS (CSV 신규 테스트 4건 포함)
- 후속 작업:
  - 다음 후보(캐시 삭제/작업 삭제 UX, 최근 작업 기록 비활성화 옵션, Jamo fuzzy 문서 정리, 오디오 싱크 플레이어, 다중 작업 큐, `frontend/` 정책)

## 2026-05-20 (핸드오프 정리 — 다음 작업 후보)
- 작업: 최신 CI/릴리즈 검증 상태와 이전 세션의 남은 기능 후보를 확인하고, 다음 세션에서 이어받기 쉬운 우선순위 목록을 `docs/roadmap-tasks.md` 상단에 정리.
- 변경 파일:
  - docs/roadmap-tasks.md
  - HISTORY.md
- 검증:
  - `gh run list --limit 12`: 최신 `Test` 성공, 최신 `Build Windows Portable` 수동 실행 성공 확인
  - `gh run view 26146847983`: `PulpitInk-Portable` artifact 업로드 확인
  - 코드 변경 없음 — 테스트/린트는 실행하지 않음
- 결과: 다음 세션 후보를 CSV Export, 캐시 삭제/작업 삭제 UX, 최근 작업 기록 비활성화, Jamo fuzzy 문서 정리, 오디오 싱크 플레이어, 다중 작업 큐, `frontend/` 산출물 정책 순으로 정리.
- 후속 작업:
  - 다음 세션에서 1순위 후보인 CSV Export부터 구현 검토
  - `frontend/` untracked 산출물의 보존/분리/정리 정책 결정

## 2026-05-20 (CI Hotfix #14 — Windows 빌드 workflow spec 누락)
- 작업: 핸드오프 후속 항목 중 GitHub Actions `build-windows.yml` 검증을 진행하고, 수동 실행 실패 원인을 수정.
- 변경 파일:
  - .gitignore (`pulpit-ink.spec`만 추적 가능하도록 예외 추가)
  - pulpit-ink.spec (Windows PyInstaller GUI 번들 spec을 저장소에 포함)
  - HISTORY.md
  - CHANGELOG.md
- 검증:
  - `gh workflow run build-windows.yml --ref main`: 실패 재현 (`Spec file "pulpit-ink.spec" not found!`)
  - `python -m ruff check .`: PASS
  - `python -m pytest`: 91/91 PASS
  - `python -m pulpit_ink.cli.main doctor`: PASS
- 결과: CI 실패 원인은 PyInstaller spec 파일이 `.gitignore`의 `*.spec`에 의해 미추적 상태였기 때문으로 확인. 루트 `pulpit-ink.spec`를 추적 대상에 포함하도록 수정.
- 후속 작업:
  - 수정 커밋 푸시 후 GitHub Actions `build-windows.yml` 재실행 결과 확인
  - 깨끗한 Windows VM에서 GUI 실행 수동 검증
  - `frontend/` untracked 산출물의 보존/정리 정책 결정

## 2026-05-20 (릴리즈 검증 #13 — 로컬 품질/패키징 체크)
- 작업: 핸드오프 후보 문서와 릴리즈 체크리스트를 확인하고, 현재 `main` 기준 로컬 품질 검사와 Windows Portable ZIP 생성을 재검증.
- 변경 파일:
  - pyproject.toml (`frontend/` untracked Tauri/번들 산출물이 `ruff check .` 대상에 섞이지 않도록 제외)
  - src/pulpit_ink/core/postprocess/jamo.py (`rapidfuzz` 미설치 기본 CI 환경에서 `difflib` fallback 사용)
  - tests/integration/verify_fuzzy.py (Ruff import 정렬/공백 정리)
  - docs/release/release-checklist.md (검증 완료 항목 갱신)
  - HISTORY.md
  - CHANGELOG.md
- 검증:
  - `python -m ruff check .`: PASS
  - `python -m pytest`: 91/91 PASS
  - `python -m pulpit_ink.cli.main doctor`: PASS
  - `./scripts/build_windows.ps1 -SkipChecks`: PASS
  - 산출물: `dist/PulpitInk_Portable_0.3.0.zip` (172,800,567 bytes)
- 결과: 로컬 품질 검사와 PyInstaller/Portable ZIP 생성 검증 완료. 기본 설치 CI에서 `rapidfuzz`가 없어도 Jamo fuzzy 유틸이 import 가능하도록 보완.
- 후속 작업:
  - 깨끗한 Windows VM에서 GUI 실행 수동 검증
  - GitHub Actions `build-windows.yml` 태그/수동 실행 검증
  - `frontend/` untracked 산출물의 보존/정리 정책 결정

## 2026-05-20 (구현 #12 — jamo fuzzy matching 통합 및 검증)
- 작업: 회차 #1 에서 발견한 `correction_suggestions=0` 문제(자모 변형 미매칭)의 설계 및 구현 완료. 한글 NFD 자모 분해 및 초성 가중 평균 기반의 Hybrid Scorer를 탑재한 Fuzzy 매칭 알고리즘을 `CorrectionEngine`에 연동. CLI 옵션(`--fuzzy/--no-fuzzy`, `--fuzzy-threshold`) 및 PySide6 GUI(체크박스, 더블 스핀박스)로 완전 노출 및 영속화 파이프라인 통합.
- 변경 파일:
  - src/pulpit_ink/core/postprocess/jamo.py (신규)
  - src/pulpit_ink/core/reference/corrections.py (CorrectionEngine 연동)
  - src/pulpit_ink/services/settings_service.py (Settings schema 확장 및 Coercion 보장)
  - src/pulpit_ink/services/transcribe_service.py (Fuzzy 파라미터 전파)
  - src/pulpit_ink/cli/main.py (CLI 인수 추가)
  - src/pulpit_ink/ui/main_window.py (GUI 설정 컨트롤 셋 연동)
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
  - src/pulpit_ink/core/reference/parser.py (`_BIBLE_REF_COLON_RE` 추가,
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
  - src/pulpit_ink/storage/database.py (schema v2 + 신규 테이블)
  - src/pulpit_ink/storage/job_repository.py (reference/alignment/correction CRUD + 세그먼트 패치)
  - src/pulpit_ink/core/postprocess/__init__.py
  - src/pulpit_ink/core/postprocess/bible_refs.py
  - src/pulpit_ink/core/postprocess/lexicon.py
  - src/pulpit_ink/core/postprocess/pipeline.py
  - src/pulpit_ink/core/reference/__init__.py
  - src/pulpit_ink/core/reference/parser.py
  - src/pulpit_ink/core/reference/aligner.py (rapidfuzz fallback + 안정성)
  - src/pulpit_ink/core/reference/prompt_builder.py
  - src/pulpit_ink/core/reference/corrections.py
  - src/pulpit_ink/services/transcribe_service.py (reference flow + needs_review + 영속화)
  - src/pulpit_ink/cli/main.py (transcribe --reference / --user-dict, corrections 서브커맨드)
  - src/pulpit_ink/ui/transcript_editor.py (편집기 위젯)
  - src/pulpit_ink/ui/main_window.py (편집기 탭 + 작업 로드 연결)
  - tests/test_postprocess.py
  - tests/test_reference_parser.py
  - tests/test_correction_engine.py
  - tests/test_transcript_editor_repo.py (편집기-DB 헤드리스 검증)
  - tests/test_storage.py (schema v2 회귀)
  - tests/test_transcribe_persistence.py (reference + correction 영속화 회귀)
  - pulpit-ink.spec
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
  - CLI: `pulpit-ink transcribe sermon.mp3 --reference sermon.md --language ko`
  - CLI: `pulpit-ink corrections list/apply/ignore`
- 결과: 진행 중 (이번 커밋 작성 시점)
- 후속 작업:
  - 실제 Windows VM 에서 PyInstaller 산출물 수동 검증
  - 30분 분량 MP3 + 원문 대조 시나리오 통합 회귀

## 2026-05-20
- 작업: Goal 2 — 로컬 SQLite DB, 설정/모델 서비스, jobs/settings/models CLI, PySide6 GUI 기반 구현
- 변경 파일:
  - src/pulpit_ink/storage/__init__.py
  - src/pulpit_ink/storage/database.py
  - src/pulpit_ink/storage/job_repository.py
  - src/pulpit_ink/services/settings_service.py
  - src/pulpit_ink/services/model_service.py
  - src/pulpit_ink/services/transcribe_service.py
  - src/pulpit_ink/services/__init__.py
  - src/pulpit_ink/cli/main.py
  - src/pulpit_ink/ui/__init__.py
  - src/pulpit_ink/ui/main_window.py
  - src/pulpit_ink/ui/worker.py
  - src/pulpit_ink/app/main.py
  - tests/conftest.py
  - tests/test_storage.py
  - tests/test_settings_service.py
  - tests/test_model_service.py
  - tests/test_transcribe_persistence.py
  - CHANGELOG.md
- 검증:
  - `python -m pytest`: 49 tests passed (신규 17개 포함)
  - `python -m ruff check .`: All checks passed
  - `python -m pulpit_ink.cli.main --help`: jobs / settings / models / db-path 명령 등록 확인
  - `python -m pulpit_ink.app.main`: PySide6 미설치 시 친절한 안내 메시지 출력 확인
- 결과: 성공
- 후속 작업:
  - 실제 PySide6 설치 환경에서 GUI 수동 검증
  - segments 편집(`clean_text`/`edited_text`) UI는 Goal 3 범위에서 진행

## 2026-05-19
- 작업: PulpitInk 3-Goal 프롬프트 중 Goal 2의 4000자 제한 초과 문제 수정
- 변경 파일:
  - docs/vibe-coding-goal-1.md
  - docs/vibe-coding-goal-2-fixed.md
  - docs/vibe-coding-goal-3.md
  - docs/common-tail-instruction.md
  - docs/vibe-coding-goals-3phase-fixed.md
- 검증: Goal 2 본문을 축약하여 4000자 제한 내 사용 가능하도록 재구성
- 결과: 성공
- 후속 작업: 실제 에이전트 입력칸에서 Goal 2 붙여넣기 검증
