# License Policy

This document is a planning guide, not legal advice. Review each dependency license before release.

## App License

Recommended app license:

```text
Apache-2.0
```

Reasons:

- Permissive open-source license
- Commercial use allowed
- Patent grant included
- Good fit for public GitHub projects

## Dependency Notes

| Component | Notes |
|---|---|
| OpenAI Whisper | MIT License in official GitHub repository |
| faster-whisper | Check official repository license before each release |
| FFmpeg | LGPL 2.1+ by default; optional GPL parts may apply |
| PySide6 / Qt for Python | Open-source licensing includes LGPL/GPL options; commercial license also exists |
| PyInstaller | GPL with special exception for distributing built apps |
| Silero VAD | MIT license reported by official/open repository pages |
| whisper.cpp | MIT license reported by repository/package listings; verify repository LICENSE before bundling |

## Distribution Rules

- Do not commit model weights to the repository.
- Do not commit FFmpeg binaries to the source repository.
- If bundling FFmpeg in release artifacts, identify the exact build and license.
- Preserve upstream copyright notices.
- Maintain `THIRD_PARTY_NOTICES.md`.
- Maintain `docs/model-policy.md`.
- Provide clear instructions for replacing or updating bundled binaries.
