# SermonScript 사용자 가이드

본 가이드는 SermonScript v0.3.x(예정 v1.0) 의 일반 사용자 워크플로우를 다룹니다.
프로그래머가 아니더라도 따라할 수 있도록 PowerShell 명령 위주로 안내합니다.

목차

1. [설치](#1-설치)
2. [환경 점검 (`doctor`)](#2-환경-점검-doctor)
3. [CLI 변환 워크플로우](#3-cli-변환-워크플로우)
4. [GUI 변환 워크플로우](#4-gui-변환-워크플로우)
5. [편집기 사용](#5-편집기-사용)
6. [원문 대조 변환](#6-원문-대조-변환)
7. [사용자 사전](#7-사용자-사전)
8. [작업 / 설정 / 모델 관리 CLI](#8-작업--설정--모델-관리-cli)
9. [데이터 저장 위치와 백업](#9-데이터-저장-위치와-백업)
10. [문제 해결](#10-문제-해결)
11. [알려진 제한사항](#11-알려진-제한사항)

---

## 1. 설치

### 1.1 사전 준비

| 항목 | 버전/요건 | 비고 |
| --- | --- | --- |
| Windows | 10 / 11 | macOS·Linux 도 동작하지만 패키징은 Windows 만 공식 지원 |
| Python | 3.11 이상 | `python --version` 으로 확인 |
| FFmpeg | 6.x 권장 | `ffmpeg -version` 이 동작해야 함. PATH 설정 필수 |

FFmpeg 가 설치되어 있지 않다면 [공식 빌드](https://www.gyan.dev/ffmpeg/builds/) 에서 받은 뒤
`bin` 폴더를 시스템 환경변수 `PATH` 에 추가하세요.

### 1.2 소스로 설치

```powershell
git clone https://github.com/jeiel85/sermonscript.git
cd sermonscript
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[gui,reference,dev]"
```

| Extra | 설치되는 것 | 언제 필요한가 |
| --- | --- | --- |
| `gui` | PySide6 | GUI 를 띄울 때 |
| `reference` | rapidfuzz | 원문 대조 매칭 품질 향상 (없으면 difflib 사용) |
| `dev` | pytest, ruff | 코드 변경/검증 시 |

설치 후 어디서든 `sermonscript` 명령이 동작합니다.

### 1.3 Portable ZIP 사용 (선택)

Python 설치가 어렵다면 릴리즈 페이지에서 `SermonScript_Portable_<version>.zip` 을 받아 임의의 폴더에 풀고
`SermonScript.exe` 를 실행하면 됩니다. FFmpeg 와 STT 모델은 번들에 포함되지 않으므로 별도로 준비해야 합니다.

---

## 2. 환경 점검 (`doctor`)

설치 후 가장 먼저 실행해 환경을 점검합니다.

```powershell
sermonscript doctor
```

확인 항목:

- Python 버전 (3.11+)
- 운영체제
- FFmpeg 설치 여부 (`ffmpeg`/`ffprobe`)
- 앱 데이터 / 캐시 / 로그 디렉터리 생성 및 쓰기 권한

`실패` 표시가 나오면 표 아래에 출력되는 “해결 힌트” 를 따라 조치한 뒤 다시 실행하세요.

---

## 3. CLI 변환 워크플로우

가장 단순한 변환:

```powershell
sermonscript transcribe sermon.mp3
```

기본값은 `--language ko --model small --preset sermon` 이며, `./exports/sermon.{txt,json,md,srt,vtt}` 를 생성하고 결과를 SQLite DB 에도 기록합니다.

자주 쓰는 옵션:

```powershell
sermonscript transcribe sermon.mp3 `
  --language ko `
  --model small `
  --preset sermon `
  --format txt,json,md,srt,vtt `
  --output .\exports `
  --device auto `
  --compute-type int8 `
  --beam-size 5
```

### 3.1 전처리 프리셋

| 프리셋 | 용도 |
| --- | --- |
| `none` | 16kHz mono 변환만 수행. 이미 깨끗한 wav 에 추천 |
| `stt_basic` | 보편적 다운믹스 + loudnorm |
| `sermon` (기본) | 설교 녹음용. 저역 컷 + 적당한 다이내믹 정리 |
| `noisy` | 휴대폰/주변소음 녹음. 노이즈 게이트와 강한 정규화 |

프리셋 목록은 다음 명령으로 확인:

```powershell
sermonscript presets
```

### 3.2 모델 선택

```powershell
sermonscript models list
sermonscript models cache-dir
```

| 모델 | 메모리 | 속도 / 품질 |
| --- | --- | --- |
| `tiny` / `base` | 매우 작음 | 빠르지만 한국어 정확도 낮음 |
| `small` (기본) | 보통 | 일반 데스크톱에서 권장 |
| `medium` | 큼 | CPU 사용 시 느리지만 정확 |
| `large-v3` | 매우 큼 | GPU(CUDA, `--device cuda --compute-type float16`) 권장 |

모델 파일은 최초 사용 시 자동으로 다운로드되며 사용자 데이터 디렉터리 (`<data_dir>/models`) 에 캐시됩니다.

### 3.3 출력 포맷

`--format` 은 콤마로 구분합니다. 지원: `txt`, `json`, `md`, `srt`, `vtt`.
출력 파일명은 입력 파일의 stem 을 따릅니다.

---

## 4. GUI 변환 워크플로우

```powershell
python -m sermonscript.app.main
```

1. 좌측 패널에 파일을 드래그 앤 드롭하거나 “파일 추가” 로 선택합니다.
2. 상단의 언어 / 모델 / 전처리 프리셋 / 출력 폴더를 확인합니다 (설정의 기본값이 미리 채워집니다).
3. “변환 시작” 을 누릅니다. 변환은 워커 스레드에서 실행되어 UI 가 멈추지 않습니다.
4. 진행률 / 로그 영역에서 단계별 상태를 확인합니다.
5. 변환이 끝나면 결과 미리보기 패널에 텍스트가 표시되고, 같은 창의 “편집기” 탭에서 세그먼트를 열 수 있습니다.

GUI 가 시작하지 않고 `PySide6가 설치되어 있지 않습니다` 안내가 나오면 `pip install "sermonscript[gui]"` 를 실행하세요.

---

## 5. 편집기 사용

편집기는 작업 단위(job)로 동작하며 모든 편집은 즉시 SQLite 에 저장됩니다.

핵심 원칙:

- `raw_text` (STT 원본) 은 절대 수정되지 않습니다.
- 사용자의 직접 편집은 `edited_text` 에 저장됩니다.
- 후처리 결과는 `clean_text` 에 들어갑니다.
- Export 는 항상 `edited_text > clean_text > raw_text` 우선순위로 사용합니다.

기능 요약:

- 시작/종료 시간, 확인(`needs_review`), 텍스트 컬럼 표시.
- 셀을 더블클릭해 텍스트 편집 → 저장 시 `edited_text` 갱신.
- 검색 / 치환: 일치한 세그먼트의 `edited_text` 만 갱신합니다.
- 확인 필요 토글: STT 신뢰도(avg_logprob, no_speech_prob) 가 낮으면 자동으로 표시되며, 사용자가 직접 켜고 끌 수 있습니다.
- 우측 패널에 “교정 후보(pending)” 가 표시되고 적용/무시 버튼이 있습니다.

---

## 6. 원문 대조 변환

설교 원문(TXT 또는 Markdown) 이 있으면 함께 입력해 STT 정확도를 끌어올리고 교정 후보를 자동 생성할 수 있습니다.

```powershell
sermonscript transcribe sermon.mp3 --reference sermon.md --language ko
```

내부 동작:

1. 원문에서 제목, 성경 본문, 핵심 한국어 용어, 고유명사 후보를 추출합니다.
2. faster-whisper `initial_prompt` 를 핵심 용어 위주 짧은 문자열(≤ 280자)로 생성합니다. 원문 전체를 넣지 않는 이유는 모델이 실제 발화에 없는 문장을 환각(hallucinate) 하지 않도록 하기 위함입니다.
3. STT 세그먼트와 원문 문단을 유사도 기반으로 정렬하고, 성경 구절 / 사용자 사전 / 고유명사 매칭이 발견되면 `pending` 교정 후보로 저장합니다.

원문이 실제 발화와 다른 경우 raw_text(실제 발화) 가 우선이며, 사용자가 편집기에서 직접 교정 후보를 검토합니다.

CLI 로 교정 후보를 확인 / 적용 / 무시:

```powershell
sermonscript corrections list <job-id>
sermonscript corrections apply <suggestion-id>
sermonscript corrections ignore <suggestion-id>
```

`apply` 는 해당 세그먼트의 `edited_text` 만 갱신합니다. `raw_text` 는 보존됩니다.

---

## 7. 사용자 사전

사용자 사전은 “표준 표기 → 자주 나오는 잘못된 표기” 의 매핑입니다.

JSON 예시 (`my-dict.json`):

```json
{
  "예수 그리스도": ["예수그리스도", "예수 그리스도님"],
  "고린도전서":   ["고린도 전서"],
  "은혜": []
}
```

- 값이 빈 배열이어도 됩니다. 이때는 후처리에서 자동 치환은 일어나지 않지만, 원문 대조의 고유명사 후보로 사용됩니다.
- 기본 설교/성경 용어 사전 위에 누적 적용됩니다.

CLI 에서 적용:

```powershell
sermonscript transcribe sermon.mp3 --user-dict .\my-dict.json
```

---

## 8. 작업 / 설정 / 모델 관리 CLI

### 8.1 작업 (`jobs`)

```powershell
sermonscript jobs list --limit 20
sermonscript jobs show <job-id>
sermonscript jobs export <job-id> --format md,srt --output .\re-exports
```

`jobs export` 는 저장된 세그먼트를 다시 export 합니다. STT 를 재실행하지 않으므로 빠르고, 편집기에서 수정한 `edited_text` 가 반영됩니다.

### 8.2 설정 (`settings`)

```powershell
sermonscript settings show
sermonscript settings set language ko
sermonscript settings set model small
sermonscript settings set preset sermon
sermonscript settings set output_dir D:\sermons\exports
sermonscript settings set model_cache_dir D:\sermons\models
```

설정은 JSON 으로 저장되며 경로는 `settings show` 가 알려줍니다.

### 8.3 모델 (`models`)

```powershell
sermonscript models list
sermonscript models cache-dir
```

### 8.4 DB 경로 확인

```powershell
sermonscript db-path
```

---

## 9. 데이터 저장 위치와 백업

Windows 기본 경로 (사용자 디렉터리 안):

| 종류 | 경로 |
| --- | --- |
| DB / 설정 / 모델 캐시 | `%LOCALAPPDATA%\SermonScript\SermonScript\` |
| 로그 | `%LOCALAPPDATA%\SermonScript\SermonScript\Logs\` 또는 platform-log dir |
| 전처리 캐시 (processed.wav) | 작업 디렉터리의 `cache\jobs\<job_id>\` 또는 `--cache-root` |
| Export 결과 | `--output` 으로 지정한 폴더 (CLI) / 설정의 `output_dir` |

백업이 필요한 파일:

- `SermonScript.sqlite3` — 모든 작업/세그먼트/교정 기록
- `settings.json` — 사용자 설정
- 필요하다면 모델 캐시(`models/`) — 다시 다운로드받아도 무방하지만 시간이 걸립니다

`cache/jobs/<job_id>/processed.wav` 는 언제든 삭제해도 됩니다. 다음 변환 시 다시 생성됩니다.

---

## 10. 문제 해결

| 증상 | 원인 / 해결 |
| --- | --- |
| `FFmpeg 가 설치되어 있지 않습니다` | PATH 에 `ffmpeg` 추가 후 새 PowerShell 창을 열고 `ffmpeg -version` 확인 |
| `PySide6가 설치되어 있지 않습니다` | `pip install "sermonscript[gui]"` |
| CUDA 모델이 메모리 부족으로 실패 | `--device cpu --compute-type int8` 로 다운그레이드하거나 모델 크기를 낮춤 |
| 변환이 매우 느림 | 작은 모델로 시도(`--model small`), VAD 필터 켜기(기본값), `--preset sermon` 사용 |
| 잘못된 단어가 반복 | 사용자 사전에 등록 후 `corrections apply` 또는 편집기에서 직접 수정 |
| 결과가 비어 있음 | 원본의 음량이 너무 작거나 묵음이 많을 수 있음. `--preset noisy` 시도 |
| 교정 후보가 너무 많음 | 원문이 실제 발화와 다르면 raw_text 가 우선이므로 모두 적용하지 말고 검토 후 ignore |

자세한 로그가 필요하면 `--verbose` 를 사용합니다:

```powershell
sermonscript --verbose transcribe sermon.mp3
```

---

## 11. 알려진 제한사항

자세한 목록은 [docs/known-limitations.md](known-limitations.md) 를 참고하세요. 요약:

- v1.0 은 로컬 오디오/비디오 파일만 지원합니다. YouTube URL 입력과 온라인 다운로드는 의도적으로 제외했습니다 ([docs/deferred-youtube-import.md](deferred-youtube-import.md)).
- 화자 분리(diarization) 는 포함되지 않습니다.
- FFmpeg / STT 모델은 패키징에 번들되지 않습니다. 사용자가 별도로 준비합니다.
- Windows 패키징(Portable ZIP) 만 공식 지원합니다. macOS·Linux 에서는 소스 설치로 사용하세요.
- PySide6 는 LGPL 입니다. 재배포 시 라이선스 정책을 검토하세요 ([THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md)).
