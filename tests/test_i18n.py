"""Tests for lightweight i18n translation framework."""

from __future__ import annotations

from pulpitink.core.utils.i18n import get_language, set_language, tr


def test_i18n_default_language() -> None:
    # 기본 언어는 ko이어야 함 (또는 이전에 설정된 상태일 수 있으므로 테스트 시작시 강제 설정 후 테스트)
    set_language("ko")
    assert get_language() == "ko"


def test_i18n_translation_ko() -> None:
    set_language("ko")
    assert tr("변환 시작") == "변환 시작"
    assert tr("unknown key") == "unknown key"


def test_i18n_translation_en() -> None:
    set_language("en")
    assert get_language() == "en"
    assert tr("변환 시작") == "Start Transcription"
    assert tr("화자 분리 사용 (--diarize)") == "Use Speaker Diarization (--diarize)"
    assert tr("unknown key") == "unknown key"


def test_i18n_yt_dlp_install_keys_en() -> None:
    set_language("en")
    assert tr("yt-dlp 자동 설치") == "Auto-install yt-dlp"
    assert tr("yt-dlp 라이브러리가 준비되었습니다.") == "yt-dlp library is ready."
    assert tr("설치 성공") == "Installation Success"
    assert tr("설치 실패") == "Installation Failed"


def test_i18n_fallback_on_unsupported_language() -> None:
    set_language("fr")  # 지원되지 않는 언어
    assert get_language() == "ko"
    assert tr("변환 시작") == "변환 시작"
