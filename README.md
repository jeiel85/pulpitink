# pulpit-ink

설교, 강의, 회의 녹음 파일을 로컬 PC에서 전처리하고 텍스트로 변환한 뒤 검수, 편집, 출력까지 지원하는 Windows 데스크톱 STT 도구입니다.

[![Test](https://github.com/jeiel85/pulpit-ink/actions/workflows/test.yml/badge.svg)](https://github.com/jeiel85/pulpit-ink/actions/workflows/test.yml)
[![Build Windows Portable](https://github.com/jeiel85/pulpit-ink/actions/workflows/build-windows.yml/badge.svg)](https://github.com/jeiel85/pulpit-ink/actions/workflows/build-windows.yml)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache--2.0-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-3776AB.svg)](pyproject.toml)

- 공식 랜딩 페이지: <https://jeiel85.github.io/pulpit-ink/>
- 릴리즈 다운로드: <https://github.com/jeiel85/pulpit-ink/releases>
- 사용자 가이드: [docs/user-guide.md](docs/user-guide.md)

## 개요

pulpit-ink는 긴 한국어 설교 녹음처럼 검수가 필요한 STT 작업을 로컬 우선 방식으로 처리합니다. 오디오와 변환 텍스트는 기본적으로 외부 서버로 전송하지 않으며, 원본 오디오와 STT 원문(`raw_text`)을 보존합니다. 사용자가 고친 내용은 별도의 `edited_text`로 저장됩니다.

현재 입력 범위는 로컬 파일과 사용자가 권리를 확인한 YouTube URL입니다. YouTube 입력은 저작권 고지 동의 후 `yt-dlp`로 로컬 임시 오디오를 만든 뒤 기존 STT 파이프라인에 전달합니다. 일반 온라인 다운로드, 클라우드 동기화, 실시간 녹음은 v1.0 범위에 포함되지 않습니다.

## 주요 기능

| 영역 | 내용 |
| --- | --- |
| 입력 | `mp3`, `wav`, `m4a`, `aac`, `flac`, `ogg`, `mp4` 등 로컬 파일, YouTube URL(고지 동의 후) |
| STT | faster-whisper 기반 변환, `tiny`부터 `large-v3`까지 모델 선택 |
| 전처리 | FFmpeg 16kHz mono WAV 변환, `none`, `stt_basic`, `sermon`, `noisy` 프리셋 |
| GUI | PySide6 데스크톱 앱, 파일 추가, 진행 로그, 최근 작업, 편집기 탭 |
| CLI | 변환, 환경 점검, 작업 조회/export, 설정, 모델 캐시 확인 |
| 편집 | 세그먼트별 타임스탬프/텍스트 편집, 검색, 치환, 확인 필요 표시 |
| 후처리 | 성경 구절 정규화, 사용자 사전, 원문 대조, 한국어 Jamo fuzzy 교정 후보 |
| 화자 | 무음구간 갭 기반 Heuristic 화자 태그와 편집기 내 화자 열 수정 |
| 출력 | TXT, JSON, Markdown, SRT, VTT, CSV |
| 저장 | SQLite 기반 작업, 세그먼트, export, 원문 대조, 교정 후보 기록 |
| 배포 | PyInstaller Windows Portable ZIP, 태그 기반 GitHub Release 자동화 |

## 설치

### 요구 사항

- Windows 10/11 권장
- Python 3.11 이상
- FFmpeg (`ffmpeg`, `ffprobe`가 PATH에서 실행 가능해야 함)

### 소스 설치

```powershell
git clone https://github.com/jeiel85/pulpit-ink.git
cd pulpit-ink
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[gui,reference,dev]"
```

Extra 설명:

- `gui`: PySide6 GUI 실행에 필요
- `reference`: 원문 대조 품질 향상용 rapidfuzz 설치
- `dev`: pytest, ruff 등 개발/검증 도구 설치

### Portable ZIP

릴리즈 페이지에서 `PulpitInk_Portable_<version>.zip`을 받을 수 있습니다. FFmpeg와 STT 모델은 기본 번들에 포함되지 않으므로 사용 환경에서 별도로 준비해야 합니다.

## 사용

### 환경 점검

```powershell
pulpit-ink doctor
```

### GUI 실행

```powershell
python -m pulpit_ink.app.main
```

파일을 추가하고 언어, 모델, 전처리 프리셋, 출력 폴더를 선택한 뒤 변환을 시작합니다. 변환은 worker thread에서 실행되어 UI가 멈추지 않습니다.

### CLI 변환

```powershell
pulpit-ink transcribe sermon.mp3 --language ko --model small --preset sermon `
  --format txt,json,md,srt,vtt,csv --output .\exports
```

원문 대조와 사용자 사전:

```powershell
pulpit-ink transcribe sermon.mp3 --reference sermon.md --user-dict my-dict.json
```

교정 후보 확인/적용/무시:

```powershell
pulpit-ink corrections list <job-id>
pulpit-ink corrections apply <suggestion-id>
pulpit-ink corrections ignore <suggestion-id>
```

## 데이터 저장 위치

Windows 기본 위치:

- DB / 설정 / 모델 캐시: `%LOCALAPPDATA%\PulpitInk\PulpitInk\`
- 전처리 캐시: 작업 디렉터리 또는 `--cache-root` 아래 `cache/jobs/<job_id>/`
- DB 경로 확인: `pulpit-ink db-path`

데이터 원칙:

- 원본 오디오 파일은 수정하지 않습니다.
- `raw_text`는 덮어쓰지 않습니다.
- 사용자 편집은 `edited_text`에 저장합니다.
- 모델 파일, 큰 바이너리, 개인정보성 오디오 파일은 저장소에 커밋하지 않습니다.

## 개발

자주 쓰는 검증 명령:

```powershell
python -m ruff check .
python -m pytest
python -m pulpit_ink.cli.main doctor
```

Windows Portable ZIP 로컬 빌드:

```powershell
.\scripts\build_windows.ps1
```

릴리즈는 `v*` 태그 push로 트리거됩니다. GitHub Actions가 Portable ZIP과 `SHA256SUMS.txt`를 만들고 GitHub Release에 첨부합니다.

## 프로젝트 구조

```text
src/pulpit_ink/
  app/              GUI 진입점
  cli/              Typer CLI
  core/             오디오, STT, export, 후처리, 원문 대조 로직
  services/         설정, 모델, 변환 orchestration
  storage/          SQLite DB와 repository 계층
  ui/               PySide6 화면과 worker
tests/              단위/회귀 테스트
docs/               제품 문서, 사용자 가이드, GitHub Pages 랜딩
scripts/            Windows 빌드/패키징 스크립트
```

## v1.0 범위 제외

- 클라우드 동기화 / 외부 API 송신
- 일반 온라인 다운로드 / DRM 또는 접근 제한 우회
- 실시간 마이크 녹음
- 자동 요약
- 자동 업데이트 설치

## 문서

- [사용자 가이드](docs/user-guide.md)
- [제품 명세](docs/product-spec.md)
- [알려진 제한사항](docs/known-limitations.md)
- [릴리즈 체크리스트](docs/release/release-checklist.md)
- [로드맵 작업 목록](docs/roadmap-tasks.md)
- [시스템 아키텍처](docs/architecture/system-architecture.md)
- [의사결정 기록](docs/decision-log.md)

## 라이선스와 보안

- 라이선스: Apache-2.0 ([LICENSE](LICENSE))
- 외부 의존성 고지: [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)
- 보안 신고: [SECURITY.md](SECURITY.md)
- 기여 가이드: [CONTRIBUTING.md](CONTRIBUTING.md)
