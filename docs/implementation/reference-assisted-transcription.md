# Reference-assisted Transcription

## Purpose

If the user has a sermon manuscript, outline, Bible passage, or notes, the app can improve the workflow by using that reference before and after STT.

The reference text is not the final truth. Actual speech should be preserved when the preacher deviates from the manuscript.

## Modes

### Prompt-assisted STT

Extract short hints from the reference and pass them as `initial_prompt`.

Use:

- Sermon title
- Bible passage
- Key terms
- Names
- Theological terms

Do not pass the entire manuscript as a prompt.

### Post-STT Alignment

Align STT segments with reference paragraphs and suggest corrections.

### Dataset Export

After user review, export verified audio/text pairs for future fine-tuning experiments.

## Safe Correction Policy

| Category | Auto-apply? |
|---|---|
| Bible book names | Yes, with high confidence |
| Bible chapter/verse notation | Yes, with high confidence |
| Known dictionary terms | Optional |
| Person/church names | Ask user first |
| General sentence differences | Never auto-apply |
| Added live speech not in manuscript | Preserve |

## UI Requirement

Add a two-column review screen:

```text
Left: STT transcript with timestamps
Right: sermon manuscript/reference
Bottom: correction suggestions
```

Suggestion actions:

- Apply
- Ignore
- Always apply
- Add to dictionary
