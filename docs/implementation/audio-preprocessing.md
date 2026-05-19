# Audio Enhancement Pipeline

## Goal

The goal is not to make audio pleasant for human listening. The goal is to make speech clearer for STT models.

## Why It Matters

Sermon recordings often include room echo, low microphone gain, fan noise, air-conditioner noise, long silence, sudden loud sounds, distant voice, and sanctuary reverb.

## FFmpeg-first Strategy

For v1.0, use FFmpeg filter chains. This is practical, fast, and deployable.

Important filters:

- `highpass`
- `lowpass`
- `afftdn`
- `loudnorm`
- `dynaudnorm`

## Presets

### None

```text
anull
```

### STT Basic

```text
highpass=f=80,lowpass=f=7800,loudnorm=I=-18:TP=-1.5:LRA=11
```

### Sermon

```text
highpass=f=80,lowpass=f=7500,afftdn=nf=-25,dynaudnorm=f=150:g=15,loudnorm=I=-18:TP=-1.5:LRA=11
```

### Noisy

```text
highpass=f=100,lowpass=f=6500,afftdn=nf=-30,dynaudnorm=f=200:g=20,loudnorm=I=-18:TP=-1.5:LRA=11
```

Use with warning: speech may become muffled.

## UI Requirement

The user should be able to choose:

- No enhancement
- STT Basic
- Sermon
- Noisy Recording
- Custom

Also add:

- Compare original vs enhanced transcription
- Save processed WAV
- Auto-delete processed WAV after export
