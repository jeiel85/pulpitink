"""Centralised audio enhancement preset definitions.

The goal of these filter chains is NOT to make audio pleasant for human
listening but to make it easier for the STT model to read. Over-processing
hurts accuracy, so the default ``sermon`` preset stays moderate.
"""

from __future__ import annotations

from dataclasses import dataclass

from pulpitink.app.exceptions import PulpitInkError


@dataclass(frozen=True)
class AudioEnhancementPreset:
    """Single FFmpeg filter graph used to prepare an audio file for STT."""

    name: str
    description: str
    ffmpeg_filter: str
    sample_rate: int = 16000
    channels: int = 1


PRESETS: dict[str, AudioEnhancementPreset] = {
    "none": AudioEnhancementPreset(
        name="none",
        description="포맷 변환만 수행 (16kHz mono).",
        ffmpeg_filter="anull",
    ),
    "stt_basic": AudioEnhancementPreset(
        name="stt_basic",
        description="안전한 기본 STT 최적화 (highpass + lowpass + loudnorm).",
        ffmpeg_filter="highpass=f=80,lowpass=f=7800,loudnorm=I=-18:TP=-1.5:LRA=11",
    ),
    "sermon": AudioEnhancementPreset(
        name="sermon",
        description="설교 녹음용 균형 프리셋 (기본값).",
        ffmpeg_filter=(
            "highpass=f=80,"
            "lowpass=f=7500,"
            "afftdn=nf=-25,"
            "dynaudnorm=f=150:g=15,"
            "loudnorm=I=-18:TP=-1.5:LRA=11"
        ),
    ),
    "noisy": AudioEnhancementPreset(
        name="noisy",
        description="잡음이 많은 녹음용 강한 프리셋. 음성이 다소 뭉개질 수 있습니다.",
        ffmpeg_filter=(
            "highpass=f=100,"
            "lowpass=f=6500,"
            "afftdn=nf=-30,"
            "dynaudnorm=f=200:g=20,"
            "loudnorm=I=-18:TP=-1.5:LRA=11"
        ),
    ),
}


def get_preset(name: str) -> AudioEnhancementPreset:
    """Return a preset by name, raising ``PulpitInkError`` on unknown name."""

    try:
        return PRESETS[name]
    except KeyError as exc:
        available = ", ".join(sorted(PRESETS))
        raise PulpitInkError(
            f"알 수 없는 전처리 프리셋입니다: '{name}'. 사용 가능: {available}"
        ) from exc


def build_ffmpeg_filter(preset: AudioEnhancementPreset | str) -> str:
    """Return the filter string for a preset, accepting either object or name."""

    if isinstance(preset, str):
        preset = get_preset(preset)
    return preset.ffmpeg_filter
