"""Tests for YouTube audio downloader."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from pulpitink.core.audio.youtube_downloader import download_youtube_audio


def test_download_youtube_audio_missing_yt_dlp() -> None:
    # yt-dlp가 import되지 않을 때의 예외를 테스트
    with patch.dict(sys.modules, {"yt_dlp": None}):
        with pytest.raises(ImportError) as exc_info:
            download_youtube_audio("https://youtube.com/watch?v=mock", Path("dummy_dir"))
        assert "yt-dlp" in str(exc_info.value)


@patch("pulpitink.core.audio.youtube_downloader.Path.exists")
def test_download_youtube_audio_success(mock_exists: MagicMock, tmp_path: Path) -> None:
    mock_exists.return_value = True

    # yt_dlp 모킹
    mock_yt_dlp = MagicMock()
    mock_ydl = MagicMock()
    mock_yt_dlp.YoutubeDL.return_value.__enter__.return_value = mock_ydl
    mock_ydl.extract_info.return_value = {"title": "mock_video"}
    mock_ydl.prepare_filename.return_value = str(tmp_path / "mock_video.webm")

    with patch.dict(sys.modules, {"yt_dlp": mock_yt_dlp}):
        # 실제로 path.exists()가 true로 모킹되었으므로 파일 생성을 mock으로 건너뜀
        res = download_youtube_audio("https://youtube.com/watch?v=mock", tmp_path)
        assert res == tmp_path / "mock_video.wav"
        mock_ydl.extract_info.assert_called_once_with("https://youtube.com/watch?v=mock", download=True)
        mock_ydl.prepare_filename.assert_called_once()
