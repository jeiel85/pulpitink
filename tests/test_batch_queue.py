import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

try:
    from PySide6.QtWidgets import QApplication, QMessageBox
    PYSIDE6_AVAILABLE = True
except ImportError:
    PYSIDE6_AVAILABLE = False

pytestmark = pytest.mark.skipif(not PYSIDE6_AVAILABLE, reason="PySide6 is not installed")

from pulpit_ink.services.transcribe_service import TranscribeResult  # noqa: E402
from pulpit_ink.ui.main_window import MainWindow  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def q_app():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


def test_batch_queue_sequential_flow(q_app):
    with patch("pulpit_ink.ui.main_window.start_worker") as mock_start_worker, \
         patch("pulpit_ink.ui.main_window.connect"), \
         patch("pulpit_ink.ui.main_window.initialise_database"):

        mock_thread = MagicMock()
        mock_worker = MagicMock()
        mock_start_worker.return_value = (mock_thread, mock_worker)

        window = MainWindow()

        file1 = Path("test1.mp3")
        file2 = Path("test2.wav")
        window._add_files([file1, file2])

        assert len(window._files) == 2
        assert window.file_list.count() == 2

        window._on_run()

        assert len(window._queue_files) == 2
        assert window._current_queue_index == 0
        assert mock_start_worker.call_count == 1

        assert "[진행 중]" in window.file_list.item(0).text()
        assert "[대기]" in window.file_list.item(1).text()

        mock_result = MagicMock(spec=TranscribeResult)
        mock_result.job_id = "job_1"
        mock_result.elapsed_seconds = 1.5
        mock_result.transcription = MagicMock()
        mock_result.transcription.segments = []

        window._on_worker_done(mock_result)

        assert "[완료]" in window.file_list.item(0).text()
        assert window._current_queue_index == 1

        window._on_thread_finished()

        assert "[진행 중]" in window.file_list.item(1).text()
        assert window._current_queue_index == 1
        assert mock_start_worker.call_count == 2

        mock_result2 = MagicMock(spec=TranscribeResult)
        mock_result2.job_id = "job_2"
        mock_result2.elapsed_seconds = 2.0
        mock_result2.transcription = MagicMock()
        mock_result2.transcription.segments = []

        window._on_worker_done(mock_result2)

        assert "[완료]" in window.file_list.item(1).text()
        assert window._current_queue_index == 2

        window._on_thread_finished()

        assert window._current_queue_index == -1
        assert window._thread is None
        assert window._worker is None


def test_batch_queue_continuous_on_failure(q_app):
    with patch("pulpit_ink.ui.main_window.start_worker") as mock_start_worker, \
         patch("pulpit_ink.ui.main_window.connect"), \
         patch("pulpit_ink.ui.main_window.initialise_database"), \
         patch("PySide6.QtWidgets.QMessageBox.warning"):

        mock_thread = MagicMock()
        mock_worker = MagicMock()
        mock_start_worker.return_value = (mock_thread, mock_worker)

        window = MainWindow()

        file1 = Path("test1.mp3")
        file2 = Path("test2.wav")
        window._add_files([file1, file2])

        window._on_run()

        window._on_worker_failed("Whisper out of memory")

        assert "[실패]" in window.file_list.item(0).text()
        assert window._current_queue_index == 1

        window._on_thread_finished()

        assert "[진행 중]" in window.file_list.item(1).text()
        assert mock_start_worker.call_count == 2


def test_batch_queue_cancellation(q_app):
    with patch("pulpit_ink.ui.main_window.start_worker") as mock_start_worker, \
         patch("pulpit_ink.ui.main_window.connect"), \
         patch("pulpit_ink.ui.main_window.initialise_database"), \
         patch("PySide6.QtWidgets.QMessageBox.question") as mock_question:

        mock_question.return_value = QMessageBox.StandardButton.Yes

        mock_thread = MagicMock()
        mock_worker = MagicMock()
        mock_start_worker.return_value = (mock_thread, mock_worker)

        window = MainWindow()
        file1 = Path("test1.mp3")
        file2 = Path("test2.wav")
        window._add_files([file1, file2])

        window._on_run()

        window._on_run()

        assert len(window._queue_files) == 0
        assert window._current_queue_index == -1
        mock_thread.terminate.assert_called_once()
        mock_thread.wait.assert_called_once()

        window._on_thread_finished()
        assert "[중단]" in window.file_list.item(0).text()
        assert window._thread is None
        assert window._worker is None
