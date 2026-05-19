# Export Formats

## TXT

Plain text, no timestamps by default.

Options:

- Include timestamps
- Export raw STT
- Export cleaned text
- Export edited text

## Markdown

```md
# {title}

- Date: {date}
- Passage: {bible_passage}
- Source: {source_filename}
- Model: {model_name}

## Transcript

[00:00:01] ...
```

## SRT

```srt
1
00:00:01,000 --> 00:00:05,300
오늘은 로마서 1장 1절부터 보겠습니다.
```

## VTT

```vtt
WEBVTT

00:00:01.000 --> 00:00:05.300
오늘은 로마서 1장 1절부터 보겠습니다.
```

## JSON

```json
{
  "job_id": "uuid",
  "source_path": "sermon.mp3",
  "language": "ko",
  "model": "medium",
  "segments": [
    {
      "start": 1.0,
      "end": 5.3,
      "raw_text": "오늘은 로마서...",
      "clean_text": "오늘은 로마서...",
      "edited_text": "오늘은 로마서...",
      "needs_review": false
    }
  ]
}
```
