from __future__ import annotations

import sys

import pytest
from PySide6.QtWidgets import QApplication

from pulpit_ink.ui.transcript_editor import (
    TranscriptEditorWidget,
    _markdown_to_html,
)


# Qt Application 인스턴스 확보
@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


def test_markdown_to_html_helper():
    # 1. Bold 파싱 검사
    assert "<b>강조</b>" in _markdown_to_html("**강조**")
    assert "<b>텍스트</b>" in _markdown_to_html("__텍스트__")

    # 2. Italic 파싱 검사
    assert "<i>기울임</i>" in _markdown_to_html("*기울임*")
    assert "<i>기울임2</i>" in _markdown_to_html("_기울임2_")

    # 3. Strikethrough 파싱 검사
    assert "<del>취소</del>" in _markdown_to_html("~~취소~~")

    # 4. Inline Code 파싱 검사
    assert "font-family: monospace;" in _markdown_to_html("`code`")
    assert "code" in _markdown_to_html("`code`")

    # 5. HTML Escape 검사
    assert "&lt;script&gt;" in _markdown_to_html("<script>")
    assert "hello&amp;world" in _markdown_to_html("hello&world")

    # 6. 개행 변환 검사
    assert "첫째줄<br>둘째줄" in _markdown_to_html("첫째줄\n둘째줄")


def test_editor_shortcuts_creation(qapp):
    widget = TranscriptEditorWidget()

    # 단축키 설정 호출 검증
    assert hasattr(widget, "_shortcut_play")
    assert hasattr(widget, "_shortcut_prev")
    assert hasattr(widget, "_shortcut_next")
    assert hasattr(widget, "_shortcut_play_seg")
    assert hasattr(widget, "_shortcut_speed_up")
    assert hasattr(widget, "_shortcut_speed_down")

    # 단축키 바인딩 인스턴스 타입 검사
    from PySide6.QtGui import QShortcut
    assert isinstance(widget._shortcut_play, QShortcut)
    assert isinstance(widget._shortcut_speed_up, QShortcut)


def test_editor_playback_rate_boundaries(qapp):
    widget = TranscriptEditorWidget()

    # 1. 초기 재생 속도
    assert widget._playback_rate == 1.0

    # 2. 속도 증가 한계값 테스트 (최대 2.0)
    widget._on_shortcut_speed_up()  # 1.1
    assert widget._playback_rate == 1.1

    # 2.0 까지 강제 속도 인상 시도
    for _ in range(20):
        widget._on_shortcut_speed_up()
    assert widget._playback_rate == 2.0
    assert widget.speed_label.text() == "속도: 2.0x"

    # 3. 속도 감소 한계값 테스트 (최소 0.5)
    for _ in range(25):
        widget._on_shortcut_speed_down()
    assert widget._playback_rate == 0.5
    assert widget.speed_label.text() == "속도: 0.5x"
