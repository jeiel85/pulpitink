# Third-party References

Use this file as a working reference checklist.

## Sources to Check Before Release

- OpenAI Whisper License: https://github.com/openai/whisper/blob/main/LICENSE
- FFmpeg Legal: https://ffmpeg.org/legal.html
- Qt Licensing: https://doc.qt.io/qt-6/licensing.html
- PySide6 PyPI: https://pypi.org/project/PySide6/
- PyInstaller License: https://pyinstaller.org/en/stable/license.html
- faster-whisper repository: https://github.com/SYSTRAN/faster-whisper
- Silero VAD repository: https://github.com/snakers4/silero-vad
- whisper.cpp repository: https://github.com/ggml-org/whisper.cpp

## Release Checklist

- [ ] Re-check dependency licenses.
- [ ] Re-check model licenses.
- [ ] Update THIRD_PARTY_NOTICES.md.
- [ ] Confirm FFmpeg distribution policy.
- [ ] Confirm PySide6 packaging approach.
- [ ] Confirm no model weights are committed.
- [ ] Confirm no private audio samples are committed.
