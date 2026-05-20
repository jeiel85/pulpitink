# Design Note — 자모(jamo) 기반 fuzzy 매칭

작성: 2026-05-20 (회차 #1 결과 기반)
범위: v1.x 후속 (v1.0 출시 범위 외, [known-limitations §10](../known-limitations.md#10-원문-대조--자동-교정-적중률-v10))
상태: 설계 제안 (PoC 실측 완료, 구현 미착수)

## 1. 문제

`CorrectionEngine.suggestions_for` ([src/sermonscript/core/reference/corrections.py:92](../../src/sermonscript/core/reference/corrections.py)) 는 다음 세 가지 kind 로 교정 후보를 생성합니다.

| kind | 매칭 방식 | 회차 #1 적중 |
| --- | --- | --- |
| `bible_ref` | `normalise_bible_reference` 가 raw_text 를 변환했을 때 | 0건 |
| `user_dict` | `lexicon.wrong_forms` 에 사전 등록된 문자열이 raw_text 에 그대로 등장 | 0건 |
| `proper_noun` | reference proper_nouns 와 raw_text 의 공백 squeeze + 소문자 비교 | 0건 |

회차 #1 (35분 한국어 설교 + Markdown 원문) 결과: **세 kind 모두 0건**. 원문에 35개 proper_nouns 가 추출되었음에도 적중이 없는 이유는 STT 가 다음과 같은 한국어 자모(jamo) 레벨 변형을 내기 때문입니다.

```text
원문 표현            STT raw_text 변형 (회차 #1 빈도)
예수                이에수 (5건)
예수님              이에수님 (1건)
그리스도            크리스토 (5), 그리스토 (3), 그리시도 (2), 크리스도 (1)
예수 그리스도       이에수 크리스토 (4), 예술 그리시도 (1), 예술을 그리시도 (1)
복음                보궁 (4), 보금 (3), 복물 (1), 복면 (1)
사도 바울           사도바울 (2), 사다 바울 (1), 사도 바을 (1)
헬라인              헬라이 (2)
```

사전 등록형(lexicon wrong_forms) 으로는 위 패턴을 망라하기 어렵습니다. 사용자가 매번 새 변형을 본인 사전에 추가해야 하기 때문에 “자동 교정” 의 가치가 거의 없습니다.

## 2. 제약과 비목표

- **신뢰성 유지**: 자동 적용은 금지. 모든 후보는 여전히 `pending` 으로만 저장되고 사용자가 편집기에서 명시적으로 적용/무시.
- **False positive 통제**: 짧은 2자 단어는 fuzzy 매칭 일반 한계로 노이즈가 크므로 보수적으로 처리.
- **온라인 의존성 없음**: 외부 음성/사전 API 호출 없음. 모든 처리는 로컬.
- **언어 일반화 비목표**: 한국어 설교 환경에 한정. 영어/라틴 토큰은 기존 squeeze 비교 유지.

## 3. 실측 (PoC, 2026-05-20)

`unicodedata.normalize('NFD', s)` 로 한글을 자모로 분해한 뒤 `rapidfuzz` 의 세 가지 점수를 비교했습니다. POS 17건 / NEG 7건 (회차 #1 raw_text 에서 추출한 변형 + 의도적 부정 사례).

| scorer | POS 적중 (≥0.65) | NEG 거름 (<0.65) | 비고 |
| --- | --- | --- | --- |
| `fuzz.ratio(jamo(a), jamo(b))` | 12/17 | 7/7 | 짧은 단어 미적중 (예수↔이에수=0.600) |
| `fuzz.partial_ratio(jamo)` | 16/17 | 6/7 | 길이 다른 쌍 강함 / 짧은 토큰에서 false positive 위험 |
| `fuzz.WRatio(jamo)` | 13/17 | 7/7 | 균형 양호 |
| 초성(choseong) `fuzz.ratio` | 16/17 | 7/7 | 모음 변형에 강함, 초성만 같은 다른 단어에 약함 |
| **Hybrid 0.6×ratio + 0.4×cho** | **13/17** | **7/7** | 권장. precision 1.0, recall 0.76 |

**Hybrid 가 잡는 케이스**: 예수, 예수님, 그리스도(4종 변형), 사도, 바울, 사도 바울, 헬라인, 이방인, 예수 그리스도 등.

**Hybrid 가 못 잡는 케이스**: `복음` 의 변형들 (보궁/보금/복물/복면). 2자 단어 + 종성/중성 동시 변화로 자모 거리 큼. **사용자 사전 등록이 정답인 영역**. (v1.x 에서 별도로 `bundled_user_dicts/` 에 사전 페이로드 제공 검토)

부정 사례 거름 (Hybrid):
- 예수 ↔ 여러분 = 0.378
- 복음 ↔ 보고 = 0.440
- 그리스도 ↔ 기독교 = 0.549

## 4. 알고리즘 결정

권장: **Hybrid scorer**

```text
similarity(a, b) =
    0.6 * fuzz.ratio(jamo_seq(a), jamo_seq(b))
  + 0.4 * fuzz.ratio(choseong(a), choseong(b))
```

- `jamo_seq` : `unicodedata.normalize('NFD', s)` 결과에서 공백/제어문자 제거
- `choseong` : 한 글자씩 11172개 한글 음절을 `(ord-0xAC00) // 588` 인덱스로 풀어 CHO 테이블 매핑
- 임계값 디폴트: **0.70** (안전 마진). 사용자가 settings 로 조정 가능.

라이브러리: `rapidfuzz` 는 이미 `[reference]` extra 에 있음. 추가 의존성 없음. `unicodedata` 는 표준 라이브러리.

## 5. 통합 지점

### 5.1 신규 모듈: `core.postprocess.jamo`

```text
src/sermonscript/core/postprocess/
└── jamo.py
    - jamo_seq(s)        -> str
    - choseong(s)        -> str
    - hybrid_similarity(a, b, weights=(0.6, 0.4)) -> float
    - find_fuzzy_matches(text, candidates, threshold=0.7, min_len=3)
        -> Iterator[(snippet, candidate, score)]
```

`min_len=3` 은 “2 글자(한글 음절) 미만 후보는 fuzzy 매칭 대상에서 제외” 라는 안전 장치. 짧은 단어는 사전 등록형 매칭만 허용.

### 5.2 `CorrectionEngine` 통합

기존 `proper_noun` 매칭 ([corrections.py:144](../../src/sermonscript/core/reference/corrections.py)) 의 squeeze 비교를 다음 순서로 확장:

1. 정확 매칭 (현행) — 가장 신뢰도 높음
2. squeeze 매칭 (현행) — 공백/대소문자 변형용
3. **fuzzy 매칭 (신규)** — `find_fuzzy_matches` 의 snippet 을 `proper_noun` kind 로 emit. `source` 필드에 `"reference+fuzzy:<score>"` 기록해 사용자가 결정 근거 확인 가능.

또한 `lexicon` 의 canonical (wrong_forms 가 비어 있는 경우 포함) 도 fuzzy candidate pool 에 포함시켜 “사용자가 표제어만 등록해도 변형 잡아 줌” 효과.

### 5.3 옵션 노출

- `settings.json` 에 두 키 추가 (기본값 보수적):
  ```json
  {
    "fuzzy_matching_enabled": true,
    "fuzzy_threshold": 0.70
  }
  ```
- CLI: `sermonscript transcribe ... --fuzzy-threshold 0.65` / `--no-fuzzy`
- GUI: 설정 패널에 토글 + 슬라이더(0.6~0.9)

### 5.4 데이터/스키마 영향

- 새 컬럼/테이블 없음. `correction_suggestions.kind` 는 그대로 `proper_noun` 사용.
- `source` 컬럼은 `TEXT` 라 `"reference+fuzzy:0.72"` 같이 점수를 함께 적어도 호환.
- 마이그레이션 불필요.

## 6. 거짓 양성 통제

회차 #1 의 짧은 토큰 false positive 위험을 줄이기 위해:

1. **길이 게이트**: 후보 길이 < 3 음절 → fuzzy 제외 (정확 매칭만)
2. **이중 통과 요구**: `jamo.ratio < 0.5` 이면 hybrid 점수가 높아도 제외
3. **중복 제거**: 한 세그먼트 내 동일 (kind, original) 쌍은 한 번만 emit (현행 동작 유지)
4. **threshold 보수적 디폴트** 0.70

## 7. 회귀/검증 계획

- **단위 테스트** (`tests/test_jamo_matching.py`):
  - POS 17건 / NEG 7건 표를 fixture 로 등록해 임계값 변화 시 swing 모니터링
  - 길이 게이트 동작 확인 (`복음 ↔ 보궁` 은 정확히 미적중 expected)
- **회귀 테스트** (`tests/test_correction_engine.py`):
  - 기존 정확/squeeze 매칭이 그대로 동작
  - 새 fuzzy 케이스 1~2건 추가
- **통합 회차 #2** (`tests/integration/results.md`):
  - 같은 입력 재실행해 `correction_suggestions` 개수와 kind 분포 비교
  - 목표: pending 30건 이상, 사용자 검수 가치 발생

## 8. 작업 단위 (v1.x)

| 단계 | 내용 | 추정 |
| --- | --- | --- |
| A | `core.postprocess.jamo` 모듈 + 단위 테스트 | S (반나절) |
| B | `CorrectionEngine` fuzzy 통합 + 단위 테스트 갱신 | M (하루) |
| C | settings + CLI 옵션 노출 | S (반나절) |
| D | GUI 설정 패널 토글/슬라이더 | M (하루) |
| E | `docs/user-guide.md` §6 갱신, `known-limitations.md` §10 갱신 | S |
| F | 통합 회차 #2 실행 + 결과 기록 | S |

총 **~3.5 일** (실작업 기준).

## 9. 의사결정 필요 항목

1. **디폴트 활성화?** v1.x 출시에서 `fuzzy_matching_enabled=true` 가 기본인지, 옵션 켜야 동작인지. 권장: **true** + threshold 0.70 (false positive 통제 가능 수준). 회귀에서 사용자 불만 들리면 0.75 상향.
2. **`복음` 류 짧은 변형**을 `core.postprocess.lexicon._DEFAULT_SERMON_TERMS` 에 wrong_forms 로 사전 등록할지. 결정에 따라 fuzzy 미적중 영역을 일부 메울 수 있음. 권장: 회차 #2 이후 데이터 추가 수집 후 결정.
3. **v1.0 출시 일정에 묶을지 / v1.1 로 미룰지**. 권장: **v1.1** (현재 알려진 한계로 문서화하고 v1.0 은 안정성/문서 마무리에 집중).

## 10. 참고

- 회차 #1 실측 데이터 추출: [tests/integration/results.md](../../tests/integration/results.md)
- 현행 매칭 코드: [src/sermonscript/core/reference/corrections.py](../../src/sermonscript/core/reference/corrections.py)
- 현행 lexicon: [src/sermonscript/core/postprocess/lexicon.py](../../src/sermonscript/core/postprocess/lexicon.py)
- PoC 스크립트 (커밋 안 함, 본 노트의 §3 표 산출): 작업 디렉터리에서 인라인 실행. 재현 필요 시 본 노트 §4 알고리즘으로 1시간 내 재구성 가능.
