# AGENTS.md

이 문서는 AI 코딩 에이전트가 PulpitInk 저장소에서 작업할 때 따라야 하는 공통 작업 규칙입니다.

---

## 1. 프로젝트 설정값

```text
Project Name: PulpitInk
Repository: https://github.com/jeiel85/pulpit-ink.git
Main Branch: main
Primary Spec: docs/product-spec.md
History Document: HISTORY.md
Changelog: CHANGELOG.md
Task Document: docs/roadmap-tasks.md
Decision Log: docs/decision-log.md
Version Files: pyproject.toml, src/pulpit_ink/__init__.py, CHANGELOG.md
Build/Test Commands: pytest, ruff check ., pulpit-ink doctor
Release Trigger: tag push
CI System: GitHub Actions
Expected Assets: EXE, ZIP
Primary Platform: Windows 10/11
Primary Language: Python 3.11+
```

---

## 2. 프로젝트 범위

PulpitInk는 로컬 PC에서 설교, 강의, 회의 녹음 파일을 전처리하고 STT 변환한 뒤 검수·편집·출력하는 오픈소스 데스크톱 프로그램입니다.

v1.0에서 지원하는 입력은 로컬 파일입니다.

```text
지원: mp3, wav, m4a, flac, ogg, mp4 등 로컬 파일
제외: YouTube URL, 온라인 다운로드, 클라우드 입력, 실시간 녹음
```

YouTube URL 입력은 v1.5 또는 v2.0 후보 기능이며, 저작권/이용 권한 경고와 별도 입력 소스 모듈이 필요합니다.

---

## 3. Automation First Principle

에이전트는 가능한 한 작업을 끝까지 자동으로 수행합니다.

사용자 확인 없이 자동 진행할 수 있는 항목:

- 최신 소스 동기화
- 작업 범위 분석
- 코드 수정
- 관련 문서 갱신
- `CHANGELOG.md`, `HISTORY.md`, `docs/decision-log.md` 갱신
- 가벼운 로컬 검증
- 커밋 생성
- 원격 저장소 푸시
- GitHub Actions 상태 확인
- CI 실패 로그 확인 후 수정 커밋 및 재푸시
- 최종 작업 보고

단, 아래 항목은 자동 진행하지 않고 중단 후 보고합니다.

- `git reset --hard`
- `git clean -fd`
- `git push --force`
- 원격 브랜치 삭제
- 원격 태그 삭제
- 사용자 데이터 삭제 가능성이 있는 변경
- 롤백이 어려운 데이터 마이그레이션
- 시크릿, 인증서, API 키, 릴리즈 키 관련 변경
- 유료 서비스, 외부 API, 로그인, 결제, 분석 도구 추가
- YouTube 다운로드, 클라우드 연동, 온라인 API 호출 기능 추가
- 프로젝트 정책과 충돌하는 의존성 추가
- 배포 또는 릴리즈 조작

---

## 4. 기본 커뮤니케이션 규칙

- 사용자 설명, 작업 요약, 커밋 메시지, 이슈 코멘트는 기본적으로 한국어로 작성합니다.
- 불확실한 부분은 추측하지 않고 근거, 제약, 확인 결과를 명시합니다.
- 보안, 데이터 손실, 비용, 라이선스, 정책 충돌 가능성이 있으면 중단 후 질문합니다.
- 요청하지 않은 대규모 리팩터링, 디자인 전면 수정, 기능 확장은 하지 않습니다.
- 진행 상황 보고 시 실제 수행한 작업과 아직 확인하지 못한 작업을 구분합니다.

---

## 5. 작업 시작 전 필수 절차

```bash
git fetch origin
git checkout main
git pull origin main
git status
```

그 다음 아래 문서를 순서대로 확인합니다.

1. `AGENTS.md`
2. `docs/product-spec.md`
3. `docs/roadmap-tasks.md`
4. `HISTORY.md`
5. `docs/decision-log.md`
6. `CHANGELOG.md`
7. 관련 `README.md`, `docs/`, CI/CD 설정 파일

작업 전 `git status`가 깨끗하지 않다면 기존 변경 사항을 덮어쓰지 않습니다.

---

## 6. 구현 원칙

- 설계서의 기술 스택과 폴더 구조를 우선합니다.
- 핵심 로직은 UI와 분리하고, CLI와 GUI가 같은 core 모듈을 재사용하게 합니다.
- 원본 오디오 파일은 절대 수정하지 않습니다.
- STT 결과의 `raw_text`는 절대 덮어쓰지 않습니다.
- 사용자가 수정한 내용은 `edited_text`에 저장합니다.
- 전처리 결과는 캐시 또는 작업 폴더에 별도 생성합니다.
- 모델 파일, 큰 바이너리, 개인정보성 오디오 파일은 저장소에 커밋하지 않습니다.
- FFmpeg 바이너리는 기본 저장소에 포함하지 않습니다.
- 외부 명령, 파일 경로, URL, 사용자 입력은 검증 후 사용합니다.
- 비동기 작업은 UI 프리징을 유발하지 않도록 worker thread에서 실행합니다.
- 에러 메시지는 사용자에게 이해 가능한 문장과 개발자 추적 로그를 모두 고려합니다.
- Windows 환경을 1차 대상으로 합니다.

---

## 7. Scope Control Rules

한 번의 작업 루프에서는 가장 우선순위가 높은 작업 하나만 선택합니다.

하지 말아야 할 것:

- 관련 없는 리팩터링
- 전체 포맷팅
- 디자인 전면 수정
- 기본 기능과 직접 관련 없는 UI 개선
- 임의의 기능 추가
- 테스트 구조 전체 변경
- 프로젝트 설정의 대규모 재구성
- YouTube URL 입력을 v1.0 작업 중 임의 구현

필요해 보이는 개선 사항은 `docs/roadmap-tasks.md` 또는 `docs/decision-log.md`에 후속 작업으로 기록합니다.

---

## 8. 의존성 규칙

새 의존성은 꼭 필요한 경우에만 추가합니다.

추가 전 확인 항목:

- 기존 코드나 표준 라이브러리로 해결 가능한지
- 라이선스가 Apache-2.0 배포 정책과 충돌하지 않는지
- 번들 크기와 빌드 시간 영향
- 유지보수 상태
- 보안 취약점
- Windows 호환성

의존성 변경 시 변경 이유를 `HISTORY.md` 또는 `docs/decision-log.md`에 기록합니다.

---

## 9. 데이터 및 보안 원칙

- 사용자 데이터는 기본적으로 로컬 우선으로 다룹니다.
- 오디오 파일과 변환 텍스트는 기본적으로 외부 서버로 전송하지 않습니다.
- 캐시, 로컬 DB, 설정 파일, 임시 파일 저장 위치와 삭제 정책을 고려합니다.
- 로그에 토큰, 쿠키, 인증 헤더, 개인정보, 설교 원문 전체가 남지 않도록 주의합니다.
- 작업 삭제 시 캐시까지 삭제하는 기능을 고려합니다.
- YouTube 또는 온라인 기능은 권리 고지, 이용 책임 문구, 사용자 확인 절차 없이는 구현하지 않습니다.

---

## 10. 테스트 및 품질 확인

변경 후 가능한 범위에서 아래 순서로 검증합니다.

1. 정적 검사 또는 린트
2. 타입 체크
3. 단위 테스트
4. 통합 테스트
5. 빌드
6. 핵심 플로우 수동 확인

기본 명령:

```bash
ruff check .
pytest
pulpit-ink doctor
```

실행하지 않은 테스트를 성공한 것처럼 기록하지 않습니다.

---

## 11. 문서화 및 이력 관리

코드가 바뀌면 관련 문서를 함께 갱신합니다.

- 주요 변경 사항: `HISTORY.md`
- 릴리즈 변경 사항: `CHANGELOG.md`
- 기능 명세 변경: `docs/product-spec.md`
- 작업 목록 변경: `docs/roadmap-tasks.md`
- 중요한 기술적 판단: `docs/decision-log.md`

이력 문서에는 최소한 아래 내용을 남깁니다.

```text
날짜:
작업:
변경 파일:
검증:
결과:
후속 작업:
```

---

## 12. 커밋 및 푸시 규칙

```bash
git status
git diff --stat
git diff
git add <changed files>
git commit -m "<type>: <변경 요약>"
git push origin <CURRENT_BRANCH>
```

권장 커밋 형식:

```text
feat: 새 기능 추가
fix: 오류 수정
docs: 문서 수정
refactor: 구조 개선
test: 테스트 추가 또는 수정
chore: 설정, 빌드, 정리 작업
```

커밋 메시지는 한국어를 기본으로 작성합니다.

---

## 13. 릴리즈 및 배포 확인

릴리즈 전 확인 항목:

- GitHub Actions 성공 여부
- `CHANGELOG.md` 최신화
- `HISTORY.md` 최신화
- 앱 내부 버전과 태그 버전 일치
- Windows EXE 생성
- Portable ZIP 생성
- 파일 크기가 0이 아닌지 확인
- 모델 파일이 포함되지 않았는지 확인
- FFmpeg 포함 여부와 라이선스 고지 확인
- `THIRD_PARTY_NOTICES.md` 포함
- 릴리즈 노트와 문서가 서로 모순되지 않는지 확인

---

## 14. Final Report Format

작업 완료 후 에이전트는 아래 형식으로 요약합니다.

```text
작업 요약:
- 

변경 파일:
- 

검증:
- 로컬:
- CI:
- 생략한 검증:

커밋:
- 

푸시:
- 

후속 작업:
- 
```

검증하지 않은 항목은 성공으로 표현하지 않습니다.
