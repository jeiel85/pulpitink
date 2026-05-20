# SermonScript

설교·강의·회의 녹음 파일을 로컬에서 STT(음성-자막) 변환하는 Windows 데스크톱 도구입니다.
모든 처리는 사용자 PC에서만 일어나며 외부 클라우드로 오디오를 전송하지 않습니다.

- 오프라인 동작: faster-whisper + FFmpeg
- CLI와 PySide6 GUI 동시 제공 (같은 core/service 계층 재사용)
- TXT / JSON / Markdown / SRT / VTT 동시 Export
- 한국어 설교 후처리: 성경 구절 정규화, 사용자 사전, 원문 대조 교정 후보
- SQLite 영속화로 작업 목록·세그먼트·교정 후보 보존

자세한 사용법은 [docs/user-guide.md](docs/user-guide.md) 를 참고하세요.

## 빠른 시작

### 사전 준비

- Python 3.11 이상
- FFmpeg (`ffmpeg` 가 PATH 에서 실행 가능해야 합니다)

### 설치

```powershell
git clone https://github.com/jeiel85/sermonscript.git
cd sermonscript
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[gui,reference,dev]"
```

`[gui]` 는 PySide6, `[reference]` 는 원문 대조용 rapidfuzz 를 함께 설치합니다.

### 환경 점검

```powershell
sermonscript doctor
```

Python 버전, OS, FFmpeg 설치, 앱 데이터 디렉터리 쓰기 권한을 한 번에 확인합니다.

### CLI 한 줄 변환

```powershell
sermonscript transcribe sermon.mp3 --language ko --model small --preset sermon `
  --format txt,json,md,srt,vtt,csv --output .\exports
```

원문 대조와 사용자 사전을 같이 쓰려면:

```powershell
sermonscript transcribe sermon.mp3 --reference sermon.md --user-dict my-dict.json
```

### GUI 실행

```powershell
python -m sermonscript.app.main
```

파일을 드래그 앤 드롭으로 추가하고, 언어·모델·전처리 프리셋·출력 폴더를 고른 뒤 변환을 시작합니다.
변환 후에는 같은 창의 편집기 탭에서 세그먼트를 수정하고 교정 후보를 적용/무시할 수 있습니다.

## 주요 기능

| 영역 | 기능 |
| --- | --- |
| 오디오 전처리 | FFmpeg 16kHz mono WAV 변환, 프리셋 `none / stt_basic / sermon / noisy` |
| STT | faster-whisper (모델 자동 다운로드, `tiny ~ large-v3`) |
| Export | TXT, JSON, Markdown, SRT, VTT, CSV 동시 출력 |
| 영속화 | SQLite (`jobs`, `segments`, `exports`, `reference_documents`, `alignment_pairs`, `correction_suggestions`) |
| 편집기 | 시간/텍스트/확인 컬럼, 검색·치환, 교정 후보 패널 |
| 후처리 | 기본 설교/성경 용어 사전 + 사용자 사전 + 성경 구절 정규화 (`로마서 일장 일절` → `로마서 1장 1절`) |
| 원문 대조 | 설교 원문에서 핵심 용어 추출 → 짧은 `initial_prompt` + 교정 후보 (pending) |
| 패키징 | PyInstaller 스펙, `scripts/build_windows.ps1`, Portable ZIP, GitHub Actions Windows 빌드 |

## 데이터가 저장되는 위치

`platformdirs` 가 계산한 사용자 디렉터리를 사용합니다. Windows 기준 기본 경로는:

- DB / 설정 / 모델 캐시: `%LOCALAPPDATA%\SermonScript\SermonScript\`
- 전처리 캐시 (`cache/jobs/<job_id>/processed.wav`): 작업 디렉터리 또는 `--cache-root`
- DB 경로 확인: `sermonscript db-path`

원본 오디오 파일은 절대 수정하지 않으며, STT 결과의 `raw_text` 도 덮어쓰지 않습니다. 사용자의 편집은 항상 `edited_text` 로만 저장됩니다.

## v1.0 범위 제외

다음 기능은 v1.0 에 포함되지 않습니다(향후 검토):

- YouTube URL 입력 / 온라인 다운로드 — [docs/deferred-youtube-import.md](docs/deferred-youtube-import.md)
- 화자 분리
- 클라우드 / 외부 API 송신

## 라이선스

- 본 프로젝트: Apache-2.0 ([LICENSE](LICENSE))
- 외부 의존성 고지: [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)
- 보안 신고: [SECURITY.md](SECURITY.md)
- 기여 가이드: [CONTRIBUTING.md](CONTRIBUTING.md)

## 더 읽을 거리

- 사용자 가이드: [docs/user-guide.md](docs/user-guide.md)
- 알려진 제한사항: [docs/known-limitations.md](docs/known-limitations.md)
- 릴리즈 체크리스트: [docs/release/release-checklist.md](docs/release/release-checklist.md)
- 로드맵: [docs/release/roadmap.md](docs/release/roadmap.md)
- 시스템 아키텍처: [docs/architecture/system-architecture.md](docs/architecture/system-architecture.md)
