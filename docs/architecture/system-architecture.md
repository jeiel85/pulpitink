# System Architecture

## 1. Recommended Stack

| Layer | Technology |
|---|---|
| Language | Python 3.11+ |
| GUI | PySide6 |
| CLI | Typer |
| STT | faster-whisper |
| Optional STT | whisper.cpp |
| Audio preprocessing | FFmpeg |
| VAD | Silero VAD, optional |
| DB | SQLite |
| Config | JSON or TOML |
| Packaging | PyInstaller |
| Installer | Inno Setup or NSIS |

## 2. High-level Architecture

```text
┌──────────────────────────────────────────────┐
│                  PySide6 GUI                 │
│ MainWindow / JobList / TranscriptEditor      │
└──────────────────────┬───────────────────────┘
                       │
┌──────────────────────▼───────────────────────┐
│              Application Services             │
│ JobService / SettingsService / ModelService   │
└──────────────────────┬───────────────────────┘
                       │
┌──────────────────────▼───────────────────────┐
│              Processing Pipeline              │
│ Analyze → Enhance → Split → Transcribe        │
└──────────────────────┬───────────────────────┘
                       │
┌──────────────────────▼───────────────────────┐
│                STT Engine Layer               │
│ faster-whisper / whisper.cpp adapters         │
└──────────────────────┬───────────────────────┘
                       │
┌──────────────────────▼───────────────────────┐
│              Post-processing Layer            │
│ Dictionary / Bible refs / paragraphs / diff   │
└──────────────────────┬───────────────────────┘
                       │
┌──────────────────────▼───────────────────────┐
│              Storage and Export               │
│ SQLite / TXT / MD / SRT / VTT / JSON / PDF    │
└──────────────────────────────────────────────┘
```

## 3. Design Principles

### Local-first

Default processing happens on the user's PC.

### Original Preservation

The original audio file must never be modified. All generated files are stored as cache or explicit exports.

### Engine Abstraction

STT engines must be behind a common interface. This allows the app to support faster-whisper first and whisper.cpp later.

### Review-first Workflow

The app should not claim perfect transcription. It should produce a good first draft and make correction fast.

### Source Traceability

Raw STT, cleaned text, and manually edited text should be stored separately.

```text
raw_text      = direct STT result
clean_text    = rule-based corrected result
edited_text   = user-approved final text
```
