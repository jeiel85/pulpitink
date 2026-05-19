# Post-processing Design

## Text Layers

Each segment stores three text fields:

```text
raw_text     = direct STT output
clean_text   = rule-based corrected output
edited_text  = user-approved final text
```

## User Dictionary

Suggested file:

```yaml
terms:
  - canonical: "로마서"
    variants:
      - "로마 써"
      - "로마 서"

  - canonical: "고린도전서"
    variants:
      - "고린도 전서"
      - "고린도전 써"

  - canonical: "데살로니가"
    variants:
      - "데살로니까"
      - "데살로니카"

  - canonical: "칭의"
    variants:
      - "칭이"
      - "친의"
```

## Bible Reference Normalization

Normalize patterns such as:

```text
로마서 일장 일절
로마서 1 장 1 절
로마서 1장 일절
로마 써 일장 일절
```

Into:

```text
로마서 1장 1절
```

## Review Flags

A segment should be marked `needs_review` if:

- avg_logprob is low
- no_speech_prob is high
- the segment contains unknown terms
- the text is very short despite long audio duration
- reference alignment score is low
- STT result conflicts with likely Bible reference
