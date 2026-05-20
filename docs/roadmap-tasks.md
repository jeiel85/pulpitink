# Roadmap Tasks

## Next Session Candidates (2026-05-20)

현재 `main` 기준 릴리즈 검증은 대부분 완료된 상태입니다. 최신 확인 결과:

- GitHub Actions `Test`: 성공 (`fix: Windows 빌드 spec 파일 추적`)
- GitHub Actions `Build Windows Portable`: 수동 실행 성공, artifact `SermonScript-Portable` 업로드 확인
- 로컬 기록: `ruff check .`, `pytest 91/91`, `sermonscript doctor`, `scripts/build_windows.ps1 -SkipChecks` 통과
- 주의: `Build Windows Portable`의 태그 푸시 트리거는 아직 별도 검증 흔적이 없습니다.
- 주의: 작업트리에 untracked `frontend/` 산출물이 남아 있습니다. 다음 작업자가 보존/분리/정리 정책을 먼저 확인해야 합니다.

다음 세션에서 바로 잡기 좋은 기능 후보:

1. [x] CSV Export 추가 (2026-05-20 완료)
   - `core.export.csv_exporter`, CLI/GUI/서비스 기본 포맷 csv 포함, 단위 테스트 4건 추가, README/사용자 가이드/통합 시나리오 갱신
   - 결과: `pytest 95/95`, `ruff check .` 통과
   - 후속(낮은 우선): 짧은 2글자 한글 false positive와 별개로 발견되는 한계 있으면 별도 정리

2. [ ] 캐시 삭제 / 작업 삭제 UX 보강
   - 근거: 릴리즈 체크리스트의 `캐시 삭제 동작 확인`이 남아 있고, 현재 DB cascade 삭제 테스트는 있으나 사용자 관점의 캐시 정리 흐름이 약합니다.
   - 범위: CLI `jobs delete` 또는 `cache clean` 후보 검토, 작업별 `cache/jobs/<job_id>` 삭제, 안전 확인 메시지, 테스트 추가.
   - 주의: 사용자 데이터 삭제 가능성이 있으므로 삭제 범위와 확인 절차를 보수적으로 설계해야 합니다.

3. [ ] 최근 작업 기록 비활성화 옵션
   - 근거: `docs/known-limitations.md`에 v1.x 후속 작업으로 명시되어 있고 개인정보/프라이버시 성격이 있습니다.
   - 범위: settings 스키마에 최근 작업 표시/저장 옵션 추가, GUI 최근 작업 패널 동작 조정, 문서 갱신.
   - 추천도: 중간 이상. 릴리즈 후 사용자 신뢰에 도움이 됩니다.

4. [ ] Jamo fuzzy 문서 상태 정리
   - 근거: `docs/design/jamo-fuzzy-matching.md`는 아직 "구현 미착수 / v1.x 후속"으로 적혀 있지만 실제 구현은 완료되어 있습니다.
   - 범위: 설계 노트를 구현 완료 상태로 갱신하고, 남은 한계(짧은 2글자 단어 false positive/미검출)를 후속 항목으로 분리합니다.
   - 추천도: 중간. 기능 추가는 아니지만 다음 작업자의 혼선을 줄입니다.

5. [ ] 오디오 싱크 플레이어
   - 근거: `docs/known-limitations.md`에 편집기 후속 작업으로 명시되어 있습니다.
   - 범위: 세그먼트 선택 시 해당 구간 재생, 재생/정지, 위치 이동, GUI 검증.
   - 추천도: 중간. 사용자 가치는 크지만 작업량이 큽니다.

6. [ ] 다중 작업 큐 개선
   - 근거: GUI는 여러 파일 추가가 가능하지만 변환은 한 번에 한 작업입니다.
   - 범위: 순차 큐 처리, 완료/실패 상태 표시, 중단/재시도 UX.
   - 추천도: 중간. 긴 파일 배치 처리 니즈가 커질 때 우선순위가 올라갑니다.

7. [ ] `frontend/` untracked 산출물 정책 결정
   - 근거: 현재 작업트리에 `frontend/`가 추적되지 않은 상태로 남아 있습니다 (`.vscode`, `dist`, `node_modules`, `src-tauri` 포함).
   - 범위: 실험 산출물 보존 여부, 별도 브랜치/저장소 분리 여부, `.gitignore` 정책 결정.
   - 주의: 사용자/이전 세션 산출물일 수 있으므로 임의 삭제하지 않습니다.

## Phase 0: 저장소 초기화

- [ ] pyproject.toml 작성
- [ ] src/sermonscript 패키지 생성
- [ ] Typer CLI 생성
- [ ] sermonscript doctor 구현
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
