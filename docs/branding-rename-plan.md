# SermonScript → 설교필기 (PulpitInk) 브랜딩 변경 구현 계획

> **상태**: ✅ 이름 확정 / 🟡 구현 대기 (후속 세션에서 실행)
> **확정 일자**: 2026-05-20
> **작업 브랜치**: `feat/tauri-hybrid` 또는 신규 `feat/branding`

---

## 1. 확정 사항

| 항목 | 값 |
|------|-----|
| **한글 정식 명칭** | **설교필기** |
| **영문 정식 명칭** | **PulpitInk** |
| **브랜드 컨셉** | "설교단(Pulpit)의 잉크(Ink)" — 설교 특화 데스크톱 STT 앱 |

---

## 2. 브랜드 충돌 조사 결과

5개 후보에 대해 웹 검색 기반 브랜드 충돌 조사를 완료했습니다.

| # | 한글명 | 영문명 | 판정 | 사유 |
|---|--------|--------|:----:|------|
| A | 말씀필사 | VoiceQuill | ❌ 탈락 | VoiceQuill = iOS STT 노트 앱 (동일 도메인) |
| B | 소리글 | SoriScript | ❌ 탈락 | 소리글AI = 회의 녹음+요약 앱 (거의 동일 기능!) |
| C | 음성기록관 | ScribeFlow | ❌ 탈락 | ScribeFlow = 최소 5개 서비스 사용 중 |
| **D** | **설교필기** | **PulpitInk** | **✅ 선택** | 소프트웨어 충돌 없음 |
| E | 하늘소리 | CelestialVox | ⚠️ 탈락 | CelestialVox = Google Play 기도문 앱 실존 |

**PulpitInk 상세**:
- "PulpitInk"은 팟캐스트 에피소드 제목 구문의 일부로만 등장 (소프트웨어 브랜드 아님)
- "설교필기"를 앱 이름으로 사용하는 제품 없음
- 도메인(`pulpitink.com` 등) 가용성은 추가 확인 필요

---

## 3. 미결 사항 (실행 전 확인 필요)

### Q1. GitHub 저장소 이름 변경 여부
- 현재: `jeiel85/sermon-script`
- 옵션 A: `jeiel85/pulpitink`로 변경 (기존 URL은 GitHub이 리다이렉트)
- 옵션 B: 유지 (내부 이름만 변경)
- **영향**: CI 설정, 외부 링크, README 배지 등

### Q2. Python 패키지명 변경 여부
- 현재: `pip install sermonscript`, CLI 명령 `sermonscript`
- 옵션 A: `pip install pulpitink`, CLI 명령 `pulpitink`
- 옵션 B: 패키지명/CLI 유지, 표시 이름만 변경
- **참고**: PyPI에 아직 미배포 상태라면 자유롭게 변경 가능

### Q3. 타이틀바 표기 형식
- 옵션 1: `설교필기` (한글만)
- 옵션 2: `설교필기 (PulpitInk)` (한글 + 영문)
- 옵션 3: `PulpitInk — 설교필기` (영문 주 + 한글 부)

---

## 4. 변경 대상 파일 목록

### 4.1 Tauri 설정 (프론트엔드)

| 파일 | 변경 내용 |
|------|-----------|
| `frontend/src-tauri/tauri.conf.json` | `productName`, `identifier`, `windows.title` |
| `frontend/src-tauri/Cargo.toml` | `package.name` |
| `frontend/package.json` | `name` |
| `frontend/index.html` | `<title>` 태그 |

### 4.2 React UI

| 파일 | 변경 내용 |
|------|-----------|
| `frontend/src/App.tsx` | 사이드바 `<h1>` 브랜드명, Doctor 진단 헤더 |
| `frontend/src/App.css` | `.brand-name` 폰트 스타일 (한글 폰트) |

### 4.3 Python 백엔드 / CLI

| 파일 | 변경 내용 |
|------|-----------|
| `pyproject.toml` | `project.description`, `project.urls` (name은 Q2 답변에 따라) |
| `src/sermonscript/__init__.py` | `APP_NAME` 상수 |
| `src/sermonscript/cli/main.py` | CLI 헤더/배너 |
| `src/sermonscript/app/main.py` | 윈도우 타이틀 |

### 4.4 Windows 빌드 / 패키징

| 파일 | 변경 내용 |
|------|-----------|
| `sermonscript.spec` | EXE 이름 |
| `scripts/build_windows.ps1` | 출력 파일명 |
| `scripts/make_portable_zip.ps1` | ZIP 파일명 |
| `.github/workflows/build-windows.yml` | artifact 이름, Release 산출물 |

### 4.5 문서

| 파일 | 변경 내용 |
|------|-----------|
| `README.md` | 프로젝트 소개문, 제목, 배지 |
| `CHANGELOG.md` | 브랜딩 변경 항목 추가 |
| `HISTORY.md` | 브랜딩 결정 이력 |
| `docs/decision-log.md` | 이름 결정 근거 |
| `docs/product-spec.md` | 공식 명칭 |
| `docs/user-guide.md` | 앱 이름 일괄 변경 |
| `docs/release/release-checklist.md` | 릴리즈 체크 항목 갱신 |

### 4.6 GitHub 저장소

- Repository Description 갱신 (`gh repo edit`)
- About / Topics 갱신
- Social Preview 이미지 (한글명 포함)
- Repository 이름 변경 (Q1 답변에 따라)

---

## 5. 실행 절차

```text
1. 이 문서와 docs/decision-log.md 확인
2. 미결 사항(Q1~Q3) 답변 수집
3. 작업 브랜치 생성 또는 기존 브랜치 사용
4. 4.1 ~ 4.6 순서대로 일괄 반영
5. 테스트 실행:
   - python -m ruff check .
   - python -m pytest
   - npm.cmd run tauri build (프론트엔드)
6. 문서 갱신 (HISTORY, CHANGELOG, decision-log)
7. 커밋: "feat: 앱 브랜딩 변경 — 설교필기 (PulpitInk)"
8. 푸시
9. GitHub 저장소 메타데이터 갱신
```

---

## 6. 검증 체크리스트

- [ ] 앱 기동 시 타이틀바에 새 이름 표시
- [ ] 사이드바 브랜드 영역에 한글명 표시
- [ ] CLI `--version` 출력에 새 이름 반영
- [ ] `sermonscript doctor` 헤더에 새 이름 반영
- [ ] README, CHANGELOG, 문서 전체 일관성
- [ ] GitHub 저장소 About/Description 갱신
- [ ] Windows EXE 파일명 및 속성에 반영
- [ ] Portable ZIP 파일명에 반영
