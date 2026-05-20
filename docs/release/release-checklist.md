# Release Checklist

체크리스트는 Goal 3 패키징 단계 기준입니다. 사용 도구:
``scripts/build_windows.ps1`` (PyInstaller + ZIP), GitHub Actions workflow
``build-windows.yml``.

## Code

- [ ] `python -m pytest` 통과
- [ ] `python -m ruff check .` 통과
- [ ] CLI `sermonscript doctor` 통과
- [ ] GUI 가 깨끗한 Windows VM 에서 정상 실행
- [ ] 30분 분량 MP3 변환 + Export(txt/json/md/srt/vtt) 검증
- [ ] 편집기에서 edited_text 저장이 raw_text 를 덮어쓰지 않는지 확인
- [ ] 원문 대조 워크플로우: 교정 후보 생성 → 적용/무시 가능

## Security and Privacy

- [ ] 비공개 오디오 파일 미포함
- [ ] 트랜스크립트 미포함
- [ ] 기본 로그에 전체 transcript 가 남지 않음
- [ ] 캐시 삭제 동작 확인
- [ ] 최근 파일 기록을 사용자가 비활성화할 수 있음

## Licensing

- [ ] LICENSE 동봉
- [ ] THIRD_PARTY_NOTICES.md 가 실제 의존성과 일치
- [ ] FFmpeg 정책 (번들 미포함) 명시
- [ ] PySide6 LGPL 정책 명시
- [ ] 모델 파일 정책 (번들 미포함) 명시
- [ ] Binary artifact 구성 문서화 (PORTABLE-README.txt)

## Packaging

- [ ] PyInstaller 번들 생성: `scripts/build_windows.ps1`
- [ ] Portable ZIP 생성: `scripts/make_portable_zip.ps1`
- [ ] 산출물 파일명이 `SermonScript_Portable_{version}.zip` 패턴
- [ ] FFmpeg, 모델 파일이 번들에 포함되지 않았는지 확인
- [ ] GitHub Actions `build-windows.yml` 가 태그 푸시에서 정상 동작
- [ ] 앱 아이콘 포함 (선택)
- [ ] pyproject.toml 버전 업데이트
- [ ] CHANGELOG.md / HISTORY.md 업데이트

## Documentation

- [ ] README 업데이트
- [ ] 사용자 가이드 업데이트
- [ ] 스크린샷 갱신
- [ ] 알려진 제한 사항 문서화
- [ ] `docs/deferred-youtube-import.md` 로 YouTube 비포함 정책 명시
