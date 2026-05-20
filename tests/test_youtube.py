"""Tests for YouTube audio downloader."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from pulpitink.core.audio.youtube_downloader import (
    download_youtube_audio,
    install_yt_dlp,
    is_yt_dlp_available,
)


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


def test_is_yt_dlp_available_true() -> None:
    # yt_dlp 모듈이 import 가능한 상태로 모킹
    mock_module = MagicMock()
    with patch.dict(sys.modules, {"yt_dlp": mock_module}):
        assert is_yt_dlp_available() is True


def test_is_yt_dlp_available_false() -> None:
    # ImportError를 강제로 발생시켜 False 경로 검증
    import builtins

    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "yt_dlp":
            raise ImportError("simulated missing yt_dlp")
        return real_import(name, *args, **kwargs)

    with patch.object(builtins, "__import__", side_effect=fake_import):
        assert is_yt_dlp_available() is False


@patch("pulpitink.core.audio.youtube_downloader.subprocess.run")
def test_install_yt_dlp_success(mock_run: MagicMock) -> None:
    mock_run.return_value = MagicMock(stdout="Successfully installed yt-dlp", returncode=0)
    assert install_yt_dlp() is True
    mock_run.assert_called_once()
    # pip install yt-dlp 인자를 sys.executable로 호출하는지 확인
    args, kwargs = mock_run.call_args
    cmd = args[0]
    assert cmd[0] == sys.executable
    assert cmd[1:] == ["-m", "pip", "install", "yt-dlp"]
    assert kwargs.get("check") is True


@patch("pulpitink.core.audio.youtube_downloader.subprocess.run")
def test_install_yt_dlp_failure(mock_run: MagicMock) -> None:
    mock_run.side_effect = subprocess.CalledProcessError(
        returncode=1, cmd=["pip", "install", "yt-dlp"], stderr="network error"
    )
    assert install_yt_dlp() is False
