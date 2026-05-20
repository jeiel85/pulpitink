# Release Checklist

체크리스트는 Goal 3 패키징 단계 기준입니다. 사용 도구:
``scripts/build_windows.ps1`` (PyInstaller + ZIP), GitHub Actions workflow
``build-windows.yml``.

## Release Rule

- 릴리즈 트리거는 `v*` 태그 push 입니다.
- 태그 버전(`v0.3.0` → `0.3.0`)과 `pyproject.toml` 버전이 다르면 빌드를 중단합니다.
- GitHub Actions는 Windows Portable ZIP을 빌드하고 `SHA256SUMS.txt`를 생성합니다.
- 태그 push 빌드가 성공하면 GitHub Release를 자동 생성하고 ZIP + checksum 파일을 첨부합니다.
- 릴리즈 본문은 `CHANGELOG.md`의 `## [버전] - 날짜` 섹션에서 추출합니다. 섹션이 없으면 기본 문구로 생성됩니다.
- 수동 실행(`workflow_dispatch`)은 빌드 artifact 검증용이며 GitHub Release를 만들지 않습니다.

## Code

- [x] `python -m pytest` 통과 (2026-05-20, 91/91)
- [x] `python -m ruff check .` 통과 (2026-05-20)
- [x] CLI `sermonscript doctor` 통과 (2026-05-20)
- [ ] GUI 가 깨끗한 Windows VM 에서 정상 실행
- [x] 30분 분량 MP3 변환 + Export(txt/json/md/srt/vtt/csv) 검증 (회차 #1, 35분 45초, [tests/integration/results.md](../../tests/integration/results.md))
- [x] 편집기에서 edited_text 저장이 raw_text 를 덮어쓰지 않는지 확인 (회귀 테스트로 보장: `tests/test_transcript_editor_repo.py`)
- [ ] 원문 대조 워크플로우: 교정 후보 생성 → 적용/무시 가능 — **회차 #1에서 0건 발견, [known-limitations §10](../known-limitations.md#10-원문-대조--자동-교정-적중률-v10) 참고**

## Security and Privacy

- [ ] 비공개 오디오 파일 미포함
- [ ] 트랜스크립트 미포함
- [ ] 기본 로그에 전체 transcript 가 남지 않음
- [ ] 캐시 삭제 동작 확인
- [ ] 최근 파일 기록을 사용자가 비활성화할 수 있음

## Licensing

- [x] LICENSE 동봉 (2026-05-20, Portable ZIP 내 `LICENSE.txt`)
- [ ] THIRD_PARTY_NOTICES.md 가 실제 의존성과 일치
- [ ] FFmpeg 정책 (번들 미포함) 명시
- [ ] PySide6 LGPL 정책 명시
- [ ] 모델 파일 정책 (번들 미포함) 명시
- [x] Binary artifact 구성 문서화 (2026-05-20, Portable ZIP 내 `PORTABLE-README.txt`)

## Packaging

- [x] PyInstaller 번들 생성: `scripts/build_windows.ps1` (2026-05-20)
- [x] Portable ZIP 생성: `scripts/make_portable_zip.ps1` (2026-05-20)
- [x] 산출물 파일명이 `SermonScript_Portable_{version}.zip` 패턴 (2026-05-20, `SermonScript_Portable_0.3.0.zip`)
- [x] FFmpeg, 모델 파일이 번들에 포함되지 않았는지 확인 (2026-05-20, ZIP 내 `ffmpeg.exe`/`ffprobe.exe` 없음, STT 모델 파일 미발견)
- [ ] GitHub Actions `build-windows.yml` 가 태그 푸시에서 정상 동작
- [x] GitHub Release 자동 생성 규칙 정의 (2026-05-20, `build-windows.yml`)
- [x] SHA256 checksum artifact 생성 규칙 정의 (2026-05-20, `SHA256SUMS.txt`)
- [ ] 앱 아이콘 포함 (선택)
- [ ] pyproject.toml 버전 업데이트
- [x] CHANGELOG.md / HISTORY.md 업데이트 (2026-05-20)

## Documentation

- [x] README 업데이트 (`README.md` 본 프로젝트 진입점으로 재작성, 2026-05-20)
- [x] 사용자 가이드 업데이트 (`docs/user-guide.md` 신규 작성, 2026-05-20)
- [ ] 스크린샷 갱신 (GUI 변환/편집기 캡처 추가 예정)
- [x] 알려진 제한 사항 문서화 (`docs/known-limitations.md` 신규 작성, 2026-05-20)
- [x] `docs/deferred-youtube-import.md` 로 YouTube 비포함 정책 명시
