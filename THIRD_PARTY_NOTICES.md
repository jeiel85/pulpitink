# Third Party Notices

이 파일은 릴리즈 전에 실제 사용 의존성 기준으로 반드시 갱신해야 합니다.

## Planned Dependencies

| Name | Purpose | Notice |
|---|---|---|
| Python | Runtime | Check Python Software Foundation License |
| PySide6 | GUI | Check Qt for Python license terms |
| faster-whisper | STT | Check upstream license |
| CTranslate2 | Inference backend | Check upstream license |
| FFmpeg | Audio/video processing | Check LGPL/GPL build configuration |
| Typer | CLI | Check upstream license |
| Rich | CLI output | Check upstream license |
| Pydantic | Data validation | Check upstream license |
| platformdirs | App paths | Check upstream license |
| pytest | Test | Check upstream license |
| ruff | Lint/format | Check upstream license |
| RapidFuzz | Reference alignment | Check upstream license |

## Distribution Policy

- Model files are not committed to the repository.
- FFmpeg binaries are not included by default.
- If FFmpeg is bundled in a release, the exact build and license terms must be documented.
