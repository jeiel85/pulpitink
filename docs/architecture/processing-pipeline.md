# Processing Pipeline

## Standard Pipeline

```text
1. Import audio file
2. Analyze metadata and audio quality
3. Select or recommend preprocessing preset
4. Generate STT-optimized WAV
5. Segment by silence or VAD
6. Run STT engine
7. Merge timestamped segments
8. Apply post-processing
9. Align with sermon reference text if provided
10. Generate correction suggestions
11. Save job and segments
12. Display transcript editor
13. Export selected formats
```

## Pipeline Artifacts

```text
job_cache/{job_id}/
  metadata.json
  processed.wav
  segments.raw.json
  segments.clean.json
  alignment.json
  suggestions.json
  logs.txt
```

## Failure Handling

| Failure | Handling |
|---|---|
| FFmpeg missing | Show doctor result and installation guide |
| Model missing | Ask user to download model |
| CUDA unavailable | Fallback to CPU |
| Unsupported file | Try FFmpeg probe, then fail with clear message |
| Out of memory | Suggest smaller model or CPU int8 |
| Empty STT output | Suggest different preprocessing preset |
