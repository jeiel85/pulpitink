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

- [x] `python -m pytest` 통과 (2026-05-20, 100/100)
- [x] `python -m ruff check .` 통과 (2026-05-20)
- [x] CLI `PulpitInk doctor` 통과 (2026-05-20)
- [x] GUI 가 현재 Windows 11 PC 에서 PySide6 위젯 렌더링 및 스크린샷 캡처 가능 (2026-05-21, [메인 화면](../assets/pulpit-ink-gui-main.png), [편집기](../assets/pulpit-ink-gui-editor.png))
- [ ] 깨끗한 Windows VM 에서 설치 산출물 실행 검증 (릴리즈 직전 별도 확인)
- [x] 30분 분량 MP3 변환 + Export(txt/json/md/srt/vtt/csv) 검증 (회차 #1, 35분 45초, [tests/integration/results.md](../../tests/integration/results.md))
- [x] 편집기에서 edited_text 저장이 raw_text 를 덮어쓰지 않는지 확인 (회귀 테스트로 보장: `tests/test_transcript_editor_repo.py`)
- [x] 원문 대조 워크플로우: 교정 후보 생성 → 적용/무시 가능 (Fuzzy 매칭 도입으로 적중률 확보 완료, 2026-05-20, [known-limitations §10](../known-limitations.md#10-원문-대조--자동-교정-적중률-v10) 참고)

## Security and Privacy

- [x] 비공개 오디오 파일 미포함 (2026-05-20)
- [x] 트랜스크립트 미포함 (2026-05-20)
- [x] 기본 로그에 전체 transcript 가 남지 않음 (2026-05-20)
- [x] 캐시 삭제 동작 확인 (CLI clean-cache 및 GUI 컨텍스트 메뉴 검증 완료, 2026-05-20)
- [x] 최근 파일 기록을 사용자가 비활성화할 수 있음 (keep_history 설정 검증 완료, 2026-05-20)

## Licensing

- [x] LICENSE 동봉 (2026-05-20, Portable ZIP 내 `LICENSE.txt`)
- [x] THIRD_PARTY_NOTICES.md 가 실제 의존성과 일치 (2026-05-20)
- [x] FFmpeg 정책 (번들 미포함) 명시 (2026-05-20)
- [x] PySide6 LGPL 정책 명시 (2026-05-20)
- [x] 모델 파일 정책 (번들 미포함) 명시 (2026-05-20)
- [x] Binary artifact 구성 문서화 (2026-05-20, Portable ZIP 내 `PORTABLE-README.txt`)

## Packaging

- [x] PyInstaller 번들 생성: `scripts/build_windows.ps1` (2026-05-20)
- [x] Portable ZIP 생성: `scripts/make_portable_zip.ps1` (2026-05-20)
- [x] 산출물 파일명이 `PulpitInk_Portable_{version}.zip` 패턴 (2026-05-20, `PulpitInk_Portable_0.3.0.zip`)
- [x] FFmpeg, 모델 파일이 번들에 포함되지 않았는지 확인 (2026-05-20, ZIP 내 `ffmpeg.exe`/`ffprobe.exe` 없음, STT 모델 파일 미발견)
- [x] GitHub Actions `build-windows.yml` 가 태그 푸시에서 정상 동작 (2026-05-20, `v0.3.0`)
- [x] GitHub Release 자동 생성 규칙 정의 (2026-05-20, `build-windows.yml`)
- [x] SHA256 checksum artifact 생성 규칙 정의 (2026-05-20, `SHA256SUMS.txt`)
- [x] 앱 아이콘 포함 (2026-05-20, v0.4.3에서 `src/pulpit_ink/resources/pulpit-ink.ico` 탑재 및 PyInstaller spec 바인딩 완료)
- [x] Inno Setup 기반 Windows 설치 관리자 빌드 스크립트 (2026-05-20, v0.4.5, `scripts/create_installer.ps1` + `scripts/pulpit-ink.iss`. 코드 서명은 미적용)
- [x] 1시간 오디오 스트레스 테스트 / 성능 프로파일 보고서 (2026-05-20, v0.4.5, `docs/performance-profile.md`)
- [x] pyproject.toml 버전 업데이트 (2026-05-20, v0.4.0 ~ v0.4.5)
- [x] CHANGELOG.md / HISTORY.md 업데이트 (2026-05-20)

## Documentation

- [x] README 업데이트 (`README.md` 본 프로젝트 진입점으로 재작성, 2026-05-20)
- [x] 사용자 가이드 업데이트 (`docs/user-guide.md` 신규 작성, 2026-05-20)
- [x] 스크린샷 갱신 (2026-05-21, 현재 PC PySide6 렌더링: [메인 화면](../assets/pulpit-ink-gui-main.png), [편집기](../assets/pulpit-ink-gui-editor.png))
- [x] 알려진 제한 사항 문서화 (`docs/known-limitations.md` 신규 작성, 2026-05-20)
- [x] YouTube URL 입력 정책 최신화 (v0.4.4 이후 고지 동의 기반 opt-in 기능으로 전환, `docs/deferred-youtube-import.md` 갱신)
