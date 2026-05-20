"""FFmpeg-based audio preprocessing.

Wraps ``ffmpeg`` invocations so the rest of the codebase can stay agnostic of
the exact CLI flags. All preprocessing writes a 16 kHz mono WAV to the job's
cache directory and never modifies the original audio file.
"""

from __future__ import annotations

import logging
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from sermonscript.app.exceptions import FFmpegError
from sermonscript.core.audio.enhancement_presets import (
    AudioEnhancementPreset,
    get_preset,
)

DEFAULT_PRESET = "sermon"

logger = logging.getLogger("sermonscript.audio.ffmpeg")


@dataclass(frozen=True)
class FFmpegCheck:
    available: bool
    executable: str | None
    version_line: str | None
    error: str | None = None


class FFmpegRunner:
    """Thin wrapper around the ``ffmpeg`` CLI for preprocessing."""

    def __init__(self, executable: str | None = None) -> None:
        self.executable = executable or shutil.which("ffmpeg") or "ffmpeg"

    def check(self) -> FFmpegCheck:
        """Return whether ``ffmpeg`` can be located and executed."""

        path = shutil.which(self.executable) or (
            self.executable if Path(self.executable).exists() else None
        )
        if not path:
            return FFmpegCheck(False, None, None, error="ffmpeg 실행 파일을 찾을 수 없습니다.")

        try:
            result = subprocess.run(
                [path, "-version"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
                timeout=10,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            return FFmpegCheck(False, path, None, error=str(exc))

        if result.returncode != 0:
            return FFmpegCheck(False, path, None, error=result.stderr.strip() or "unknown error")

        first_line = (result.stdout or "").splitlines()[0:1]
        return FFmpegCheck(True, path, first_line[0] if first_line else None)

    def preprocess(
        self,
        input_path: Path,
        output_path: Path,
        preset: AudioEnhancementPreset | str = DEFAULT_PRESET,
        *,
        overwrite: bool = True,
    ) -> Path:
        """Run FFmpeg to produce a 16 kHz mono WAV at ``output_path``."""

        check = self.check()
        if not check.available:
            raise FFmpegError(
                "FFmpeg 실행 파일을 찾을 수 없습니다. "
                "https://ffmpeg.org 에서 설치 후 PATH에 등록하세요."
            )

        if isinstance(preset, str):
            preset_obj = get_preset(preset)
        else:
            preset_obj = preset

        output_path.parent.mkdir(parents=True, exist_ok=True)

        cmd = [
            check.executable or self.executable,
            "-hide_banner",
            "-nostdin",
            "-loglevel", "error",
            "-y" if overwrite else "-n",
            "-i", str(input_path),
            "-vn",
            "-ac", str(preset_obj.channels),
            "-ar", str(preset_obj.sample_rate),
            "-af", preset_obj.ffmpeg_filter,
            "-f", "wav",
            str(output_path),
        ]

        logger.debug("FFmpeg command: %s", " ".join(cmd))
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )
        except OSError as exc:
            raise FFmpegError(f"FFmpeg 실행 중 오류가 발생했습니다: {exc}") from exc

        if result.returncode != 0:
            stderr = _summarise_stderr(result.stderr)
            raise FFmpegError(
                "FFmpeg 전처리에 실패했습니다.\n"
                f"명령: {' '.join(cmd)}\n"
                f"메시지: {stderr}"
            )

        return output_path


def _summarise_stderr(text: str, *, max_lines: int = 12) -> str:
    """Trim FFmpeg stderr to a reasonable, user-readable summary."""

    lines = [line.rstrip() for line in (text or "").splitlines() if line.strip()]
    if not lines:
        return "(빈 stderr)"
    if len(lines) <= max_lines:
        return "\n".join(lines)
    head = lines[: max_lines - 4]
    tail = lines[-4:]
    return "\n".join([*head, "...", *tail])


def preprocess_audio(
    input_path: str | Path,
    output_path: str | Path,
    preset_key: str = DEFAULT_PRESET,
) -> Path:
    """Convenience wrapper used by tests and simple callers."""

    runner = FFmpegRunner()
    return runner.preprocess(Path(input_path), Path(output_path), preset_key)
