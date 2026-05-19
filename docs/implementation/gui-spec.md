# GUI Specification

## Main Window

```text
┌────────────────────────────────────────────────────┐
│ SermonScript                                       │
├────────────────────────────────────────────────────┤
│ [Add File] [Add Folder] [Start] [Settings] [Export]│
├────────────────────────────────────────────────────┤
│ Job List                                           │
│ 2026-05-13_sermon.mp3                              │
│ Length 35:44 / Korean / medium / Sermon preset     │
├────────────────────────────────────────────────────┤
│ Audio Analysis                                     │
│ Loudness: Low / Noise: Medium / Recommendation     │
├────────────────────────────────────────────────────┤
│ Progress                                           │
│ ███████████░░░░░ 68%                               │
│ Current segment: 00:24:12 - 00:25:03               │
├────────────────────────────────────────────────────┤
│ Transcript Editor                                  │
│ [Raw] [Clean] [Edited] [Review Needed] [Search]    │
│ 00:00:01 오늘은 로마서 1장 1절부터...             │
└────────────────────────────────────────────────────┘
```

## Transcript Editor Required Features

- Segment list with timestamps
- Edit text per segment
- Auto-save
- Search and replace
- Filter by `needs_review`
- Click segment to play audio
- Keyboard shortcuts

## Reference Alignment View

Two-column layout:

```text
Left: STT transcript
Right: sermon manuscript/reference
Bottom: suggestions
```

Actions:

- Apply
- Ignore
- Always apply
- Add to dictionary
- Jump to audio
