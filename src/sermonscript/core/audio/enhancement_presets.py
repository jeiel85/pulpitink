from dataclasses import dataclass


@dataclass(frozen=True)
class AudioEnhancementPreset:
    name: str
    description: str
    ffmpeg_filter: str
    sample_rate: int = 16000
    channels: int = 1


PRESETS = {
    "none": AudioEnhancementPreset(
        name="none",
        description="Format conversion only.",
        ffmpeg_filter="anull",
    ),
    "stt_basic": AudioEnhancementPreset(
        name="stt_basic",
        description="Safe preprocessing for speech recognition.",
        ffmpeg_filter="highpass=f=80,lowpass=f=7800,loudnorm=I=-18:TP=-1.5:LRA=11",
    ),
    "sermon": AudioEnhancementPreset(
        name="sermon",
        description="Balanced enhancement for sermon recordings.",
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
        description="Stronger noise reduction. May slightly distort speech.",
        ffmpeg_filter=(
            "highpass=f=100,"
            "lowpass=f=6500,"
            "afftdn=nf=-30,"
            "dynaudnorm=f=200:g=20,"
            "loudnorm=I=-18:TP=-1.5:LRA=11"
        ),
    ),
}
