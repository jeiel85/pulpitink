# SermonScript

SermonScript는 설교, 강의, 회의 녹음 파일을 로컬 PC에서 전처리하고 텍스트로 변환한 뒤, 사용자가 검수·편집·출력할 수 있도록 돕는 오픈소스 데스크톱 STT 프로그램입니다.

## 핵심 방향

- Local-first: 기본 변환은 사용자 PC에서 수행합니다.
- 원본 보존: 원본 오디오는 절대 수정하지 않습니다.
- 검수 중심: 100% 자동 원고보다 빠른 검수 워크플로우를 우선합니다.
- 설교 특화: 성경 구절, 신학 용어, 사용자 사전, 설교 원문 대조 기능을 제공합니다.
- 오픈소스 친화: 라이선스, 모델 출처, 외부 바이너리 사용 정책을 명확히 문서화합니다.

## 1차 기술 스택

| 영역 | 기술 |
|---|---|
| Language | Python 3.11+ |
| GUI | PySide6 |
| CLI | Typer |
| STT | faster-whisper |
| Audio | FFmpeg |
| Database | SQLite |
| Packaging | PyInstaller |
| Installer | Inno Setup 또는 NSIS |
| Test | pytest |
| Lint/Format | ruff |

## v1.0 범위

### 포함

- 로컬 오디오/비디오 파일 입력
- MP3, WAV, M4A, FLAC, OGG, MP4 지원
- FFmpeg 기반 오디오 분석 및 전처리
- faster-whisper 기반 STT
- TXT, Markdown, SRT, VTT, JSON, CSV export
- SQLite 작업 이력
- PySide6 GUI
- 타임스탬프 기반 편집기
- 사용자 사전
- 성경 구절 보정
- 설교 원문 대조 변환
- Windows Portable ZIP 및 설치 파일

### 제외

- YouTube URL 입력
- 온라인 다운로드
- 클라우드 동기화
- 실시간 녹음
- 모바일 앱
- 자동 요약
- 화자 분리
- 자동 업데이트 설치

YouTube URL 입력은 v1.5 또는 v2.0 후보 기능입니다. 이 기능은 사용자가 권리를 보유했거나 처리 권한이 있는 콘텐츠에 한해 사용하도록 경고 문구와 함께 별도 입력 소스 모듈로 구현합니다.

## 개발 시작

```bash
git clone https://github.com/jeiel85/sermonscript.git
cd sermonscript

python -m venv .venv
.venv\Scripts\activate

pip install -e ".[dev]"
sermonscript doctor
```

## 기본 CLI 목표

```bash
sermonscript doctor
sermonscript transcribe input.mp3 --language ko --model small --preset sermon --output ./exports
sermonscript jobs list
```

## 문서

- `docs/product-spec.md`
- `docs/architecture.md`
- `docs/audio-pipeline.md`
- `docs/transcription-pipeline.md`
- `docs/reference-alignment.md`
- `docs/youtube-import-deferred.md`
- `docs/vibe-coding-goals.md`
- `docs/release-roadmap.md`
- `docs/license-policy.md`

## 개인정보 원칙

SermonScript는 기본적으로 오디오 파일과 변환 텍스트를 외부 서버로 전송하지 않습니다. 모델 다운로드, 업데이트 확인, 사용자가 명시적으로 켠 온라인 기능에서만 네트워크가 사용될 수 있습니다.

## License

Apache-2.0
