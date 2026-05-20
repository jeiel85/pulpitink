# Integration fixtures (local-only)

이 디렉터리에는 통합 회귀 시나리오에서 사용하는 **실제 설교 원문/오디오** 가
들어갑니다. 모두 사용자 개인/저작권 콘텐츠이므로 `.gitignore` 가 이 디렉터리
전체(이 README 와 `.gitkeep` 제외) 를 무시합니다.

회귀 실행 시 다음 파일을 로컬에 준비하세요.

```text
tests/integration/fixtures/
├── sermon.md           # 원문 (docx → md 변환). ../extract_docx.py 사용 가능
├── sermon.mp3          # 원본 오디오 (선택, 보통은 D:\Media 등 외부 경로 사용)
└── user-dict.json      # 사용자 사전 (선택)
```

`sermon.md` 만 있어도 `--reference` 검증이 가능합니다.
원본 오디오는 보통 `--input` 인자에 절대경로로 직접 넘깁니다.
