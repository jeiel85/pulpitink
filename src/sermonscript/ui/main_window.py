"""SermonScript main window (PySide6).

UI-only logic lives here. All heavy work goes through
:mod:`sermonscript.services` so the CLI and GUI share the same pipeline.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QSplitter,
    QStatusBar,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from sermonscript.core.audio.enhancement_presets import PRESETS
from sermonscript.core.export.base import ExportFormat
from sermonscript.services.model_service import list_models
from sermonscript.services.settings_service import SettingsService
from sermonscript.services.transcribe_service import (
    SUPPORTED_INPUT_EXTENSIONS,
    TranscribeRequest,
    TranscribeResult,
)
from sermonscript.storage.database import connect, initialise_database
from sermonscript.storage.job_repository import JobRepository
from sermonscript.ui.transcript_editor import TranscriptEditorWidget
from sermonscript.ui.worker import start_worker

_LANGUAGES = (
    ("ko", "한국어"),
    ("en", "English"),
    ("ja", "日本語"),
    ("zh", "中文"),
    ("auto", "자동 감지"),
)


class MainWindow(QMainWindow):
    """SermonScript GUI entry point."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("SermonScript")
        self.resize(1100, 720)
        self.setAcceptDrops(True)

        self._settings_service = SettingsService()
        self._settings = self._settings_service.load()

        self._files: list[Path] = []
        self._thread = None
        self._worker = None

        self._build_ui()
        self._refresh_recent_jobs()

    # ---------- UI ----------

    def _build_ui(self) -> None:
        central = QWidget(self)
        root = QHBoxLayout(central)

        # Left column: file queue + actions
        left = QVBoxLayout()
        self.file_list = QListWidget()
        self.file_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        left.addWidget(QLabel("변환 대기 파일"))
        left.addWidget(self.file_list, 1)

        file_buttons = QHBoxLayout()
        add_btn = QPushButton("파일 추가…")
        add_btn.clicked.connect(self._on_add_files)
        remove_btn = QPushButton("선택 제거")
        remove_btn.clicked.connect(self._on_remove_selected)
        clear_btn = QPushButton("모두 비우기")
        clear_btn.clicked.connect(self._on_clear_files)
        file_buttons.addWidget(add_btn)
        file_buttons.addWidget(remove_btn)
        file_buttons.addWidget(clear_btn)
        left.addLayout(file_buttons)

        left.addWidget(QLabel("최근 작업 (DB)"))
        self.recent_list = QListWidget()
        self.recent_list.itemSelectionChanged.connect(self._on_recent_selected)
        left.addWidget(self.recent_list, 1)

        # Right column: options + run + tabs
        right = QVBoxLayout()
        right.addWidget(self._build_options_group())

        run_row = QHBoxLayout()
        self.run_btn = QPushButton("변환 시작")
        self.run_btn.clicked.connect(self._on_run)
        run_row.addWidget(self.run_btn)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setVisible(False)
        run_row.addWidget(self.progress_bar, 1)
        right.addLayout(run_row)

        self.tabs = QTabWidget()
        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.preview_view = QPlainTextEdit()
        self.preview_view.setReadOnly(True)
        self.editor = TranscriptEditorWidget()
        self.tabs.addTab(self.log_view, "로그")
        self.tabs.addTab(self.preview_view, "결과 미리보기")
        self.tabs.addTab(self.editor, "편집기")
        right.addWidget(self.tabs, 1)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        left_wrap = QWidget()
        left_wrap.setLayout(left)
        right_wrap = QWidget()
        right_wrap.setLayout(right)
        splitter.addWidget(left_wrap)
        splitter.addWidget(right_wrap)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        root.addWidget(splitter)
        self.setCentralWidget(central)

        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage(
            "파일을 추가하거나 드래그하여 변환을 시작하세요."
        )

    def _build_options_group(self) -> QGroupBox:
        group = QGroupBox("변환 설정")
        form = QFormLayout()

        self.language_combo = QComboBox()
        for code, label in _LANGUAGES:
            self.language_combo.addItem(f"{label} ({code})", userData=code)
        self._select_combo_value(self.language_combo, self._settings.language)
        form.addRow("언어", self.language_combo)

        self.model_combo = QComboBox()
        for model in list_models():
            self.model_combo.addItem(f"{model.name} — {model.size_label}", userData=model.name)
        self._select_combo_value(self.model_combo, self._settings.model)
        form.addRow("모델", self.model_combo)

        self.preset_combo = QComboBox()
        for preset in PRESETS.values():
            self.preset_combo.addItem(f"{preset.name} — {preset.description}", userData=preset.name)
        self._select_combo_value(self.preset_combo, self._settings.preset)
        form.addRow("전처리", self.preset_combo)

        output_row = QHBoxLayout()
        self.output_label = QLabel(str(self._settings.resolved_output_dir()))
        self.output_label.setWordWrap(True)
        choose_btn = QPushButton("폴더 선택…")
        choose_btn.clicked.connect(self._on_choose_output)
        output_row.addWidget(self.output_label, 1)
        output_row.addWidget(choose_btn)
        wrapper = QWidget()
        wrapper.setLayout(output_row)
        form.addRow("출력 폴더", wrapper)

        group.setLayout(form)
        return group

    @staticmethod
    def _select_combo_value(combo: QComboBox, value: str) -> None:
        for i in range(combo.count()):
            if combo.itemData(i) == value:
                combo.setCurrentIndex(i)
                return

    # ---------- file queue ----------

    def _on_add_files(self) -> None:
        filters = " ".join(f"*{ext}" for ext in sorted(SUPPORTED_INPUT_EXTENSIONS))
        paths, _ = QFileDialog.getOpenFileNames(
            self, "오디오/비디오 파일 선택", "", f"미디어 파일 ({filters})"
        )
        if paths:
            self._add_files([Path(p) for p in paths])

    def _add_files(self, paths: list[Path]) -> None:
        added = 0
        for path in paths:
            if path.suffix.lower() not in SUPPORTED_INPUT_EXTENSIONS:
                self._append_log(f"건너뜀(지원하지 않는 확장자): {path.name}")
                continue
            if path in self._files:
                continue
            self._files.append(path)
            item = QListWidgetItem(f"{path.name}  —  {path}")
            item.setData(Qt.ItemDataRole.UserRole, str(path))
            self.file_list.addItem(item)
            added += 1
        if added:
            self.statusBar().showMessage(f"{added}개 파일 추가됨 (총 {len(self._files)}개)")

    def _on_remove_selected(self) -> None:
        for item in self.file_list.selectedItems():
            row = self.file_list.row(item)
            self.file_list.takeItem(row)
            try:
                self._files.pop(row)
            except IndexError:
                pass

    def _on_clear_files(self) -> None:
        self.file_list.clear()
        self._files.clear()

    # ---------- drag-and-drop ----------

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:
        paths = [Path(url.toLocalFile()) for url in event.mimeData().urls() if url.isLocalFile()]
        if paths:
            self._add_files(paths)
            event.acceptProposedAction()

    # ---------- output dir ----------

    def _on_choose_output(self) -> None:
        current = self.output_label.text() or str(self._settings.resolved_output_dir())
        chosen = QFileDialog.getExistingDirectory(self, "출력 폴더 선택", current)
        if chosen:
            self.output_label.setText(chosen)
            try:
                self._settings = self._settings_service.update(output_dir=chosen)
            except KeyError:
                pass

    # ---------- run ----------

    def _on_run(self) -> None:
        if self._thread is not None:
            QMessageBox.information(self, "SermonScript", "이미 변환이 진행 중입니다.")
            return
        if not self._files:
            QMessageBox.information(self, "SermonScript", "변환할 파일을 추가하세요.")
            return

        target = self._files[0]
        language = self.language_combo.currentData()
        model = self.model_combo.currentData()
        preset = self.preset_combo.currentData()
        output_dir = Path(self.output_label.text())

        # Persist the latest choices so the next launch starts from where the user left off.
        try:
            self._settings_service.update(
                language=language,
                model=model,
                preset=preset,
                output_dir=str(output_dir),
            )
        except KeyError:
            pass

        request = TranscribeRequest(
            input_path=target,
            output_dir=output_dir,
            language=None if language == "auto" else language,
            model=model,
            preset=preset,
            formats=(
                ExportFormat.TXT,
                ExportFormat.JSON,
                ExportFormat.MD,
                ExportFormat.SRT,
                ExportFormat.VTT,
            ),
        )

        self.log_view.clear()
        self.preview_view.clear()
        self._set_running(True)
        self._append_log(f"변환 시작: {target.name}")

        thread, worker = start_worker(request)
        worker.progress.connect(self._append_log)
        worker.finished_ok.connect(self._on_worker_done)
        worker.failed.connect(self._on_worker_failed)
        thread.finished.connect(self._on_thread_finished)
        self._thread = thread
        self._worker = worker
        thread.start()

    def _set_running(self, running: bool) -> None:
        self.run_btn.setEnabled(not running)
        self.progress_bar.setVisible(running)
        if running:
            self.statusBar().showMessage("변환 중…")
        else:
            self.statusBar().showMessage("대기 중")

    def _append_log(self, msg: str) -> None:
        self.log_view.appendPlainText(msg)

    def _on_worker_done(self, result: TranscribeResult) -> None:
        self._append_log(f"완료: {result.job_id} ({result.elapsed_seconds:.2f}s)")
        if result.transcription is not None:
            preview = "\n".join(seg.text for seg in result.transcription.segments[:200])
            self.preview_view.setPlainText(preview)
            self.tabs.setCurrentWidget(self.preview_view)
        if self._files:
            done_path = self._files.pop(0)
            if self.file_list.count():
                self.file_list.takeItem(0)
            self._append_log(f"큐에서 제거: {done_path.name}")
        try:
            self.editor.load_job(result.job_id)
        except Exception as exc:  # noqa: BLE001
            self._append_log(f"편집기 로드 실패: {exc}")
        self._refresh_recent_jobs()

    def _on_worker_failed(self, message: str) -> None:
        self._append_log(f"오류: {message}")
        QMessageBox.warning(self, "SermonScript", f"변환 실패:\n{message}")
        self._refresh_recent_jobs()

    def _on_thread_finished(self) -> None:
        if self._thread is not None:
            self._thread.deleteLater()
        if self._worker is not None:
            self._worker.deleteLater()
        self._thread = None
        self._worker = None
        self._set_running(False)

    # ---------- recent jobs ----------

    def _refresh_recent_jobs(self) -> None:
        self.recent_list.clear()
        try:
            initialise_database()
            with connect() as conn:
                jobs = JobRepository(conn).list_jobs(limit=30)
        except Exception as exc:  # noqa: BLE001
            self._append_log(f"최근 작업 로드 실패: {exc}")
            return

        for job in jobs:
            status_tag = {
                "completed": "[완료]",
                "running": "[진행]",
                "failed": "[실패]",
            }.get(job.status, f"[{job.status}]")
            item = QListWidgetItem(f"{status_tag} {job.title}  ({job.id})")
            item.setData(Qt.ItemDataRole.UserRole, job.id)
            self.recent_list.addItem(item)

    def _on_recent_selected(self) -> None:
        items = self.recent_list.selectedItems()
        if not items:
            return
        job_id = items[0].data(Qt.ItemDataRole.UserRole)
        try:
            with connect() as conn:
                repo = JobRepository(conn)
                segs = repo.list_segments(job_id)
        except Exception as exc:  # noqa: BLE001
            self._append_log(f"세그먼트 로드 실패: {exc}")
            return
        text = (
            "\n".join(s.edited_text or s.clean_text or s.raw_text for s in segs[:200])
            if segs
            else "(저장된 세그먼트가 없습니다.)"
        )
        self.preview_view.setPlainText(text)
        try:
            self.editor.load_job(job_id)
        except Exception as exc:  # noqa: BLE001
            self._append_log(f"편집기 로드 실패: {exc}")
