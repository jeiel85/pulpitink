# CLI Specification

The CLI should be implemented before the GUI.

## Commands

```bash
pulpit-ink doctor
pulpit-ink transcribe input.mp3
pulpit-ink transcribe input.mp3 --language ko --model medium
pulpit-ink transcribe input.mp3 --preset sermon
pulpit-ink transcribe input.mp3 --output ./exports --format txt,md,json
pulpit-ink transcribe input.mp3 --reference sermon.md
pulpit-ink transcribe input.mp3 --compare-enhancement
pulpit-ink models list
pulpit-ink models download medium
pulpit-ink models remove medium
pulpit-ink licenses check
```

## doctor Checks

- Python version
- OS version
- FFmpeg path
- FFmpeg execution
- CUDA availability
- faster-whisper import
- model cache path
- database path
- write permissions

## Exit Codes

| Code | Meaning |
|---:|---|
| 0 | Success |
| 1 | General failure |
| 2 | Invalid argument |
| 10 | FFmpeg missing |
| 20 | Model missing |
| 30 | STT failed |
| 40 | Export failed |
