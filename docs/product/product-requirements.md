# Product Requirements Document

## 1. Product Name

**SermonScript**

## 2. One-line Description

A local-first desktop transcription app for converting sermon, lecture, meeting, and interview recordings into reviewable text.

## 3. Target Users

| User | Use Case |
|---|---|
| Pastor | Convert sermon recordings into text manuscripts |
| Church media team | Generate sermon subtitles, blog posts, archive text |
| Lecturer | Convert lecture recordings into notes |
| Researcher | Transcribe interview recordings |
| General user | Transcribe long voice recordings |

## 4. Core Problem

Generic STT tools produce rough text, but long sermon recordings require:

- Audio enhancement before transcription
- Bible reference correction
- Custom dictionary for religious and theological terms
- Manuscript/reference alignment
- Timestamp-based review
- Export into practical church/media formats

## 5. Product Goals

1. Process 30-90 minute recordings reliably on a PC.
2. Generate a reviewable first transcript.
3. Reduce manual correction time through audio preprocessing and reference-assisted correction.
4. Preserve the original audio and the raw STT result.
5. Provide usable export formats for ministry, study, subtitles, and archiving.

## 6. Product Modes

### General Transcription Mode

Input: audio/video file. Output: transcript with timestamps.

### Enhanced Transcription Mode

Input: audio/video file plus selected audio preprocessing preset. Output: transcript generated from STT-optimized audio.

### Reference-assisted Transcription Mode

Input: audio/video file plus sermon manuscript, outline, Bible passage, or notes. Output: transcript aligned with reference text, correction suggestions, and reviewable diff.

### Training Dataset Export Mode

Input: reviewed transcript, timestamped segments, and audio file. Output: segment-level audio/text pairs for future fine-tuning experiments.

## 7. v1.0 Scope

Must include:

- Windows desktop app
- CLI engine
- FFmpeg audio preprocessing
- faster-whisper STT
- Job history
- Timestamp editor
- TXT/MD/SRT/VTT/JSON export
- Model selection
- Local settings
- Windows installer and portable ZIP
- Open-source documentation and license notices

Should include:

- User dictionary
- Bible reference normalization
- Reference text prompt generation

Won't include:

- Mobile app
- Cloud AI summary
- Fully automated fine-tuning
