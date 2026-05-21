# Roadmap Tasks

## Next Session Candidates (2026-05-21)

v0.4.6 마일스톤이 성공적으로 완수되었습니다. 다음 세션 및 차기 출시 마일스톤에서 즉각 적용할 수 있는 고부가가치 5대 핵심 작업 후보군 명세는 다음과 같습니다.

1. **[후보 1] PyInstaller 배포본 물리 패키징 검증 및 Portable ZIP 검수**
   - **세부 작업**: `scripts/build_windows.ps1`을 구동하여 PyInstaller 컴파일 단일 `PulpitInk.exe` 배포 바이너리를 실제 물리 기동하고 라이브러리 누락 여부 검증.
   - **기대 가치**: 최종 릴리즈 품질을 100% 무결하게 확립하여 최종 사용자 설치 배포 리스크 제거.

2. **[후보 2] 프로 검수 단축키 및 Markdown 리치 텍스트 편집 모드**
   - **세부 작업**: 마우스 조작을 원천 제거하는 재생/일시정지/세그먼트 탐색 키보드 핫키(`Ctrl+Space`, `Alt+Left/Right` 등) 연동 및 리치 텍스트 실시간 검수 편집기 지원.
   - **기대 가치**: 교역자/강연 타이피스트들의 텍스트 교정 및 정제 속도를 비약적으로 상승.

3. **[후보 3] GPU 가속 (CUDA/cuDNN) 자동 진단 GUI 및 셋업 가이드**
   - **세부 작업**: 앱 기동 시 CUDA 런타임 및 `.dll` 유무를 자동 감지하고, CPU/GPU 가속 사용 상태를 메인 창 하단 상태바에 시각적으로 상시 표시 및 간편 설정 연계.
   - **기대 가치**: 대용량 오디오 STT 작업의 연산 시간을 최대 5배 이상 대폭 단축할 수 있는 진입 장벽 제거.

4. **[후보 4] 로컬 오프라인 한국어 맞춤법 사전 및 띄어쓰기 가이드 연동**
   - **세부 작업**: 완전 오프라인으로 작동하는 Hunspell 사전 패키지를 내장하여, 검수 시 맞춤법이 어긋난 단어 아래에 붉은 밑줄 표시 및 우클릭 추천 교정어 팝업 탑재.
   - **기대 가치**: 최종 Word 내보내기 전 오프라인에서도 완벽한 맞춤법 검수가 가능해 최종 문서 품질 완성.

5. **[후보 5] 사용자 맞춤 용어(Glossary) 교정 기여도 분석 통계 대시보드**
   - **세부 작업**: 사용자가 등록한 단어장이 변환 파이프라인에서 실제로 몇 차례 동작해 교정했는지 트래킹/SQLite 저장하고, GUI 탭 내에서 교정 기여도를 매력적인 통계 카드 형태로 시각화.
   - **기대 가치**: "사전을 채울수록 업무가 효율화되는 과정"을 사용자에게 직관적으로 보상 및 피드백하여 사전 활용률 유도.

### v0.4.6 마일스톤 개발 완료 이력 (2026-05-21 완료)

1. [x] **Word (.docx) 3대 맞춤형 템플릿 및 성경 하이라이트 박스 내보내기 엔진 개발 완료**
   - `docx_exporter.py` 신규 설계 및 3대 스타일(강대상용, 주보용, 검수용) 서식, 대조 구절 상단 하이라이트 블록 단락 구현 완비.
2. [x] **GitHub Releases API 연동 실시간 업데이트 알리미 및 24시간 로컬 캐싱 체계 도입**
   - 비동기 `UpdateCheckWorker` 및 딥 블루 그라데이션 `UpdateBannerWidget` GUI 통합.
   - API Rate Limit 완벽 방지를 위한 24시간 로컬 캐싱(`update_cache.json`) 및 수동 업데이트(Bypass) 가동 체계 구축.
3. [x] **사용자 맞춤 Glossary 사전 GUI 및 백엔드 지능형 자동 연동 완비**
   - PySide6 기반 `GlossaryTab` 신설(단어 추가/수정/삭제/실시간 검색).
   - 로컬 `%LOCALAPPDATA%/PulpitInk/user_dict.json` 백업/복구 지원형 안전 디스크 세이브(`save_user_lexicon`) 엔진 완비.
   - CSV 사전 파일 일괄 가져오기(Import) 및 내보내기(Export) 파이프라인 완비.


## Phase 0: 저장소 초기화

- [x] pyproject.toml 작성
- [x] src/pulpit_ink 패키지 생성
- [x] Typer CLI 생성
- [x] PulpitInk doctor 구현
- [x] pytest/ruff 설정
- [x] README 개발 실행법 정리

## Phase 1: CLI 변환기

- [x] transcribe 명령 추가
- [x] 입력 파일 검증
- [x] FFmpeg 변환
- [x] faster-whisper 실행
- [x] TXT/JSON Export
- [x] 에러 메시지 정리

## Phase 2: 오디오 전처리

- [x] enhancement_presets.py
- [x] preprocess.py
- [x] --preset 옵션
- [x] processed.wav 생성
- [x] 전처리 테스트
- [x] yt-dlp 기반 비동기 YouTube 오디오 다운로드 파이프라인 구축 (v0.4.4)

## Phase 3: SQLite

- [x] jobs 테이블
- [x] segments 테이블
- [x] exports 테이블
- [x] jobs list/show 명령
- [x] jobs delete 및 clean-cache 명령어로 DB 및 물리 캐시 디렉터리 연쇄 삭제 보강 (v0.4.0)

## Phase 4: GUI

- [x] PySide6 main window
- [x] 파일 드래그 앤 드롭
- [x] 모델/언어/프리셋 선택
- [x] 변환 worker
- [x] 결과 표시
- [x] 다중 작업 배치 큐 순차적 연쇄 처리 및 개별 실패 시 연속 변환 기동 루프 구현 (v0.4.0)
- [x] 경량 i18n 실시간 영한 UI 번역 프레임워크 탑재 및 번역 스위치 UI 연동 (v0.4.4)

## Phase 5: 편집기

- [x] 타임스탬프 세그먼트 표시
- [x] edited_text 저장
- [x] 검색/치환
- [x] Export 반영
- [x] PySide6.QtMultimedia 기반의 오디오 싱크 플레이어 재생 제어 및 테이블 하이라이트 스크롤 연동 (v0.4.0)
- [x] 세그먼트별 화자(Speaker) 편집 열 제공 및 SQLite DB 실시간 수정 영속화 연동 (v0.4.4)

## Phase 6: 원문 대조

- [x] reference 문서 입력
- [x] 키워드/성경구절 추출
- [x] initial_prompt 생성
- [x] RapidFuzz 정렬
- [x] 교정 후보 저장
- [x] UI 적용/무시
- [x] 한글 NFD 자모 분해 및 초성 가중치를 결합한 Hybrid Scorer 기반 한국어 자모 Fuzzy 매칭 탑재 (v0.4.0)
- [x] 자모 Fuzzy 매칭 2글자 오탐 방지를 위한 스톱워드(Stop-words) 게이트 적용 (v0.4.3)

## Phase 7: 배포

- [x] PyInstaller (pulpit-ink.spec, pulpit-ink-sidecar.spec)
- [x] Portable ZIP
- [x] Setup EXE (Inno Setup pulpit-ink.iss 및 create_installer.ps1 스크립트 도입 - v0.4.5)
- [x] GitHub Actions (태그 푸시 및 수동 트리거 기반 Windows Portable ZIP 자동 릴리즈 - v0.3.0)
- [x] 릴리즈 체크리스트 수립 및 갱신 (docs/release/release-checklist.md)
- [x] yt-dlp 자동 진단 및 GUI 저작권 Disclaimer 창 내 백그라운드 원클릭 pip 설치 워커 제공 (v0.4.5)
- [x] 1시간 오디오 벤치마크 및 psutil 기반 CPU/RSS 실측 성능 프로파일 보고서 제공 (v0.4.5)

