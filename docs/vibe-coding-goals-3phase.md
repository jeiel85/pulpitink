# SermonScript 바이브 코딩 `/goal` 프롬프트 묶음 — 3단계 대형 Goal 버전

이 문서는 SermonScript를 바이브 코딩 에이전트로 개발할 때 사용할 `/goal` 프롬프트를 **3개의 큰 작업 단위**로 재구성한 버전입니다.

기존 6단계 Goal보다 각 단계의 범위를 크게 잡았습니다. 한 Goal은 에이전트가 약 2~3시간 이상 집중해서 진행할 수 있는 분량을 목표로 합니다.

---

## 전체 구성

```text
Goal 1. 저장소 초기화 + CLI 코어 + 오디오 전처리/STT/Export
Goal 2. SQLite/설정/모델 관리 + PySide6 GUI + 작업 큐
Goal 3. 편집기/후처리/사용자 사전 + 원문 대조 변환 + 릴리즈 패키징
```

각 Goal은 독립적인 개발 세션으로 사용할 수 있습니다. 단, 순서는 반드시 1 → 2 → 3을 권장합니다.

---

# Goal 1 — 저장소 초기화 + CLI 코어 + 오디오 전처리/STT/Export

```text
/goal
SermonScript 프로젝트의 초기 저장소 구조, CLI 기반 코어, 오디오 전처리, STT 변환, Export 파이프라인을 한 번에 구현한다.

배경:
SermonScript는 Windows PC용 오픈소스 설교 녹음 STT 프로그램이다.
기본 목표는 로컬 오디오/비디오 파일을 입력받아 전처리하고, faster-whisper로 텍스트 변환한 뒤 TXT/JSON/Markdown/SRT/VTT로 내보내는 것이다.
첨부된 설계서 묶음과 AGENTS.md 규칙을 기준으로 개발한다.
v1.0은 로컬 파일 기반 STT만 지원한다.
YouTube URL 입력, 온라인 다운로드, 클라우드 기능은 v1.0 범위에서 제외한다.

이번 Goal의 목표:
GitHub Public 저장소로 개발 가능한 프로젝트 골격을 만들고, GUI 없이 CLI에서 실제 오디오 파일을 변환할 수 있는 핵심 파이프라인을 완성한다.

기술 스택:
- Python 3.11+
- Typer CLI
- faster-whisper
- FFmpeg
- pytest
- ruff
- pyproject.toml 기반 패키징
- Windows 10/11 1차 대상

구현 요구사항 A: 프로젝트 구조
1. pyproject.toml 기반 Python 프로젝트 구조를 만든다.
2. src/sermonscript 패키지 구조를 만든다.
3. 다음 디렉터리 구조를 준비한다.
   - app/
   - cli/
   - core/audio/
   - core/transcription/
   - core/export/
   - core/postprocess/
   - core/reference/
   - services/
   - storage/
   - ui/
4. Typer 기반 CLI 진입점을 만든다.
5. platformdirs를 사용해 앱 데이터 경로를 계산한다.
6. logging 기본 설정을 만든다.
7. 공통 예외 클래스를 만든다.
8. .gitignore를 Python/Windows/PyInstaller/모델 캐시 기준으로 정리한다.
9. GitHub Actions test workflow를 추가한다.
10. README.md의 개발 실행 방법을 실제 명령과 일치시킨다.
11. AGENTS.md는 SermonScript 프로젝트 설정값에 맞게 유지한다.

구현 요구사항 B: doctor 명령
1. sermonscript doctor 명령을 구현한다.
2. doctor 명령은 다음을 확인한다.
   - Python 버전
   - OS 정보
   - FFmpeg 설치 여부
   - 현재 작업 디렉터리 쓰기 권한
   - 앱 데이터 디렉터리 생성 가능 여부
3. 사용자가 이해할 수 있는 한국어 메시지를 출력한다.
4. 실패 항목은 원인과 해결 힌트를 함께 표시한다.

구현 요구사항 C: transcribe CLI
1. sermonscript transcribe 명령을 추가한다.
2. 명령 형식은 아래를 지원한다.
   sermonscript transcribe input.mp3 --language ko --model small --preset sermon --output ./exports --format txt,json,md,srt,vtt
3. 입력 파일 존재 여부를 검증한다.
4. 지원 확장자는 다음으로 한다.
   - .mp3
   - .wav
   - .m4a
   - .aac
   - .flac
   - .ogg
   - .mp4
5. 원본 파일은 절대 수정하지 않는다.
6. 변환 작업마다 job_id를 생성한다.
7. 전처리 결과는 cache/jobs/{job_id}/processed.wav에 저장한다.

구현 요구사항 D: FFmpeg 오디오 전처리
1. FFmpegRunner를 구현한다.
2. FFmpeg 설치 여부와 실행 가능 여부를 검사한다.
3. 입력 파일을 16kHz mono WAV로 변환한다.
4. 전처리 프리셋을 구현한다.
   - none: 최소 변환
   - stt_basic: highpass, lowpass, loudnorm
   - sermon: 설교 녹음용 균형 프리셋
   - noisy: 잡음 많은 녹음용 프리셋
5. 기본 프리셋은 sermon으로 한다.
6. FFmpeg 실패 시 stderr를 정리해서 사용자에게 보여준다.
7. 과한 전처리가 기본값이 되지 않도록 한다.
8. 전처리 값은 core/audio/enhancement_presets.py에서 중앙 관리한다.

구현 요구사항 E: STT 엔진
1. TranscriptionEngine 인터페이스를 만든다.
2. TranscriptSegment 데이터 구조를 만든다.
3. TranscriptSegment에는 다음을 포함한다.
   - start
   - end
   - text
   - avg_logprob
   - no_speech_prob
4. FasterWhisperEngine 구현체를 만든다.
5. faster-whisper의 결과를 TranscriptSegment 목록으로 변환한다.
6. CLI 코드 안에 STT 로직을 직접 몰아넣지 말고 core/transcription에 분리한다.
7. 모델 파일은 저장소에 커밋하지 않는다.

구현 요구사항 F: Export
1. Exporter 인터페이스를 만든다.
2. 다음 exporter를 구현한다.
   - TXT
   - JSON
   - Markdown
   - SRT
   - VTT
3. Export 시 현재 단계에서는 raw_text를 사용한다.
4. 나중에 edited_text > clean_text > raw_text 우선순위로 확장 가능하게 설계한다.
5. SRT/VTT 타임스탬프 포맷을 정확히 구현한다.
6. JSON에는 source_path, language, model, preset, segments를 포함한다.
7. Markdown에는 제목, 파일 정보, 모델 정보, 변환 본문을 포함한다.
8. 변환 중 진행 로그를 CLI에 출력한다.

구현 요구사항 G: 테스트/문서
1. pytest 기본 테스트를 추가한다.
2. 다음 테스트를 포함한다.
   - doctor 유틸 테스트
   - 입력 파일 검증 테스트
   - 전처리 프리셋 필터 문자열 테스트
   - SRT/VTT 타임스탬프 포맷 테스트
   - Exporter 출력 테스트
3. ruff 설정을 추가하고 ruff check가 통과되게 한다.
4. HISTORY.md에 이번 작업 이력을 추가한다.
5. CHANGELOG.md에 Unreleased 변경 사항을 추가한다.
6. README.md에 CLI 사용 예시를 추가한다.

완료 조건:
- pip install -e . 실행 가능
- sermonscript doctor 실행 가능
- sermonscript transcribe input.mp3 --language ko --model small 실행 가능
- processed.wav 생성
- TXT export 생성
- JSON export 생성
- Markdown export 생성
- SRT export 생성
- VTT export 생성
- pytest 통과
- ruff check 통과
- README, HISTORY, CHANGELOG 갱신 완료

범위 제외:
- PySide6 GUI 구현 제외
- SQLite 작업 이력 제외
- 사용자 사전 제외
- 원문 대조 변환 제외
- YouTube URL 입력 제외
- 온라인 다운로드 제외
- 클라우드/API 기능 제외
- 모델 파일 저장소 커밋 제외

공통 개발 원칙:
- 설계서의 기술 스택과 폴더 구조를 우선한다.
- 임의로 Electron, Tauri, Flutter, C#으로 바꾸지 않는다.
- CLI와 GUI가 나중에 같은 core 모듈을 재사용할 수 있게 설계한다.
- 원본 오디오 파일은 절대 수정하지 않는다.
- 모델 파일, 큰 바이너리, 개인정보성 오디오 파일은 저장소에 커밋하지 않는다.
- Windows 환경을 1차 대상으로 한다.
- 모든 변경은 테스트 가능한 단위로 작성한다.
- 작업 후 git diff를 확인하고, HISTORY.md와 CHANGELOG.md를 갱신한다.
```

---

# Goal 2 — SQLite/설정/모델 관리 + PySide6 GUI + 작업 큐

```text
/goal
SermonScript의 로컬 작업 이력, 설정 시스템, 모델 관리 기반, PySide6 GUI, 작업 큐와 진행률 표시를 구현한다.

배경:
Goal 1에서 CLI 기반 오디오 전처리, faster-whisper STT, TXT/JSON/Markdown/SRT/VTT Export가 동작한다고 가정한다.
이번 Goal은 CLI 코어를 실제 사용자가 쓸 수 있는 데스크톱 앱 형태로 확장하는 단계다.

이번 Goal의 목표:
변환 작업을 SQLite에 저장하고, 설정/모델 정보를 관리하며, PySide6 GUI에서 파일을 추가하고 변환을 실행할 수 있게 만든다.
긴 STT 작업이 UI를 멈추지 않도록 worker thread 또는 task queue 구조를 사용한다.

기술 스택:
- Python 3.11+
- SQLite
- platformdirs
- Typer CLI
- PySide6
- QThread 또는 QRunnable/QThreadPool
- pytest
- ruff

구현 요구사항 A: SQLite 작업 이력
1. storage/database.py를 구현한다.
2. 앱 데이터 디렉터리는 platformdirs를 사용한다.
3. SQLite DB 기본 경로를 정의한다.
4. DB 초기화 함수를 만든다.
5. 다음 테이블을 만든다.
   - jobs
   - segments
   - exports
6. jobs 테이블에는 다음 필드를 포함한다.
   - id
   - source_path
   - title
   - duration_sec
   - language
   - model_name
   - engine
   - preset
   - status
   - error_message
   - created_at
   - updated_at
7. segments 테이블에는 다음 필드를 포함한다.
   - id
   - job_id
   - start_sec
   - end_sec
   - raw_text
   - clean_text
   - edited_text
   - avg_logprob
   - no_speech_prob
   - needs_review
   - speaker
8. exports 테이블에는 다음 필드를 포함한다.
   - id
   - job_id
   - format
   - output_path
   - created_at
9. transcribe 실행 시 job record를 생성한다.
10. STT 세그먼트를 DB에 저장한다.
11. Export 결과를 DB에 저장한다.
12. 실패한 작업은 status=failed와 error_message를 저장한다.
13. DB migration을 위한 기본 구조를 만든다.
14. 테스트에서는 실제 사용자 DB를 건드리지 않고 임시 DB를 사용한다.

구현 요구사항 B: jobs/settings/models CLI
1. sermonscript jobs list 명령을 추가한다.
2. sermonscript jobs show <job_id> 명령을 추가한다.
3. sermonscript jobs export <job_id> 명령을 추가한다.
4. settings service를 구현한다.
5. 설정 항목은 다음을 포함한다.
   - 기본 언어
   - 기본 모델
   - 기본 전처리 프리셋
   - 기본 출력 폴더
   - 모델 캐시 폴더
6. sermonscript settings show 명령을 추가한다.
7. sermonscript settings set <key> <value> 명령을 추가한다.
8. model service 기반을 만든다.
9. sermonscript models list 명령을 추가한다.
10. sermonscript models cache-dir 명령을 추가한다.
11. 실제 모델 다운로드 구현이 과도하면 지원 모델 목록과 캐시 경로까지만 구현하고 후속 작업으로 기록한다.

구현 요구사항 C: PySide6 GUI 기본
1. python -m sermonscript.app.main 으로 GUI를 실행할 수 있게 한다.
2. main_window.py를 구현한다.
3. 메인 화면 구성:
   - 파일 추가 버튼
   - 폴더 추가 버튼은 가능하면 구현, 어려우면 후속 작업으로 기록
   - 드래그 앤 드롭 영역
   - 작업 목록 테이블
   - 언어 선택 콤보박스
   - 모델 선택 콤보박스
   - 전처리 프리셋 선택 콤보박스
   - 출력 폴더 선택
   - 변환 시작 버튼
   - 진행률 표시
   - 로그 패널
   - 결과 미리보기 영역
4. 파일 드래그 앤 드롭으로 지원 확장자 파일을 추가할 수 있게 한다.
5. 작업 목록에는 파일명, 길이, 상태, 모델, 프리셋을 표시한다.
6. GUI는 기존 core/services/storage 모듈을 재사용한다.
7. UI 코드 안에 STT 로직을 직접 구현하지 않는다.
8. 변환 완료 후 결과 텍스트를 미리보기 영역에 표시한다.
9. 변환 완료 후 export 파일 경로를 표시한다.
10. 실패 시 사용자에게 이해 가능한 한국어 메시지를 표시한다.
11. jobs DB에 저장된 최근 작업을 GUI에서 불러올 수 있게 한다.

구현 요구사항 D: 작업 큐와 진행률
1. 긴 변환 작업은 UI 스레드를 막지 않도록 worker thread에서 실행한다.
2. QThread 또는 QRunnable/QThreadPool 중 하나를 사용한다.
3. 변환 중 상태 메시지를 UI에 표시한다.
4. 가능한 경우 단계별 진행 상태를 표시한다.
   - 입력 파일 검사
   - 오디오 전처리
   - STT 변환
   - Export
   - DB 저장
5. 실패한 작업은 UI와 DB에 모두 실패 상태로 남긴다.
6. 사용자가 여러 파일을 추가할 수 있게 하되, 동시 변환은 1개부터 시작해도 된다.
7. 향후 병렬 작업이 가능하도록 작업 큐 구조를 과하게 복잡하지 않은 선에서 분리한다.

구현 요구사항 E: 설정 UI
1. 설정 화면 또는 간단한 설정 패널을 만든다.
2. 설정 변경은 settings service를 통해 저장한다.
3. 앱 종료 후 재실행 시 기본 설정을 유지한다.
4. 설정에는 다음을 포함한다.
   - 기본 언어
   - 기본 모델
   - 기본 전처리 프리셋
   - 기본 출력 폴더
   - 모델 캐시 폴더
5. 고급 설정은 UI에서 숨기거나 별도 섹션으로 분리한다.

구현 요구사항 F: 테스트/문서
1. SQLite 저장/조회 테스트를 추가한다.
2. settings service 테스트를 추가한다.
3. jobs CLI 테스트를 추가한다.
4. GUI는 무리한 E2E 대신 최소한 앱 진입점과 분리 가능한 core 테스트를 우선한다.
5. README.md에 GUI 실행 방법을 추가한다.
6. HISTORY.md에 작업 이력을 추가한다.
7. CHANGELOG.md에 Unreleased 변경 사항을 추가한다.
8. docs/architecture.md 또는 docs/roadmap-tasks.md에 Goal 2 완료 내용을 반영한다.

완료 조건:
- transcribe 실행 후 DB에 job/segments/exports가 저장됨
- sermonscript jobs list 실행 가능
- sermonscript jobs show 실행 가능
- sermonscript settings show 실행 가능
- sermonscript models list 실행 가능
- python -m sermonscript.app.main 실행 가능
- MP3/M4A/WAV 파일 GUI 추가 가능
- GUI에서 변환 시작 가능
- 변환 중 UI가 멈추지 않음
- 변환 완료 후 결과 미리보기 가능
- 작업 상태가 DB에 저장됨
- pytest 통과
- ruff check 통과
- README, HISTORY, CHANGELOG 갱신 완료

범위 제외:
- 고급 타임스탬프 편집기 제외
- 사용자 사전 제외
- 원문 대조 변환 제외
- 화자 분리 제외
- LLM 요약 제외
- YouTube URL 입력 제외
- 온라인 다운로드 제외
- 설치 파일 생성 제외

중요 원칙:
- 사용자 데이터 손실 가능성이 있는 DB 변경은 migration 계획을 남긴다.
- raw_text는 원본 STT 결과로 보존한다.
- clean_text와 edited_text는 별도 필드로 관리한다.
- 테스트는 실제 앱 데이터 경로를 오염시키지 않는다.
- GUI는 core/service 계층을 재사용한다.
- UI와 비즈니스 로직을 분리한다.
- 사용자에게 보이는 오류 메시지는 한국어로 이해 가능하게 작성한다.
```

---

# Goal 3 — 편집기/후처리/사용자 사전 + 원문 대조 변환 + 릴리즈 패키징

```text
/goal
SermonScript의 타임스탬프 편집기, 설교 후처리, 사용자 사전, 설교 원문 대조 변환, Windows 릴리즈 패키징 기반을 구현한다.

배경:
Goal 2까지 로컬 오디오 기반 STT, 전처리, Export, SQLite 작업 이력, 설정 시스템, PySide6 GUI, 작업 큐가 동작한다고 가정한다.
이번 Goal은 SermonScript를 단순 Whisper GUI가 아니라 설교 녹음 전문 STT 워크플로우 앱으로 차별화하는 단계다.

이번 Goal의 목표:
STT 결과를 세그먼트 단위로 검수/수정할 수 있는 편집기를 만들고, 설교/성경 용어 후처리와 사용자 사전을 구현한다.
또한 설교 원문 TXT/MD 파일을 참고 자료로 사용해 STT 결과와 대조하고 교정 후보를 제안한다.
마지막으로 Windows Portable ZIP 빌드를 위한 패키징 기반과 릴리즈 문서를 준비한다.

기술 스택:
- PySide6
- SQLite
- Python 표준 라이브러리
- RapidFuzz 사용 가능. 의존성 추가 시 라이선스와 필요성을 HISTORY.md에 기록한다.
- PyInstaller
- GitHub Actions
- pytest
- ruff

구현 요구사항 A: 타임스탬프 편집기
1. ui/widgets/transcript_editor.py를 구현한다.
2. 세그먼트를 줄 단위 또는 테이블 형태로 표시한다.
3. 각 세그먼트는 다음 정보를 가진다.
   - 시작 시간
   - 종료 시간
   - 텍스트
   - 확인 필요 여부
4. 사용자가 각 세그먼트의 텍스트를 수정할 수 있게 한다.
5. 수정 내용은 edited_text에 저장한다.
6. raw_text는 절대 덮어쓰지 않는다.
7. clean_text는 후처리 결과로 관리한다.
8. Export 시 edited_text > clean_text > raw_text 순서로 사용한다.
9. 검색 기능을 구현한다.
10. 치환 기능을 구현한다.
11. needs_review 표시 기능을 구현한다.
12. avg_logprob 또는 no_speech_prob 기반으로 확인 필요 후보를 표시한다.
13. 변경사항 자동 저장 또는 저장 버튼을 제공한다.
14. 사용자가 직접 수정한 edited_text는 자동 후처리로 덮어쓰지 않는다.

구현 요구사항 B: 설교 후처리와 사용자 사전
1. core/postprocess/dictionary.py를 구현한다.
2. 사용자 사전 파일을 지원한다.
   예:
   canonical: 로마서
   variants: 로마 써, 로마 서
3. 기본 설교/성경 용어 사전 초안을 만든다.
4. 사용자 사전 적용은 자동 덮어쓰기보다 교정 후보 또는 clean_text 생성 방식으로 구현한다.
5. core/postprocess/bible_reference.py를 구현한다.
6. 다음 유형을 보정한다.
   - 로마서 일장 일절 → 로마서 1장 1절
   - 로마서 1 장 1 절 → 로마서 1장 1절
   - 고린도 전서 → 고린도전서
7. 원문 모드와 정리 모드를 분리한다.
8. 후처리 적용 전/후를 비교할 수 있게 한다.
9. GUI에서 후처리 적용 버튼을 제공한다.
10. 후처리 결과는 clean_text에 저장한다.
11. 일반 문장을 과도하게 바꾸지 않는다.
12. 실제 발화를 훼손하지 않도록 자동 교정은 보수적으로 적용한다.

구현 요구사항 C: 원문 대조 변환
1. core/reference 모듈을 구현한다.
2. TXT/Markdown 원문 파일을 읽을 수 있게 한다.
3. reference_documents 테이블을 추가한다.
4. alignment_pairs 테이블을 추가한다.
5. correction_suggestions 테이블을 추가한다.
6. DB migration 또는 안전한 초기화 로직을 작성한다.
7. 원문에서 다음 정보를 추출한다.
   - 설교 제목 후보
   - 성경 본문 후보
   - 주요 용어
   - 고유명사 후보
8. 추출한 정보를 기반으로 faster-whisper initial_prompt를 생성한다.
9. initial_prompt에는 원문 전체를 넣지 않는다.
10. 성경 본문과 주요 용어만 짧게 넣는다.
11. STT 세그먼트와 원문 문단을 유사도 기반으로 정렬한다.
12. RapidFuzz를 사용할 경우 의존성 추가 이유와 라이선스 확인 내용을 HISTORY.md에 기록한다.
13. 성경 구절, 성경책 이름, 고유명사, 사용자 사전 기반 교정 후보를 생성한다.
14. 일반 문장은 자동 교체하지 않는다.
15. 교정 후보는 pending 상태로 저장한다.
16. GUI에서 교정 후보 목록을 표시한다.
17. 사용자는 교정 후보를 적용/무시할 수 있다.
18. 적용한 교정은 edited_text에 반영한다.
19. 원문과 실제 발화가 다른 경우 실제 발화를 우선 보존한다.
20. CLI에도 reference 입력 옵션을 추가한다.
   예:
   sermonscript transcribe sermon.mp3 --reference sermon.md --language ko --model medium

구현 요구사항 D: YouTube URL 기능 문서화
1. YouTube URL 입력은 v1.0 범위에서 제외한다.
2. docs/youtube-import-deferred.md 또는 docs/deferred-youtube-import.md를 작성/갱신한다.
3. 문서에는 다음 내용을 포함한다.
   - YouTube URL 입력은 입력 편의 기능일 뿐 STT 코어가 아님
   - 구현 시 URL 검증 → 권리/저작권 경고 → 오디오 추출 → 기존 로컬 파이프라인 전달 구조
   - 사용자는 권리가 있는 콘텐츠만 처리해야 함
   - v1.5 또는 v2.0 후보 기능으로 분류
4. 실제 YouTube 다운로드 기능은 구현하지 않는다.
5. 온라인 다운로드, DRM 우회, 접근 제한 우회 기능은 구현하지 않는다.

구현 요구사항 E: Windows 릴리즈 패키징
1. PyInstaller 설정을 추가한다.
2. scripts/build_windows.ps1을 만든다.
3. Portable ZIP 생성 스크립트를 만든다.
4. GitHub Actions Windows 빌드 workflow를 추가한다.
5. 빌드 산출물 이름 규칙:
   - SermonScript_Portable_{version}.zip
   - SermonScript_Setup_{version}.exe 는 후속 작업 가능
6. FFmpeg는 기본적으로 포함하지 않는다.
7. 모델 파일은 빌드 산출물에 포함하지 않는다.
8. THIRD_PARTY_NOTICES.md를 패키지에 포함한다.
9. docs/release-checklist.md를 작성/갱신한다.
10. CHANGELOG.md에 릴리즈 준비 항목을 기록한다.
11. HISTORY.md에 작업 이력을 기록한다.

구현 요구사항 F: 테스트/문서
1. 다음 테스트를 추가한다.
   - 사용자 사전 치환 후보
   - 성경 구절 보정
   - Export 우선순위 edited_text > clean_text > raw_text
   - needs_review 판정
   - 원문 파서
   - initial_prompt 생성
   - 세그먼트/원문 정렬
   - 교정 후보 생성
2. README.md에 편집기, 후처리, 원문 대조 변환 사용법을 추가한다.
3. docs/reference-alignment.md를 갱신한다.
4. docs/release-roadmap.md를 갱신한다.
5. HISTORY.md에 작업 이력을 추가한다.
6. CHANGELOG.md에 Unreleased 변경 사항을 추가한다.

완료 조건:
- STT 결과를 GUI에서 세그먼트 단위로 수정 가능
- 수정 내용이 DB의 edited_text에 저장됨
- raw_text가 보존됨
- 사용자 사전 기반 후처리 가능
- 성경 구절 보정 가능
- Export가 edited_text를 우선 사용
- reference 문서를 입력해 STT initial_prompt 생성 가능
- STT 결과와 원문 문단 정렬 가능
- 교정 후보 생성 가능
- GUI에서 교정 후보 적용/무시 가능
- YouTube URL 기능은 구현하지 않고 deferred 문서에만 기록
- PyInstaller 기반 Windows 빌드 스크립트 존재
- Portable ZIP 생성 가능
- pytest 통과
- ruff check 통과
- README, HISTORY, CHANGELOG, docs 갱신 완료

범위 제외:
- 실제 YouTube URL 다운로드 기능 제외
- LLM 요약 제외
- 화자 분리 제외
- 자동 업데이트 제외
- 상용 설치 프로그램 완성은 후속 작업 가능
- FFmpeg 번들 포함 제외
- 모델 파일 번들 포함 제외

중요 원칙:
- 설교 원문은 정답지가 아니라 참고 자료다.
- 실제 발화와 원문이 다르면 실제 발화를 보존한다.
- 일반 문장은 자동 교체하지 않는다.
- 교정 후보는 사용자가 승인해야 적용한다.
- 저작권 위험이 있는 온라인 다운로드 기능은 구현하지 않는다.
- FFmpeg와 모델 파일은 라이선스 정책을 확인하지 않고 번들에 포함하지 않는다.
- 사용자가 직접 수정한 edited_text는 자동 후처리로 덮어쓰지 않는다.
```

---

# 모든 Goal에 붙이는 공통 꼬리 지시문

각 `/goal` 끝에 아래 공통 지시문을 붙이면 좋습니다.

```text
공통 작업 규칙:
- 작업 시작 전 AGENTS.md, README.md, docs/ 문서를 먼저 확인한다.
- 작업 전 git status를 확인하고 기존 변경을 덮어쓰지 않는다.
- 이번 Goal 범위 밖 기능은 구현하지 말고 후속 작업으로 HISTORY.md 또는 docs/roadmap-tasks.md에 기록한다.
- 코드 변경 시 관련 문서도 함께 갱신한다.
- 사용자에게 보이는 메시지는 기본적으로 한국어로 작성하고, 필요한 경우 영어를 병기한다.
- core 로직은 UI와 분리한다.
- CLI와 GUI가 같은 core/service 계층을 재사용하게 한다.
- 원본 오디오 파일은 절대 수정하지 않는다.
- raw_text는 절대 덮어쓰지 않는다.
- edited_text는 사용자 수정본으로만 사용한다.
- 모델 파일, 오디오 샘플, 큰 바이너리, 개인정보성 파일은 Git에 커밋하지 않는다.
- YouTube URL 입력, 온라인 다운로드, 클라우드 기능은 v1.0 범위에서 제외한다.
- 외부 의존성을 추가할 때는 라이선스와 필요성을 확인하고 HISTORY.md에 이유를 기록한다.
- 완료 전 ruff check와 pytest를 실행한다.
- 실행하지 못한 검증은 성공했다고 쓰지 말고, 왜 생략했는지 기록한다.
- 작업 완료 후 변경 파일, 검증 결과, 후속 작업을 요약한다.
```

---

# 추천 사용 순서

```text
1회차 작업:
Goal 1 — 저장소 초기화 + CLI 코어 + 오디오 전처리/STT/Export

2회차 작업:
Goal 2 — SQLite/설정/모델 관리 + PySide6 GUI + 작업 큐

3회차 작업:
Goal 3 — 편집기/후처리/사용자 사전 + 원문 대조 변환 + 릴리즈 패키징
```

3개 Goal은 각각 꽤 큰 작업 단위입니다. 에이전트가 실패하거나 중간에 멈추면 같은 Goal을 다시 실행하기보다, 실패 지점만 작은 후속 Goal로 잘라서 복구하는 방식을 권장합니다.
