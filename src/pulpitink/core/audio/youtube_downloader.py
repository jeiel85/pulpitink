"""YouTube audio downloader helper using yt-dlp.

Dynamically imports 'yt-dlp' to prevent hard crashes if the library is not installed
on the user's system, raising a helpful error message instead.
"""

from __future__ import annotations

import logging
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger("pulpitink.youtube")


def is_yt_dlp_available() -> bool:
    """Check if yt-dlp library is installed and importable."""
    try:
        import yt_dlp  # noqa: F401
        return True
    except ImportError:
        return False


def install_yt_dlp() -> bool:
    """Install yt-dlp using python's pip module synchronously.

    Usually called from background worker threads to prevent UI freezes.
    """
    logger.info("Attempting to auto-install yt-dlp via pip...")
    try:
        # Use sys.executable to run pip in the same python environment
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "yt-dlp"],
            capture_output=True,
            text=True,
            check=True,
        )
        logger.info("yt-dlp auto-install successful: %s", result.stdout)
        return True
    except Exception:
        logger.exception("Failed to auto-install yt-dlp")
        return False


def download_youtube_audio(url: str, output_dir: Path) -> Path:
    """Download audio track from a YouTube URL and extract it as WAV.

    Returns the path to the downloaded WAV file.
    """
    try:
        import yt_dlp
    except ImportError as exc:
        raise ImportError(
            "YouTube 다운로드 기능을 사용하려면 'yt-dlp' 패키지가 필요합니다.\n"
            "터미널에서 'pip install yt-dlp' 명령을 통해 라이브러리를 설치해 주세요."
        ) from exc

    output_dir.mkdir(parents=True, exist_ok=True)

    # yt-dlp options to download best audio and post-process to wav
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": str(output_dir / "%(title)s.%(ext)s"),
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
                "preferredquality": "192",
            }
        ],
        "quiet": True,
        "no_warnings": True,
    }

    logger.info("YouTube audio download requested: %s", url)
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            # Since FFmpegExtractAudio post-processes to .wav, replacing the extension is correct.
            wav_path = Path(filename).with_suffix(".wav")
            if not wav_path.exists():
                # In some cases, prepare_filename might not exactly match the actual post-processed filename if it had double extension or similar
                # Check for any .wav with the same base name
                base_pattern = Path(filename).stem
                for p in output_dir.glob(f"{base_pattern}*.wav"):
                    wav_path = p
                    break

            if not wav_path.exists():
                raise FileNotFoundError(f"추출된 WAV 오디오 파일을 찾을 수 없습니다: {wav_path}")

            logger.info("YouTube audio successfully downloaded and extracted: %s", wav_path)
            return wav_path
    except Exception as exc:
        logger.exception("Failed to download YouTube audio from %s", url)
        raise RuntimeError(f"YouTube 오디오 다운로드 중 오류가 발생했습니다: {exc}") from exc

