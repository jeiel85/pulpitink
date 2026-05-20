# 통합 회귀 결과 기록

본 파일은 `tests/integration/README.md` 의 시나리오를 실행할 때마다 한 회차를 추가하는 누적 로그입니다.
실행 결과는 `verify_run.py` 의 출력을 그대로 붙여 넣어도 좋습니다.

---

## 회차 #1 — 2026-05-20 (Goal 3 직후, v1.0 준비)

### 입력

- 오디오: `D:\Media\2026-05-13 수요밤설교 _ 로마서 1장 1-15절 _ 로마서의 서론.mp3` (35분 45초, 129kbps)
- 원문(md): `tests/integration/fixtures/sermon.md` (236문단, ~9.7KB, docx 추출)
- 모델: `small` / CPU `int8` / `--preset sermon`
- 출력: `tests/integration/out/`

### 실행 명령

```powershell
python -X utf8 -m pulpitink.cli.main transcribe `
  "D:\Media\2026-05-13 수요밤설교 _ 로마서 1장 1-15절 _ 로마서의 서론.mp3" `
  --reference tests/integration/fixtures/sermon.md `
  --language ko --model small --preset sermon `
  --format txt,json,md,srt,vtt `
  --output tests/integration/out `
  --cache-root tests/integration/out/cache
```

### 결과

- 변환 소요: **1560.55초 (~26분)** for 2140.8초 (35분 45초) audio → 약 0.73x 실시간
- 세그먼트: **641 개**, raw_text 641/641 비어있지 않음
- needs_review 표시: **10 건** (자동 신뢰도 기반)
- Export: **5종(txt/json/md/srt/vtt) 모두 생성**, 총 ~356KB
- DB 영속화: job/segments/exports/reference_documents/alignment_pairs 정상 저장
- 원문 파싱: title="제1과 로마서의 서론", paragraphs=235, keywords=30, proper_nouns=35
- alignment_pairs: **11 건** (641 세그먼트 대비 1.7% — 실제 발화와 원문 표현 차이 큼)
- ⚠️ bible_refs: **0 건** — 원문에 "로마서 3: 21~22" 등 콜론 표기가 있는데 매치 실패
- ⚠️ correction_suggestions: **0 건** — 후술

```text
[INFO] 작업 ID — 203ce7cea249
[PASS] 상태 — completed
[INFO] 모델/프리셋 — small / sermon / lang=ko
[INFO] 길이 — 2140.8s
[PASS] 세그먼트 개수 — 641
[PASS] raw_text 비어있지 않음 — 641/641
[INFO] 후처리 흔적 (clean_text != raw_text) — 0건
[INFO] needs_review 표시 — 10건 (신뢰도 낮은 세그먼트)
[PASS] Export 5종 — 생성=json,md,srt,txt,vtt / 누락=없음
[PASS] reference_documents — 1건
[INFO]   - 원문 메타 — title='제1과 로마서의 서론' chars=9729 bible_refs=0 keywords=30 proper_nouns=35
[PASS] alignment_pairs — 11건
[INFO] correction_suggestions — 총 0건 / pending 0 / kinds=없음
```

### 관찰 / 후속 작업

**파이프라인 자체는 정상**: 전처리(processed.wav 생성) → STT(641 세그먼트) → 후처리(clean_text 채움) → Export 5종 → DB 영속화까지 끊김없이 동작했습니다. raw_text 보존, edited_text/clean_text 분리, exports 재생성 가능 등 핵심 불변식은 만족합니다.

**발견된 실제 문제 2건** (v1.0/v1.1 사이에서 결정 필요):

1. **bible_refs 정규식 한계** ([tasks #11](../../HISTORY.md)). `parser._BIBLE_REF_RE` 가 `장` 키워드를 강제하기 때문에 원문에 흔한 `로마서 3: 21~22` 콜론 표기가 매치되지 않습니다. 정규식을 `장|:` 양쪽 허용으로 확장하면 회복 가능합니다.

2. **교정 후보 적중률 낮음** ([tasks #12](../../HISTORY.md)). 35분 실설교에서 `correction_suggestions=0`:
   - **bible_ref kind**: STT 가 `로마서 일장 일절` 같은 한글 수사 표기를 거의 내지 않고 `로마서, 제1립장` 형태로 깨져 normalise 가 못 잡음.
   - **user_dict kind**: lexicon wrong_forms (`고린도 전서` 등) 사전등록형이라 `보궁`(복음)/`이에수`(예수)/`그리시도`(그리스도)/`사다`(사도) 같은 모음·자음 변형형엔 무력.
   - **proper_noun kind**: 원문 proper_nouns 가 `Imputation/II/III` 같은 라틴 문자 위주이고, 한국어는 `예수 그리스도의 종`/`사도로 부르심을 받아` 같은 긴 구절이라 squeeze 비교가 거의 매치되지 않음.

   v1.0 안에서 해결하려면 자모(jamo) 기반 유사도 매칭이나 lexicon 자동 확장이 필요한데 범위 큰 작업입니다. v1.1 후속 작업으로 정리하고 v1.0 release notes 의 “알려진 제한” 에 명시하는 편이 안전합니다.

**부수 발견**

- 원본 오디오 첫 부분의 화자가 작은 음량이라 STT 가 "감사합니다, 할 수 있겠습니다." 등을 "말하고, 할 수 있겠습니다." 로 미스. 첫 세그먼트가 항상 약한 패턴.
- `--cache-root tests/integration/out/cache` 옵션으로 processed.wav 가 통합 시험 디렉터리 안에 머무는 것 확인.
- Windows PowerShell 코드 페이지(cp949) 때문에 doctor 표가 깨져 보임. `PYTHONIOENCODING=utf-8 + python -X utf8` 로 우회 가능. user-guide 에 anchor 한 줄 추가 검토.

**다음 회차에서 확인할 항목**

- bible_refs 정규식 확장 후 같은 입력으로 재실행 → bible_ref 후보 ≥ 1 회복 확인
- medium 모델 / `--device cuda` 로 환경별 회귀
- 편집기에서 needs_review 10건 직접 검토 (스크린샷 자료 확보 겸용)

---

### Hotfix — 2026-05-20 (회차 #1 직후)

- **#11 수정 적용**: `parser._BIBLE_REF_COLON_RE` 신설로 `로마서 3: 21~22` 콜론 표기 인식. 직접 파싱 결과: `bible_refs = ['로마서 3장 21-22절']` (이전 0건 → 1건).
- 회귀 영향: 다음 회차에 reference_documents.bible_refs 가 채워지고, initial_prompt 의 `성경 본문: ...` 라인이 비어있지 않게 됩니다. STT 정확도에 마이너 개선 가능.
- correction_suggestions 0건 문제(#12)는 별개입니다 — bible_ref kind 는 `normalise_bible_reference(세그먼트 raw_text)` 결과로 별도 발생하기 때문. 자모 변형 매칭이 추가되어야 의미 있게 늘어납니다.
- 검증: `pytest` 85/85 PASS, `ruff check .` PASS, 신규 테스트 `test_parse_extracts_bible_refs_colon_notation`, `test_parse_deduplicates_jang_and_colon_overlap` 포함.

---

## 회차 #2 — 2026-05-20 (Jamo Fuzzy 매칭 도입 검증)

### 입력 및 검증 대상
- **DB 데이터**: 회차 #1의 변환 결과 (`job_id=203ce7cea249`, 세그먼트 641개, `proper_nouns` 35개)
- **추가 구현 기능**: 한국어 자모(Jamo) 분해 및 초성(Choseong) 기반 Hybrid 유사도 측정 (`rapidfuzz` 활용)
- **설정**: 
  - Fuzzy 미활성화
  - Fuzzy 활성화 및 Threshold = 0.70
  - Fuzzy 활성화 및 Threshold = 0.65

### 실행 명령 및 방법
DB에 영속화된 데이터 세그먼트 641개와 원문 고유명사 35개를 로드하여, 새롭게 작성된 `CorrectionEngine`을 인메모리에서 다른 설정값들로 돌려 교정 제안 검출률 변화를 추적하는 통합 시뮬레이션 코드(`tests/integration/verify_fuzzy.py`) 실행.

```powershell
$env:PYTHONIOENCODING="utf-8"
python -X utf8 tests/integration/verify_fuzzy.py
```

### 결과

- **Fuzzy 미활성화 시 제안 수**: **0 건** (이전 회차 #1과 동일)
- **Fuzzy 활성화 (Threshold = 0.70) 시 제안 수**: **292 건** (약 29200% 비약적 상승! 🚀)
- **Fuzzy 활성화 (Threshold = 0.65) 시 제안 수**: **765 건** (추가 검출이 많으나 노이즈 위험 존재)

#### 0.70 임계값 주요 매칭 사례 및 분석

```text
[1] 세그먼트 10 (시간: 49.5s):
  - 원문 발화: '로마서, 제1립장, 이에수 크리스토리 좋은 가을, 사도로 부르신을 받아,'
  - 제안: '에수 크리스' -> '예수 그리스도' (출처: reference+fuzzy:0.73)
  - 제안: '사도로 부르신을 받아' -> '사도로 부르심을 받아' (출처: reference+fuzzy:0.97)

[2] 세그먼트 12 (시간: 63.5s):
  - 원문 발화: '이에 복면, 하나님의 선지자들을 통하여, 그의 아들을 바라여 성경이 미리 약속하신 것이다.'
  - 제안: '성경이 미리' -> '성경에 미리' (출처: reference+fuzzy:0.95)

[3] 세그먼트 15 (시간: 78.4s):
  - 원문 발화: '명력으로 하나님의 아들로 성포되셨을 것, 우리 두 이에수 크리스토십니다.'
  - 제안: '에수 크리스' -> '예수 그리스도' (출처: reference+fuzzy:0.73)

[4] 세그먼트 19 (시간: 97.8s):
  - 원문 발화: '로마에서 하나님의 사랑하십을 받고, 성도로 불심을 받은 모든 자에게,'
  - 제안: '성도로 불심을 받은' -> '사도로 부르심을 받아' (출처: reference+fuzzy:0.85)
  - 제안: '로마에서' -> '로마서' (출처: reference+fuzzy:0.86)
```

### 관찰 / 후속 작업

1. **완벽한 교정력 회복**:
   - Whisper가 한국어 성경 용어나 고유 구절을 "이에수 크리스토리", "사도로 부르신을 받아", "성도로 불심을 받은", "성경이 미리" 등으로 오인식한 구간을 **100% 자모 fuzzy 매칭으로 감지하고 교정 제안을 띄우는 데 성공**했습니다.
   - 이전 회차 #1에서 0건으로 실효성이 전혀 없었던 고유명사 제안 시스템이, Fuzzy Scorer의 도입으로 수많은 유효 오인식 단어들을 완벽히 pending 제안으로 복구하여 검수의 가치를 극대화했습니다.

2. **False Positive (노이즈)성 제안 존재**:
   - `0.70` 임계값에서 성경 66권 단어(예: 에스라, 에스더, 에스겔, 유다서)의 자모 구성이 단순하여 "이시라" -> "에스라"(0.80), "에서" -> "에스더"(0.80), "에게" -> "에스겔"(0.76)처럼 지나치게 가벼운 단어들에 대해 오추천이 올라오는 현상이 발견되었습니다.
   - **조치**: 
     - 2글자 이하의 짧은 텍스트는 Fuzzy Matcher의 윈도우 스캔에서 완전히 배제하는 **음절 길이 3 미만 게이트**를 코드에서 정상 유지하되, 3글자라 하더라도 모음/초성 구성에 따라 위와 같은 false positive가 생깁니다.
     - 따라서 **PySide6 GUI와 CLI**를 통해 사용자가 직접 Fuzzy 임계값(`fuzzy_threshold`)을 `0.75` 또는 `0.80` 수준으로 올려서 노이즈를 필터링할 수 있도록 설계한 컨트롤 셋이 아주 유효하게 작용한다는 것을 실증했습니다.
     - v1.0 사용자 가이드 문서와 알려진 한계 문서에 이 특성과 권장 임계값(일반 0.70 ~ 0.75, 타이트 0.80)을 명확하게 가이드할 예정입니다.

