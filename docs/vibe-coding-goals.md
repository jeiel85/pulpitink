# Vibe Coding `/goal` Prompts

## 공통 개발 원칙

매번 `/goal` 아래쪽에 붙입니다.

```text
공통 개발 원칙:
- 설계서의 기술 스택과 폴더 구조를 우선한다.
- 임의로 프레임워크를 바꾸지 않는다.
- 기능을 구현할 때 CLI와 GUI가 같은 core 모듈을 재사용하게 한다.
- 원본 오디오 파일은 절대 수정하지 않는다.
- STT 결과의 raw_text는 절대 덮어쓰지 않는다.
- 사용자가 수정한 내용은 edited_text에 저장한다.
- 모델 파일, 큰 바이너리, 개인정보성 오디오 파일은 저장소에 커밋하지 않는다.
- 모든 기능에는 최소한의 테스트를 추가한다.
- 에러 메시지는 사용자가 이해할 수 있게 작성한다.
- Windows 환경을 1차 대상으로 한다.
- 코드는 ruff 기준으로 정리한다.
- YouTube URL 입력, 온라인 다운로드, 클라우드 기능은 v1.0 범위에서 제외한다.
- 현재는 로컬 오디오/비디오 파일 입력만 지원한다.
```

## Goal 0: 저장소 초기화

```text
/goal
첨부한 SermonScript 설계서 묶음을 기준으로 GitHub Public 오픈소스 프로젝트의 초기 저장소를 구성한다.

이번 목표는 아직 STT 기능을 구현하지 않고, 프로젝트 골격과 CLI doctor 명령까지만 안정적으로 만드는 것이다.

구현 범위:
1. Python 3.11+ 프로젝트 구조 생성
2. pyproject.toml 작성
3. src/sermonscript 패키지 구조 생성
4. Typer 기반 CLI 생성
5. sermonscript doctor 명령 구현
6. FFmpeg 설치 여부 확인
7. Python 버전 확인
8. OS 정보 출력
9. 앱 데이터 디렉터리 생성 가능 여부 확인
10. pytest 테스트 추가
11. ruff 설정 추가
12. README의 개발 실행법 업데이트

완료 조건:
- pip install -e . 가능
- sermonscript doctor 실행 가능
- pytest 통과
- ruff check 통과

공통 개발 원칙:
- 설계서의 기술 스택과 폴더 구조를 우선한다.
- 임의로 프레임워크를 바꾸지 않는다.
- 처음부터 GUI를 만들지 않는다.
- 처음부터 STT 변환을 구현하지 않는다.
- 모델 파일이나 큰 바이너리를 저장소에 넣지 않는다.
- Windows 환경을 1차 대상으로 한다.
- YouTube URL 입력, 온라인 다운로드, 클라우드 기능은 v1.0 범위에서 제외한다.
```

## Goal 1: CLI 변환기

```text
/goal
SermonScript의 Phase 1을 구현한다.

이번 목표는 GUI 없이 CLI에서 오디오 파일을 텍스트로 변환하는 최소 동작 버전을 만드는 것이다.

구현할 명령:
sermonscript transcribe input.mp3 --language ko --model small --output ./exports

요구사항:
1. transcribe 명령을 추가한다.
2. 입력 파일 존재 여부와 확장자를 검증한다.
3. FFmpeg가 설치되어 있는지 검사한다.
4. 입력 오디오를 임시 작업 폴더에 16kHz mono WAV로 변환한다.
5. faster-whisper로 STT를 실행한다.
6. 결과를 TXT와 JSON으로 저장한다.
7. JSON에는 source_path, language, model, segments를 포함한다.
8. segments에는 start, end, text를 포함한다.
9. 변환 중 에러가 발생하면 사용자에게 명확한 메시지를 출력한다.
10. 핵심 로직은 CLI 함수 안에 몰아넣지 말고 core/audio, core/transcription, core/export 모듈로 분리한다.

완료 조건:
- sermonscript transcribe sample.mp3 --language ko --model small 실행 가능
- TXT 파일 생성
- JSON 파일 생성
- pytest 통과
- ruff 통과
```

## Goal 2: 오디오 전처리

```text
/goal
SermonScript의 오디오 전처리 파이프라인을 구현한다.

이번 목표는 STT 전에 오디오를 변환하기 좋은 상태로 만드는 전처리 프리셋을 추가하는 것이다.

구현할 프리셋:
1. none: 포맷 변환만 수행
2. stt_basic: mono, 16kHz, highpass, lowpass, loudnorm
3. sermon: 설교 녹음용 균형 프리셋
4. noisy: 잡음 많은 녹음용 강한 프리셋

완료 조건:
- sermonscript transcribe input.mp3 --preset sermon 실행 가능
- processed.wav 생성
- TXT/JSON Export 정상 동작
- pytest 통과
- ruff 통과
```

## Goal 3: SQLite 작업 이력

```text
/goal
SermonScript에 SQLite 기반 작업 이력 저장 기능을 구현한다.

이번 목표는 변환 작업, 세그먼트, 내보내기 이력을 로컬 DB에 저장하는 것이다.

완료 조건:
- transcribe 후 DB에 job/segments/exports 저장
- sermonscript jobs list 실행 가능
- sermonscript jobs show 실행 가능
- pytest 통과
- ruff 통과
```

## Goal 4: PySide6 GUI

```text
/goal
SermonScript의 PySide6 기반 Windows 데스크톱 GUI v0.3을 구현한다.

이번 목표는 사용자가 오디오 파일을 드래그 앤 드롭하고 변환을 실행할 수 있는 기본 GUI를 만드는 것이다.

완료 조건:
- python -m sermonscript.app.main 으로 GUI 실행
- MP3 파일 드래그 앤 드롭 가능
- 변환 시작 가능
- UI가 멈추지 않음
- 결과 텍스트 표시
- pytest 통과
- ruff 통과
```

## Goal 5: 원문 대조 변환

```text
/goal
SermonScript에 설교 원문 대조 변환 기능을 구현한다.

이번 목표는 사용자가 설교 원문 TXT/MD 파일을 함께 입력하면, STT 결과와 원문을 대조하여 교정 후보를 제안하는 것이다.

완료 조건:
- 오디오 + 원문 입력 가능
- initial_prompt 생성 가능
- STT 결과와 원문 대조 가능
- 교정 후보 목록 표시 가능
- 적용한 교정은 edited_text에 반영
- pytest 통과
- ruff 통과
```
