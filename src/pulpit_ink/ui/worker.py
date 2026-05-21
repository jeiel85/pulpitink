"""QThread worker that wraps :func:`run_transcribe`.

Keeps the long-running pipeline off the Qt event loop so the UI stays
responsive. Progress lines and completion are reported via signals.
"""

from __future__ import annotations

from PySide6.QtCore import QObject, QThread, Signal

from pulpit_ink.services.transcribe_service import (
    TranscribeRequest,
    TranscribeResult,
    run_transcribe,
)


class TranscribeWorker(QObject):
    """Run one :class:`TranscribeRequest` and emit progress/result signals."""

    progress = Signal(str)
    finished_ok = Signal(object)  # TranscribeResult
    failed = Signal(str)

    def __init__(self, request: TranscribeRequest) -> None:
        super().__init__()
        self._request = request

    def run(self) -> None:
        try:
            result: TranscribeResult = run_transcribe(
                self._request,
                progress=lambda msg: self.progress.emit(msg),
                persist=True,
            )
        except Exception as exc:  # noqa: BLE001 — surfaced to UI
            self.failed.emit(str(exc))
            return
        self.finished_ok.emit(result)


def start_worker(request: TranscribeRequest) -> tuple[QThread, TranscribeWorker]:
    """Create a thread + worker pair, connected and ready to ``start()``.

    The caller owns both objects and is responsible for keeping references
    until the thread finishes (Qt deletes them otherwise).
    """

    thread = QThread()
    worker = TranscribeWorker(request)
    worker.moveToThread(thread)
    thread.started.connect(worker.run)
    worker.finished_ok.connect(thread.quit)
    worker.failed.connect(thread.quit)
    return thread, worker
