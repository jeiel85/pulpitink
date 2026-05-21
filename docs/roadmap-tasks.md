# Roadmap Tasks

## Next Session Candidates (2026-05-20)

현재 `main` 기준 릴리즈 검증은 대부분 완료된 상태입니다. 최신 확인 결과:

- GitHub Actions `Test`: 성공 (`fix: Windows 빌드 spec 파일 추적`)
- GitHub Actions `Build Windows Portable`: 태그 `v0.3.0` 실행 성공, GitHub Release 생성 및 artifact 업로드 확인
- 로컬 기록: `ruff check .`, `pytest 91/91`, `PulpitInk doctor`, `scripts/build_windows.ps1 -SkipChecks` 통과
- 완료: `Build Windows Portable`의 태그 푸시 트리거는 `v0.3.0`에서 검증되었습니다.
- 주의: 작업트리에 untracked `frontend/` 산출물이 남아 있습니다. 다음 작업자가 보존/분리/정리 정책을 먼저 확인해야 합니다.

다음 세션에서 바로 잡기 좋은 기능 후보:

1. [x] CSV Export 추가 (2026-05-20 완료)
   - `core.export.csv_exporter`, CLI/GUI/서비스 기본 포맷 csv 포함, 단위 테스트 4건 추가, README/사용자 가이드/통합 시나리오 갱신
   - 결과: `pytest 95/95`, `ruff check .` 통과
   - 후속(낮은 우선): 짧은 2글자 한글 false positive와 별개로 발견되는 한계 있으면 별도 정리

2. [x] 캐시 삭제 / 작업 삭제 UX 보강 (2026-05-20 완료)
   - 구현: CLI `jobs delete <job_id>` 및 `jobs clean-cache` 명령어 구현.
   - GUI: 최근 작업 목록 마우스 우클릭 시 컨텍스트 메뉴로 "작업 및 캐시 삭제" 메뉴 추가, `QMessageBox` 최종 확인 후 DB 레코드와 물리 캐시(`cache/jobs/<job_id>`) 연쇄 삭제 처리.
   - 결과: `pytest` 통과 및 `ruff` 린트 완료.

3. [x] 최근 작업 기록 비활성화 옵션 (2026-05-20 완료)
   - 구현: settings 스키마에 `keep_history: bool` 추가. 토글 시 즉시 설정 저장 및 최근 작업 목록을 `"(최근 작업 기록 기능이 비활성화되었습니다)"` 고지 처리.
   - STT: `settings.keep_history`가 False이면 `persist` 매개변수를 오버라이드하여 DB 영속화 과정을 완벽히 생략하도록 우회 처리.
   - 결과: `test_settings_service.py`, `test_transcribe_persistence.py` 테스트 케이스 추가 및 통과.

4. [x] Jamo fuzzy 문서 상태 정리 (2026-05-20 완료)
   - 작업: `docs/design/jamo-fuzzy-matching.md` 상단 상태를 "구현 완료 (v1.0 완비)"로 최신화하고, 2글자 한글 단어 노이즈 한계 및 임계값 상향 우회 가이드를 6절에 명문화하여 다음 작업자의 혼선 최소화.

5. [x] 오디오 싱크 플레이어 (2026-05-20 완료)
   - 근거: `docs/known-limitations.md`에 편집기 후속 작업으로 명시되어 있습니다.
   - 범위: 세그먼트 선택 시 해당 구간 재생, 재생/정지, 위치 이동, GUI 검증.
   - 추천도: 중간. 사용자 가치는 크지만 작업량이 큽니다.

6. [x] 다중 작업 큐 개선 (2026-05-20 완료)
   - 근거: GUI는 여러 파일 추가가 가능하지만 변환은 한 번에 한 작업입니다.
   - 범위: 순차 큐 처리, 완료/실패 상태 표시, 중단/재시도 UX.
   - 추천도: 중간. 긴 파일 배치 처리 니즈가 커질 때 우선순위가 올라갑니다.

7. [x] `frontend/` untracked 산출물 정책 결정 (2026-05-21 완료)
   - 근거: 현재 작업트리에 `frontend/`가 추적되지 않은 상태로 남아 있습니다 (`.vscode`, `dist`, `node_modules`, `src-tauri` 포함).
   - 결정: 로컬 Tauri/프론트엔드 실험 산출물로 보존하되 `main`에는 추적하지 않습니다. `.gitignore`와 Ruff 제외 설정을 유지하고, 병합 판단은 별도 브랜치(`feat/tauri-hybrid`) 검토 작업으로 분리합니다.
   - 브랜치 확인: `feat/tauri-hybrid`는 React/Tauri 골격과 사이드카 연동을 포함하지만, `main` 대비 대규모 변경(165개 파일)이며 일부 문서/패키지명이 과거 `sermonscript` 상태로 되돌아가는 diff가 있어 현재 `main`에 직접 병합하지 않습니다.
   - 주의: 사용자/이전 세션 산출물일 수 있으므로 임의 삭제하지 않습니다.

8. [x] 현재 PC 기준 GUI 스크린샷 갱신 (2026-05-21 완료)
   - 결과: `docs/assets/pulpit-ink-gui-main.png`, `docs/assets/pulpit-ink-gui-editor.png` 추가.
   - 한계: 깨끗한 Windows VM 설치 산출물 실행 검증은 릴리즈 직전 별도 항목으로 유지합니다.

9. [x] YouTube/화자 분리 문서 상태 정합성 정리 (2026-05-21 완료)
   - 결과: v0.4.4 이후 구현된 YouTube opt-in 입력과 Heuristic 화자 분리 상태를 README, 제품 명세, 사용자 가이드, 릴리즈 체크리스트에 반영했습니다.

## Phase 0: 저장소 초기화

- [ ] pyproject.toml 작성
- [ ] src/pulpit_ink 패키지 생성
- [ ] Typer CLI 생성
- [ ] PulpitInk doctor 구현
- [ ] pytest/ruff 설정
- [ ] README 개발 실행법 정리

## Phase 1: CLI 변환기

- [ ] transcribe 명령 추가
- [ ] 입력 파일 검증
- [ ] FFmpeg 변환
- [ ] faster-whisper 실행
- [ ] TXT/JSON Export
- [ ] 에러 메시지 정리

## Phase 2: 오디오 전처리

- [ ] enhancement_presets.py
- [ ] preprocess.py
- [ ] --preset 옵션
- [ ] processed.wav 생성
- [ ] 전처리 테스트

## Phase 3: SQLite

- [ ] jobs 테이블
- [ ] segments 테이블
- [ ] exports 테이블
- [ ] jobs list/show 명령

## Phase 4: GUI

- [ ] PySide6 main window
- [ ] 파일 드래그 앤 드롭
- [ ] 모델/언어/프리셋 선택
- [ ] 변환 worker
- [ ] 결과 표시

## Phase 5: 편집기

- [ ] 타임스탬프 세그먼트 표시
- [ ] edited_text 저장
- [ ] 검색/치환
- [ ] Export 반영

## Phase 6: 원문 대조

- [ ] reference 문서 입력
- [ ] 키워드/성경구절 추출
- [ ] initial_prompt 생성
- [ ] RapidFuzz 정렬
- [ ] 교정 후보 저장
- [ ] UI 적용/무시

## Phase 7: 배포

- [ ] PyInstaller
- [ ] Portable ZIP
- [ ] Setup EXE
- [ ] GitHub Actions
- [ ] 릴리즈 체크리스트
