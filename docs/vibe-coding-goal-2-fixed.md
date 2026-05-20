# Goal 2 — SQLite/설정/모델 관리 + PySide6 GUI + 작업 큐

```text
/goal
SermonScript의 로컬 DB, 설정, 모델 관리, PySide6 GUI, 작업 큐를 구현한다.

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
15. python -m sermonscript.app.main으로 PySide6 GUI를 실행한다.
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
