"""Lightweight i18n helper for PulpitInk.

Provides a simple translate dictionary interface to support 'ko' and 'en'
without overhead, falling back gracefully to key text when translation is missing.
"""

from __future__ import annotations

import logging

logger = logging.getLogger("pulpitink.i18n")

_current_lang = "ko"

# Main dictionary mapping Korean UI strings (as keys) to English (as values)
TRANSLATIONS: dict[str, str] = {
    "변환 시작": "Start Transcription",
    "최근 작업": "Recent Jobs",
    "설정": "Settings",
    "작업 대기열": "Job Queue",
    "파일 추가": "Add File",
    "YouTube 주소 추가": "Add YouTube URL",
    "전처리 프리셋": "Preprocessing Preset",
    "음성인식 모델": "STT Model",
    "인식 언어": "Transcription Language",
    "성경 구절 교정 (Fuzzy)": "Bible Verse Correction (Fuzzy)",
    "임계값": "Threshold",
    "최근 작업 기록 저장": "Save Recent Job History",
    "인터페이스 언어": "Interface Language",
    "저장": "Save",
    "닫기": "Close",
    "도움말": "Help",
    "준비됨": "Ready",
    "변환 중...": "Transcribing...",
    "완료": "Completed",
    "실패": "Failed",
    "작업 및 캐시 삭제": "Delete Job and Cache",
    "삭제하시겠습니까?": "Are you sure you want to delete?",
    "경고": "Warning",
    "오류": "Error",
    "성공": "Success",
    "알림": "Notification",
    "상태": "Status",
    "작업 ID": "Job ID",
    "파일명": "File Name",
    "크기": "Size",
    "등록시간": "Registered Time",
    "진행률": "Progress",
    "변환 텍스트": "Transcribed Text",
    "검색": "Search",
    "치환": "Replace",
    "모두 치환": "Replace All",
    "원문 대조 교정": "Reference-Based Correction",
    "대조 원문 텍스트": "Reference Text",
    "교정 제안 적용": "Apply Corrections",
    "교정 제안": "Correction Suggestions",
    "내보내기": "Export",
    "텍스트 파일 (*.txt)": "Text File (*.txt)",
    "JSON 파일 (*.json)": "JSON File (*.json)",
    "CSV 파일 (*.csv)": "CSV File (*.csv)",
    "오디오 싱크 플레이어": "Audio Sync Player",
    "화자": "Speaker",
    "내용": "Content",
    "시간": "Time",
    "재생": "Play",
    "일시정지": "Pause",
    "정지": "Stop",
    "화자 분리 사용 (--diarize)": "Use Speaker Diarization (--diarize)",
    "YouTube 저작권 동의": "YouTube Copyright Disclaimer",
    "동의 및 계속": "Agree and Continue",
    "취소": "Cancel",
}


def set_language(lang: str) -> None:
    """Set current global UI language ('ko' or 'en')."""
    global _current_lang
    if lang in ("ko", "en"):
        _current_lang = lang
    else:
        logger.warning("Unsupported language code '%s', fallback to 'ko'", lang)
        _current_lang = "ko"


def get_language() -> str:
    """Get current global UI language."""
    return _current_lang


def tr(text: str) -> str:
    """Translate Korean source string to the active target language (e.g. English).

    If the current language is 'ko', or translation is missing, returns 'text' itself.
    """
    if _current_lang == "ko":
        return text
    return TRANSLATIONS.get(text, text)
