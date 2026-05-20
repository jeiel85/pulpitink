# PulpitInk 3-Goal Vibe Coding Prompts — Fixed

이 묶음은 `/goal` 입력 제한 4000자에 맞춰 Goal 2를 축약한 버전입니다.

## Goal 구성

1. 저장소 초기화 + CLI 코어 + 오디오 전처리/STT/Export
2. SQLite/설정/모델 관리 + PySide6 GUI + 작업 큐
3. 편집기/후처리/사용자 사전 + 원문 대조 변환 + 릴리즈 패키징

## 수정 사항

- Goal 2 본문을 4000자 이하로 축약했습니다.
- 기능 범위는 유지하되 긴 설명과 중복 문장을 줄였습니다.
- YouTube URL 입력은 계속 v1.0 제외 기능으로 유지했습니다.

## 권장 사용법

각 Goal 본문을 `/goal` 입력칸에 넣고, 필요하면 `common-tail-instruction.md`의 공통 규칙을 별도 메시지로 추가하세요.


# Goal 1 — 저장소 초기화 + CLI 코어 + 오디오 전처리/STT/Export

```text
/goal
PulpitInk의 초기 저장소, CLI 코어, 오디오 전처리, STT, Export 파이프라인을 구현한다.

배경:
PulpitInk는 Windows PC용 오픈소스 설교 녹음 STT 프로그램이다. v1.0은 로컬 오디오/비디오 파일만 지원하며 YouTube URL 입력, 온라인 다운로드, 클라우드 기능은 제외한다.

기술 스택:
Python 3.11+, Typer, faster-whisper, FFmpeg, pytest, ruff, pyproject.toml.

구현:
1. pyproject.toml 기반 프로젝트 구조를 만든다.
2. src/pulpitink 아래 app, cli, core/audio, core/transcription, core/export, core/postprocess, core/reference, services, storage, ui 구조를 만든다.
3. Typer CLI와 PulpitInk doctor 명령을 구현한다.
4. doctor는 Python 버전, OS, FFmpeg 설치 여부, 쓰기 권한, 앱 데이터 경로 생성을 확인한다.
5. PulpitInk transcribe 명령을 구현한다.
6. 지원 입력: mp3, wav, m4a, aac, flac, ogg, mp4.
7. FFmpegRunner로 16kHz mono WAV 전처리를 수행한다.
8. 전처리 프리셋 none, stt_basic, sermon, noisy를 구현한다. 기본값은 sermon.
9. 원본 파일은 절대 수정하지 않고 cache/jobs/{job_id}/processed.wav를 생성한다.
10. TranscriptionEngine 인터페이스와 FasterWhisperEngine 구현체를 만든다.
11. TranscriptSegment는 start, end, text, avg_logprob, no_speech_prob를 포함한다.
12. TXT, JSON, Markdown, SRT, VTT exporter를 구현한다.
13. CLI 예: PulpitInk transcribe input.mp3 --language ko --model small --preset sermon --output ./exports --format txt,json
14. README, HISTORY, CHANGELOG를 갱신한다.
15. pytest와 ruff 설정 및 기본 테스트를 추가한다.

완료 조건:
- pip install -e . 가능
- PulpitInk doctor 실행 가능
- PulpitInk transcribe로 TXT/JSON/MD/SRT/VTT 생성 가능
- processed.wav 생성
- pytest 통과
- ruff check 통과

제외:
GUI, SQLite 저장, 사용자 사전, 원문 대조, YouTube URL 입력, 온라인 다운로드, 클라우드/API 기능.

원칙:
core 로직은 CLI와 분리한다. 모델 파일, 오디오 샘플, 큰 바이너리는 커밋하지 않는다. 작업 후 문서와 이력을 갱신한다.
```


# Goal 2 — SQLite/설정/모델 관리 + PySide6 GUI + 작업 큐

```text
/goal
PulpitInk의 로컬 DB, 설정, 모델 관리, PySide6 GUI, 작업 큐를 구현한다.

배경:
Goal 1에서 CLI transcribe, FFmpeg 전처리, faster-whisper STT, Export가 동작한다고 가정한다. 이번 목표는 일반 사용자가 GUI에서 파일을 추가하고 변환할 수 있는 데스크톱 앱 기반을 만드는 것이다.

기술 스택:
SQLite, platformdirs, Typer, PySide6, QThread 또는 QThreadPool, pytest, ruff.

구현:
1. storage/database.py를 만들고 platformdirs로 앱 데이터 경로를 계산한다.
2. SQLite DB를 초기화한다.
3. jobs, segments, exports 테이블을 만든다.
4. jobs 필드: id, source_path, title, duration_sec, language, model_name, engine, preset, status, error_message, created_at, updated_at.
5. segments 필드: id, job_id, start_sec, end_sec, raw_text, clean_text, edited_text, avg_logprob, no_speech_prob, needs_review, speaker.
6. exports 필드: id, job_id, format, output_path, created_at.
7. transcribe 실행 시 job, segment, export 기록을 저장한다.
8. 실패 작업은 status=failed와 error_message를 저장한다.
9. jobs list/show/export CLI를 추가한다.
10. settings service를 만든다. 기본 언어, 모델, 전처리 프리셋, 출력 폴더, 모델 캐시 경로를 저장한다.
11. settings show/set CLI를 추가한다.
12. model service를 만들고 지원 모델 목록과 캐시 경로를 표시한다.
13. models list/cache-dir CLI를 추가한다.
14. 테스트는 임시 DB를 사용하고 실제 사용자 DB를 건드리지 않는다.
15. python -m pulpitink.app.main으로 PySide6 GUI를 실행한다.
16. GUI에는 파일 추가, 드래그 앤 드롭, 작업 목록, 언어/모델/프리셋 선택, 출력 폴더, 변환 시작, 진행률, 로그, 결과 미리보기를 둔다.
17. GUI 변환은 기존 core/service 파이프라인을 재사용한다.
18. 긴 작업은 worker thread에서 실행해 UI가 멈추지 않게 한다.
19. 최근 작업을 DB에서 불러와 GUI에 표시한다.
20. HISTORY.md와 CHANGELOG.md를 갱신한다.

완료 조건:
- transcribe 후 DB에 job/segments/exports 저장
- jobs/settings/models CLI 실행 가능
- GUI 실행 가능
- GUI에서 파일 추가 및 변환 가능
- 변환 중 UI가 멈추지 않음
- 결과 미리보기 가능
- pytest 통과
- ruff check 통과

제외:
고급 편집기, 오디오 싱크 플레이어, 원문 대조, 화자 분리, YouTube URL 입력, 온라인 다운로드, 설치 파일 생성.

원칙:
raw_text는 덮어쓰지 않는다. UI와 core 로직을 분리한다. 사용자 데이터 손실 가능성이 있는 DB 변경은 migration 계획을 남긴다.
```


# Goal 3 — 편집기/후처리/사용자 사전 + 원문 대조 변환 + 릴리즈 패키징

```text
/goal
PulpitInk의 타임스탬프 편집기, 설교 후처리, 사용자 사전, 원문 대조 변환, Windows 릴리즈 패키징을 구현한다.

배경:
Goal 2까지 GUI에서 로컬 파일을 추가하고 STT 변환 결과를 볼 수 있다고 가정한다. 이번 목표는 검수/교정 워크플로우와 배포 기반을 완성하는 것이다.

구현 A — 편집기/후처리:
1. transcript_editor.py를 구현한다.
2. 세그먼트를 시작 시간, 종료 시간, 텍스트, 확인 필요 여부와 함께 표시한다.
3. 사용자가 텍스트를 수정하면 edited_text에 저장한다.
4. raw_text는 절대 덮어쓰지 않는다.
5. 후처리 결과는 clean_text에 저장한다.
6. Export는 edited_text > clean_text > raw_text 순서로 사용한다.
7. 검색, 치환, needs_review 표시를 구현한다.
8. avg_logprob 또는 no_speech_prob 기반 확인 필요 후보를 표시한다.
9. 사용자 사전과 기본 설교/성경 용어 사전을 구현한다.
10. 성경 구절 보정: 로마서 일장 일절 → 로마서 1장 1절, 고린도 전서 → 고린도전서.

구현 B — 원문 대조:
1. TXT/Markdown 설교 원문을 입력받는다.
2. reference_documents, alignment_pairs, correction_suggestions 테이블을 추가한다.
3. 원문에서 제목, 성경 본문, 주요 용어, 고유명사 후보를 추출한다.
4. faster-whisper initial_prompt를 생성하되 원문 전체는 넣지 않고 핵심 용어만 짧게 넣는다.
5. STT 세그먼트와 원문 문단을 유사도 기반으로 정렬한다.
6. 성경구절, 고유명사, 사용자 사전 기반 교정 후보를 만든다.
7. 일반 문장은 자동 교체하지 않는다.
8. 교정 후보는 pending으로 저장하고 GUI에서 적용/무시할 수 있게 한다.
9. 적용한 교정은 edited_text에 반영한다.
10. CLI 옵션 예: PulpitInk transcribe sermon.mp3 --reference sermon.md --language ko

구현 C — 릴리즈/문서:
1. YouTube URL 입력은 v1.0 제외 기능으로 docs/deferred-youtube-import.md에만 문서화한다.
2. PyInstaller 설정과 scripts/build_windows.ps1을 추가한다.
3. Portable ZIP 생성 스크립트를 만든다.
4. GitHub Actions Windows 빌드 workflow를 추가한다.
5. 산출물 이름은 PulpitInk_Portable_{version}.zip 형식을 사용한다.
6. FFmpeg와 모델 파일은 기본 번들에 포함하지 않는다.
7. THIRD_PARTY_NOTICES.md와 docs/release-checklist.md를 갱신한다.
8. HISTORY.md와 CHANGELOG.md를 갱신한다.

완료 조건:
- 세그먼트 편집 및 edited_text 저장 가능
- 후처리와 사용자 사전 적용 가능
- 원문 대조 교정 후보 생성 및 적용/무시 가능
- YouTube 기능은 문서화만 되고 구현되지 않음
- Portable ZIP 빌드 스크립트 존재
- pytest 통과
- ruff check 통과

원칙:
실제 발화가 원문과 다르면 실제 발화를 보존한다. 자동 교정은 보수적으로 적용한다. 온라인 다운로드 기능은 구현하지 않는다.
```


# Common Tail Instruction

```text
공통 작업 규칙:
- 작업 시작 전 AGENTS.md, README.md, docs/를 확인한다.
- 작업 전 git status를 확인하고 기존 변경을 덮어쓰지 않는다.
- 이번 Goal 범위 밖 기능은 구현하지 말고 후속 작업으로 HISTORY.md 또는 docs/roadmap.md에 기록한다.
- 코드 변경 시 관련 문서도 함께 갱신한다.
- 사용자에게 보이는 메시지는 기본적으로 한국어로 작성한다.
- core 로직은 UI와 분리한다.
- CLI와 GUI가 같은 core/service 계층을 재사용하게 한다.
- 원본 오디오 파일은 절대 수정하지 않는다.
- raw_text는 절대 덮어쓰지 않는다.
- edited_text는 사용자 수정본으로만 사용한다.
- 모델 파일, 오디오 샘플, 큰 바이너리, 개인정보성 파일은 Git에 커밋하지 않는다.
- YouTube URL 입력, 온라인 다운로드, 클라우드 기능은 v1.0 범위에서 제외한다.
- 외부 의존성을 추가할 때는 라이선스와 필요성을 확인하고 HISTORY.md에 이유를 기록한다.
- 완료 전 ruff check와 pytest를 실행한다.
- 실행하지 못한 검증은 성공했다고 쓰지 말고 이유를 기록한다.
- 작업 완료 후 변경 파일, 검증 결과, 후속 작업을 요약한다.
```
