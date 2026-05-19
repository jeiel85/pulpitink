# CLI Specification

The CLI should be implemented before the GUI.

## Commands

```bash
sermonscript doctor
sermonscript transcribe input.mp3
sermonscript transcribe input.mp3 --language ko --model medium
sermonscript transcribe input.mp3 --preset sermon
sermonscript transcribe input.mp3 --output ./exports --format txt,md,json
sermonscript transcribe input.mp3 --reference sermon.md
sermonscript transcribe input.mp3 --compare-enhancement
sermonscript models list
sermonscript models download medium
sermonscript models remove medium
sermonscript licenses check
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
