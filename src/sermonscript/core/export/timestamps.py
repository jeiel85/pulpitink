"""Timestamp formatting helpers for SRT/VTT output."""

from __future__ import annotations


def _split_seconds(seconds: float) -> tuple[int, int, int, int]:
    if seconds is None or seconds != seconds:  # NaN guard
        seconds = 0.0
    if seconds < 0:
        seconds = 0.0
    total_ms = int(round(seconds * 1000))
    hours, rest = divmod(total_ms, 3_600_000)
    minutes, rest = divmod(rest, 60_000)
    secs, millis = divmod(rest, 1000)
    return hours, minutes, secs, millis


def format_srt_timestamp(seconds: float) -> str:
    """Return ``HH:MM:SS,mmm`` as required by SRT."""

    h, m, s, ms = _split_seconds(seconds)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def format_vtt_timestamp(seconds: float) -> str:
    """Return ``HH:MM:SS.mmm`` as required by WebVTT."""

    h, m, s, ms = _split_seconds(seconds)
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"
