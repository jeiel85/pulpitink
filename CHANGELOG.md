# CHANGELOG.md

## Unreleased

### Documentation
- 바이브 코딩용 `/goal` 프롬프트를 6단계에서 3단계 대형 작업 단위로 재구성했습니다.
- `docs/vibe-coding-goals.md`와 `docs/vibe-coding-goals-3phase.md`에 동일한 3단계 Goal 문서를 포함했습니다.
- README에 3단계 Goal 사용 안내를 추가했습니다.

## v0.2.0 - 2026-05-20

### Added
- SermonScript 제품 설계서 묶음 추가
- Python 3.11+, PySide6, faster-whisper, FFmpeg, SQLite 기반 기술 스택 정의
- 로컬 오디오 파일 기반 STT 파이프라인 설계 추가
- FFmpeg 기반 오디오 전처리 프리셋 설계 추가
- 설교 원문 대조 변환 설계 추가
- 사용자 사전 및 성경 구절 보정 설계 추가
- 타임스탬프 편집기 및 Export 설계 추가
- 바이브 코딩용 `/goal` 프롬프트 단계별 문서 추가
- YouTube URL 입력 기능을 v1.0 제외 및 후순위 기능으로 문서화

### Changed
- 기존 범용 `AGENTS.md` 규칙을 SermonScript 프로젝트에 맞게 조정
- 릴리즈 산출물 검증 대상을 모바일 APK/AAB 중심에서 Windows EXE/ZIP 중심으로 변경

### Documentation
- `docs/product-spec.md`
- `docs/architecture.md`
- `docs/audio-pipeline.md`
- `docs/transcription-pipeline.md`
- `docs/reference-alignment.md`
- `docs/youtube-import-deferred.md`
- `docs/vibe-coding-goals.md`
- `docs/release-roadmap.md`
- `docs/license-policy.md`
- `docs/roadmap-tasks.md`
- `docs/decision-log.md`

### Verification
- 문서 묶음 생성 확인
- 압축 파일 생성 확인

## v0.1.0 - 2026-05-20

### Added
- SermonScript 초기 설계 방향 수립
- 로컬 우선 STT 데스크톱 앱 방향 결정
- PC 우선 개발, 모바일 보조 앱 후순위 전략 결정
