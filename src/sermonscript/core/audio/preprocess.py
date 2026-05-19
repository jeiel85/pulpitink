from pathlib import Path
import subprocess

from sermonscript.core.audio.enhancement_presets import PRESETS


def preprocess_audio(input_path: str, output_path: str, preset_key: str = "sermon") -> Path:
    preset = PRESETS[preset_key]

    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-ac", str(preset.channels),
        "-ar", str(preset.sample_rate),
        "-af", preset.ffmpeg_filter,
        output_path,
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg preprocessing failed:
{result.stderr}")

    return Path(output_path)
