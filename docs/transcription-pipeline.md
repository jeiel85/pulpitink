# Transcription Pipeline

## 1. 기본 흐름

```text
입력 파일
→ 오디오 분석
→ 전처리
→ STT
→ 세그먼트 병합
→ 후처리
→ 저장
→ Export
```

## 2. STT 엔진

v1.0 기본 엔진:

```text
faster-whisper
```

후보 엔진:

```text
whisper.cpp
```

## 3. 기본 옵션

```text
language: ko
model: medium
device: auto
compute_type: int8
beam_size: 5
vad_filter: true
preset: sermon
```

## 4. 모델 선택

| 목적 | 모델 |
|---|---|
| 테스트 | tiny |
| 저사양 PC | base |
| 균형 | small |
| 설교 실사용 | medium |
| 정확도 우선 | large-v3 |

## 5. 세그먼트 데이터

```json
{
  "start": 1.0,
  "end": 5.3,
  "raw_text": "오늘은 로마서 1장...",
  "clean_text": "",
  "edited_text": "",
  "needs_review": false
}
```

## 6. 보존 원칙

```text
raw_text는 STT 원문입니다.
clean_text는 후처리 결과입니다.
edited_text는 사용자가 수정한 최종 후보입니다.
```

`raw_text`는 절대 덮어쓰지 않습니다.
