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
