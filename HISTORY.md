# HISTORY.md

## 2026-05-20
- 작업: SermonScript 설계서 묶음 통합 및 기존 AGENTS/README/HISTORY/CHANGELOG 템플릿 반영
- 변경 파일:
  - README.md: SermonScript 프로젝트 소개, v1.0 범위, 개발 시작 방법 작성
  - AGENTS.md: 기존 범용 에이전트 규칙을 SermonScript용으로 프로젝트 설정값 및 범위에 맞게 변환
  - CHANGELOG.md: v0.2.0 설계 문서 통합 변경 사항 기록
  - HISTORY.md: 통합 작업 이력 기록
  - docs/: 제품 명세, 아키텍처, 오디오 파이프라인, 원문 대조, YouTube 후순위 기능, 바이브 코딩 목표 문서 추가
  - src/: 초기 Python 패키지 스캐폴드 추가
- 검증: 문서 구조 및 압축 파일 생성 확인
- 결과: 성공
- 후속 작업:
  - GitHub 저장소 생성 후 첫 `/goal`로 프로젝트 초기화 및 `sermonscript doctor` 구현
  - 실제 라이브러리 추가 시 각 의존성 라이선스 재확인
  - YouTube URL 입력은 v1.5 또는 v2.0 후보로 유지

## 2026-05-17
- 작업: 기존 범용 에이전트 규칙의 모바일 배포 및 릴리즈 운영 규칙 확인
- 반영:
  - Expected Assets 개념을 SermonScript의 EXE/ZIP 산출물 검증으로 변환
  - 릴리즈 노트, CHANGELOG, HISTORY 동시 갱신 규칙 반영
  - 민감 정보, 외부 SDK, 배포 산출물 확인 규칙을 데스크톱 프로젝트에 맞게 조정


## 2026-05-20
- 작업: 바이브 코딩 `/goal` 프롬프트를 6단계에서 3단계 대형 Goal 구조로 재구성
- 변경 파일:
  - docs/vibe-coding-goals.md: 3단계 대형 Goal 프롬프트로 갱신
  - docs/vibe-coding-goals-3phase.md: 동일한 3단계 Goal 문서 추가
  - README.md: 3단계 Goal 안내 추가
  - CHANGELOG.md: 문서 변경 사항 기록
- 검증: 문서 변경 내용 검토, ruff check, pytest, sermonscript doctor
- 결과: 성공
- 후속 작업: 실제 개발 시 Goal 1부터 순차적으로 바이브 코딩 에이전트에 입력
