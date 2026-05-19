# Roadmap Tasks

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
