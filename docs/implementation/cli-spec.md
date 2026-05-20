# CLI Specification

The CLI should be implemented before the GUI.

## Commands

```bash
PulpitInk doctor
PulpitInk transcribe input.mp3
PulpitInk transcribe input.mp3 --language ko --model medium
PulpitInk transcribe input.mp3 --preset sermon
PulpitInk transcribe input.mp3 --output ./exports --format txt,md,json
PulpitInk transcribe input.mp3 --reference sermon.md
PulpitInk transcribe input.mp3 --compare-enhancement
PulpitInk models list
PulpitInk models download medium
PulpitInk models remove medium
PulpitInk licenses check
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
