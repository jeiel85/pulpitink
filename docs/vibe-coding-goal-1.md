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
