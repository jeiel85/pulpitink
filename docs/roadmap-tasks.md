# Roadmap Tasks

## Phase 0: 저장소 초기화
- [x] pyproject.toml 작성
- [x] src/sermonscript 패키지 생성
- [x] Typer CLI 생성
- [x] sermonscript doctor 구현
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

## Phase 3: SQLite
- [x] jobs 테이블
- [x] segments 테이블
- [x] exports 테이블
- [x] jobs list/show 명령

## Phase 4: GUI (Legacy - PySide6)
- [x] PySide6 main window
- [x] 파일 드래그 앤 드롭
- [x] 모델/언어/프리셋 선택
- [x] 변환 worker
- [x] 결과 표시
- *참고: 상용 UX 한계 극복을 위해 Phase 8에서 Tauri + React로 전면 마이그레이션 및 PySide6 GUI는 점진적 지원 중단(Deprecated) 처리.*

## Phase 5: 편집기 (Legacy - PySide6)
- [x] 타임스탬프 세그먼트 표시
- [x] edited_text 저장
- [x] 검색/치환
- [x] Export 반영

## Phase 6: 원문 대조 & 자모 Fuzzy 매칭
- [x] reference 문서 입력 및 파싱
- [x] 키워드/성경구절(장/절 및 콜론 표기법) 추출
- [x] initial_prompt 생성
- [x] RapidFuzz 및 difflib 정렬 알고리즘 탑재
- [x] 한국어 자모 분해 및 초성 가중 Hybrid Fuzzy Scorer 알고리즘 구현
- [x] 교정 후보 pending 저장 및 GUI/CLI 적용/무시
- [x] 통합 회귀 1, 2차 수동/자동 검증 완료

## Phase 7: 레거시 배포
- [x] PyInstaller 스펙 정의 (`sermonscript.spec`)
- [x] Portable ZIP 패키징 유틸 스크립트 작성
- [x] GitHub Actions 자동 빌드 파이프라인
- [x] 릴리즈 체크리스트 작성

## Phase 8: Tauri Hybrid UI 대전환 (현재 진행 중)
- [x] Tauri 하이브리드 아키텍처 상세 설계서 작성 (`docs/design/tauri-hybrid-architecture.md`)
- [x] PySide6를 제외한 초경량 백그라운드용 PyInstaller Spec 설계 및 사이드카 빌드 (`sermonscript-sidecar.spec`)
- [x] 사이드카 바이너리 및 305MB 용량의 의존 DLL 디렉터리 추출 및 Tauri binaries 폴더 배정
- [x] React + TypeScript + Vite 기반 프론트엔드 환경 구축 및 Tauri 2.0 CLI 포팅
- [x] Tauri `Cargo.toml`, `tauri.conf.json` 내 `externalBin` 사이드카 맵핑 및 보안 권한 셋업 완료
- [x] Rust 링킹 단에서 비동기 `run_sermonscript_sidecar` 및 실시간 STDOUT/STDERR 파이프 스트림 UI 방출 커맨드 구현 완료
- [x] Tauri 컴파일러 기반 첫 빌드 및 GUI 윈도우 프레임 구동 100% 성공
- [/] React + Tailwind CSS + shadcn/ui 기반 프리미엄 모던 웹 디자인 시스템 구축
- [ ] UI단에서 사이드카 IPC 통신을 통한 오디오 전처리, STT, 원문 대조 연동 테스트 완료
- [ ] 타임라인 재생, 오디오 파형(Waveform) 비주얼라이저 및 실시간 2단 대조 검수 편집기 구현
- [ ] Tauri 2.0 및 사이드카 연동 기반의 최종 Windows 데스크톱 Portable ZIP/EXE 빌드 파이프라인 완성

