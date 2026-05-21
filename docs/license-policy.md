# License Policy

## 1. 앱 자체 라이선스

권장 라이선스:

```text
Apache-2.0
```

## 2. 주요 의존성 정책

| 구성요소 | 정책 |
|---|---|
| OpenAI Whisper | LICENSE 고지 필요 |
| faster-whisper | LICENSE 고지 필요 |
| CTranslate2 | LICENSE 고지 필요 |
| FFmpeg | 포함 여부와 빌드 라이선스 확인 필요 |
| PySide6 | LGPL/GPL/Commercial 조건 확인 필요 |
| PyInstaller | 라이선스 예외 조항 확인 필요 |
| Silero VAD | 선택 의존성, LICENSE 확인 필요 |
| RapidFuzz | 원문 대조 기능에서 사용 시 LICENSE 확인 필요 |

## 3. 저장소 정책

- 모델 파일은 저장소에 커밋하지 않습니다.
- FFmpeg 바이너리는 기본 저장소에 포함하지 않습니다.
- 실제 설교 녹음, 개인정보성 오디오, 교회 내부 자료는 테스트 fixture로 커밋하지 않습니다.
- 외부 모델을 지원 목록에 추가할 때 모델 카드와 라이선스를 확인합니다.
- `THIRD_PARTY_NOTICES.md`를 릴리즈 패키지에 포함합니다.

## 4. YouTube 기능 정책

YouTube URL 입력 기능은 v0.4.4 이후 고지 동의 기반 opt-in 기능으로 제공됩니다.

유지 조건:

- 사용자가 권리를 보유했거나 처리 권한이 있는 콘텐츠에 한해 사용하도록 경고합니다.
- 다운로드 목적 기능으로 홍보하지 않습니다.
- STT core와 분리된 입력 소스/다운로드 계층으로 유지합니다.
- 법적 책임 문구를 UI와 문서에 표시합니다.
- DRM 우회, 접근 제한 우회, 클라우드 동기화, 일반 온라인 다운로드 기능으로 확장하지 않습니다.
