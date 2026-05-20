# Integration Scenario — 35분 설교 MP3 + 원문 대조

본 디렉터리는 자동화된 pytest 가 아니라 **수동 회귀 시나리오** 입니다.
[docs/release/release-checklist.md](../../docs/release/release-checklist.md) 의
"30분 분량 MP3 변환 + Export 검증" 과 "원문 대조 워크플로우" 항목을 만족하기
위한 절차/입력/관찰 결과를 한곳에 남깁니다.

실제 오디오 파일은 저작권상 커밋하지 않습니다. 변환 입력은 **로컬 경로** 로만
지정하고, 추출된 원문(`fixtures/sermon.md`) 만 저장소에 함께 둡니다.

## 입력

| 항목 | 경로 | 비고 |
| --- | --- | --- |
| 오디오 | `D:\Media\2026-05-13 수요밤설교 _ 로마서 1장 1-15절 _ 로마서의 서론.mp3` | 35분 45초, 129kbps, MP3 |
| 원문(docx) | `D:\Media\2026-05-13 수요밤설교 _ 로마서 1장 1-15절 _ 로마서의 서론.docx` | 변환 전 원본 |
| 원문(md) | `tests/integration/fixtures/sermon.md` | docx → md (236문단, ~9.7KB) |

`extract_docx.py` 는 외부 의존성 없이 (zip + xml 파싱) docx → md 변환에만 사용합니다.

## 실행

PowerShell 기준:

```powershell
python -m sermonscript.cli.main transcribe `
  "D:\Media\2026-05-13 수요밤설교 _ 로마서 1장 1-15절 _ 로마서의 서론.mp3" `
  --reference tests/integration/fixtures/sermon.md `
  --language ko `
  --model small `
  --preset sermon `
  --format txt,json,md,srt,vtt `
  --output tests/integration/out
```

변환 후 확인:

```powershell
python -m sermonscript.cli.main jobs list --limit 5
python -m sermonscript.cli.main jobs show <job-id>
python -m sermonscript.cli.main corrections list <job-id>
```

## 검증 항목

- [x] 전처리: `cache/jobs/<job-id>/processed.wav` 생성 (16kHz mono)
- [x] STT: 세그먼트가 DB 의 `segments` 테이블에 기록되고 `raw_text` 비어 있지 않음
- [ ] 후처리: `clean_text` 가 `raw_text` 와 다른 세그먼트가 존재 — **실제 회차 #1에서 0건**. lexicon wrong_forms 사전등록형 한계 ([results.md](results.md))
- [x] Export: `out/<stem>.{txt,json,md,srt,vtt}` 5개 모두 생성
- [x] 원문 대조: `reference_documents` 1건, `alignment_pairs` 11건 (`correction_suggestions` 는 아래 참고)
- [ ] 교정 후보: 최소 1건 이상 pending 으로 저장됨 — **실제 회차 #1에서 0건**. v1.1 후속 ([tasks #12](../../HISTORY.md))
- [x] `raw_text` 가 절대 수정되지 않음 (스키마/리포지터리 차원에서 enforce)
- [x] CLI `corrections apply` 가 `edited_text` 만 갱신 (회귀 테스트로 보장)
- [x] 재export(`jobs export`) 가 `edited_text > clean_text > raw_text` 우선순위 적용 (회귀 테스트로 보장)

## 결과 기록

회차별 관찰은 [results.md](results.md) 에 누적 기록합니다.
