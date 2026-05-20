"""PulpitInk main window (PySide6).

UI-only logic lives here. All heavy work goes through
:mod:`pulpitink.services` so the CLI and GUI share the same pipeline.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
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

from pulpitink.core.audio.enhancement_presets import PRESETS
from pulpitink.core.export.base import ExportFormat
from pulpitink.core.utils.i18n import tr
from pulpitink.services.model_service import list_models
from pulpitink.services.settings_service import SettingsService
from pulpitink.services.transcribe_service import (
    SUPPORTED_INPUT_EXTENSIONS,
    TranscribeRequest,
    TranscribeResult,
)
from pulpitink.storage.database import connect, initialise_database
from pulpitink.storage.job_repository import JobRepository
from pulpitink.ui.transcript_editor import TranscriptEditorWidget
from pulpitink.ui.worker import start_worker

_LANGUAGES = (
    ("ko", "한국어"),
    ("en", "English"),
    ("ja", "日本語"),
    ("zh", "中文"),
    ("auto", "자동 감지"),
)


class MainWindow(QMainWindow):
    """PulpitInk GUI entry point."""

    def __init__(self) -> None:
        super().__init__()
        self.resize(1100, 720)
        self.setAcceptDrops(True)

        self._settings_service = SettingsService()
        self._settings = self._settings_service.load()

        self._files: list[Path] = []
        self._queue_files: list[Path] = []
        self._current_queue_index: int = -1
        self._thread = None
        self._worker = None

        self._build_ui()
        self._retranslate_ui()
        self._refresh_recent_jobs()

    # ---------- UI ----------

    def _build_ui(self) -> None:
        central = QWidget(self)
        root = QHBoxLayout(central)

        # Left column: file queue + actions
        left = QVBoxLayout()
        self.file_list = QListWidget()
        self.file_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.file_title_label = QLabel("")
        left.addWidget(self.file_title_label)
        left.addWidget(self.file_list, 1)

        file_buttons = QHBoxLayout()
        self.add_btn = QPushButton("")
        self.add_btn.clicked.connect(self._on_add_files)
        self.remove_btn = QPushButton("")
        self.remove_btn.clicked.connect(self._on_remove_selected)
        self.clear_btn = QPushButton("")
        self.clear_btn.clicked.connect(self._on_clear_files)
        file_buttons.addWidget(self.add_btn)
        file_buttons.addWidget(self.remove_btn)
        file_buttons.addWidget(self.clear_btn)
        left.addLayout(file_buttons)

        self.recent_db_label = QLabel("")
        self.recent_list = QListWidget()
        self.recent_list.itemSelectionChanged.connect(self._on_recent_selected)
        self.recent_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.recent_list.customContextMenuRequested.connect(self._show_recent_context_menu)
        left.addWidget(self.recent_db_label)
        left.addWidget(self.recent_list, 1)

        # Right column: options + run + tabs
        right = QVBoxLayout()
        right.addWidget(self._build_options_group())

        run_row = QHBoxLayout()
        self.run_btn = QPushButton("")
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
        self.tabs.addTab(self.log_view, "")
        self.tabs.addTab(self.preview_view, "")
        self.tabs.addTab(self.editor, "")
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

    def _build_options_group(self) -> QGroupBox:
        self.options_group = QGroupBox("")
        form = QFormLayout()

        self.app_lang_label = QLabel("")
        self.app_language_combo = QComboBox()
        self.app_language_combo.addItem("한국어 (ko)", userData="ko")
        self.app_language_combo.addItem("English (en)", userData="en")
        self._select_combo_value(self.app_language_combo, self._settings.app_language)
        self.app_language_combo.currentIndexChanged.connect(self._on_app_language_changed)
        form.addRow(self.app_lang_label, self.app_language_combo)

        self.lang_label = QLabel("")
        self.language_combo = QComboBox()
        for code, label in _LANGUAGES:
            self.language_combo.addItem(f"{label} ({code})", userData=code)
        self._select_combo_value(self.language_combo, self._settings.language)
        form.addRow(self.lang_label, self.language_combo)

        self.model_label = QLabel("")
        self.model_combo = QComboBox()
        for model in list_models():
            self.model_combo.addItem(f"{model.name} — {model.size_label}", userData=model.name)
        self._select_combo_value(self.model_combo, self._settings.model)
        form.addRow(self.model_label, self.model_combo)

        self.preset_label = QLabel("")
        self.preset_combo = QComboBox()
        for preset in PRESETS.values():
            self.preset_combo.addItem(f"{preset.name} — {preset.description}", userData=preset.name)
        self._select_combo_value(self.preset_combo, self._settings.preset)
        form.addRow(self.preset_label, self.preset_combo)

        output_row = QHBoxLayout()
        self.output_label = QLabel(str(self._settings.resolved_output_dir()))
        self.output_label.setWordWrap(True)
        self.choose_btn = QPushButton("")
        self.choose_btn.clicked.connect(self._on_choose_output)
        output_row.addWidget(self.output_label, 1)
        output_row.addWidget(self.choose_btn)
        wrapper = QWidget()
        wrapper.setLayout(output_row)
        self.output_dir_label_title = QLabel("")
        form.addRow(self.output_dir_label_title, wrapper)

        self.fuzzy_checkbox = QCheckBox("")
        self.fuzzy_checkbox.setChecked(self._settings.fuzzy_matching_enabled)
        self.fuzzy_label_title = QLabel("")
        form.addRow(self.fuzzy_label_title, self.fuzzy_checkbox)

        self.fuzzy_spin = QDoubleSpinBox()
        self.fuzzy_spin.setRange(0.60, 0.90)
        self.fuzzy_spin.setSingleStep(0.05)
        self.fuzzy_spin.setValue(self._settings.fuzzy_threshold)
        self.fuzzy_spin.setEnabled(self._settings.fuzzy_matching_enabled)
        self.fuzzy_checkbox.toggled.connect(self.fuzzy_spin.setEnabled)
        self.fuzzy_spin_label_title = QLabel("")
        form.addRow(self.fuzzy_spin_label_title, self.fuzzy_spin)

        self.history_checkbox = QCheckBox("")
        self.history_checkbox.setChecked(self._settings.keep_history)
        self.history_checkbox.toggled.connect(self._on_history_toggled)
        self.history_label_title = QLabel("")
        form.addRow(self.history_label_title, self.history_checkbox)

        self.options_group.setLayout(form)
        return self.options_group

    def _retranslate_ui(self) -> None:
        self.setWindowTitle(tr("설교필기") + " (PulpitInk)")
        self.statusBar().showMessage(tr("파일을 추가하거나 드래그하여 변환을 시작하세요."))

        self.file_title_label.setText(tr("변환 대기 파일"))
        self.add_btn.setText(tr("파일 추가…"))
        self.remove_btn.setText(tr("선택 제거"))
        self.clear_btn.setText(tr("모두 비우기"))
        self.recent_db_label.setText(tr("최근 작업"))
        self.run_btn.setText(tr("변환 시작"))

        self.options_group.setTitle(tr("변환 설정"))
        self.app_lang_label.setText(tr("인터페이스 언어"))
        self.lang_label.setText(tr("인식 언어"))
        self.model_label.setText(tr("음성인식 모델"))
        self.preset_label.setText(tr("전처리 프리셋"))
        self.output_dir_label_title.setText(tr("출력 폴더"))
        self.fuzzy_label_title.setText(tr("성경 구절 교정 (Fuzzy)"))
        self.fuzzy_spin_label_title.setText(tr("임계값"))
        self.history_label_title.setText(tr("최근 작업 기록 저장"))

        self.fuzzy_checkbox.setText(tr("성경 구절 교정 (Fuzzy)") + " " + tr("활성화"))
        self.history_checkbox.setText(tr("최근 작업 기록 저장"))
        self.choose_btn.setText(tr("폴더 선택…"))

        self.tabs.setTabText(0, tr("로그"))
        self.tabs.setTabText(1, tr("결과 미리보기"))
        self.tabs.setTabText(2, tr("편집기"))

    def _on_app_language_changed(self) -> None:
        lang = self.app_language_combo.currentData()
        try:
            self._settings = self._settings_service.update(app_language=lang)
            self._retranslate_ui()
        except Exception as e:
            pass

    @staticmethod
    def _select_combo_value(combo: QComboBox, value: str) -> None:
        for i in range(combo.count()):
            if combo.itemData(i) == value:
                combo.setCurrentIndex(i)
                return

    # ---------- file queue ----------

    def _on_add_files(self) -> None:
        if self._thread is not None:
            QMessageBox.information(self, "설교필기", "변환 진행 중에는 새 파일을 추가할 수 없습니다.")
            return
        filters = " ".join(f"*{ext}" for ext in sorted(SUPPORTED_INPUT_EXTENSIONS))
        paths, _ = QFileDialog.getOpenFileNames(
            self, "오디오/비디오 파일 선택", "", f"미디어 파일 ({filters})"
        )
        if paths:
            self._add_files([Path(p) for p in paths])

    def _add_files(self, paths: list[Path]) -> None:
        if self._thread is not None:
            QMessageBox.information(self, "설교필기", "변환 진행 중에는 새 파일을 추가할 수 없습니다.")
            return

        added = 0
        for path in paths:
            if path.suffix.lower() not in SUPPORTED_INPUT_EXTENSIONS:
                self._append_log(f"건너뜀(지원하지 않는 확장자): {path.name}")
                continue
            if path in self._files:
                continue
            self._files.append(path)
            item = QListWidgetItem(f"[대기] {path.name}  —  {path}")
            item.setData(Qt.ItemDataRole.UserRole, str(path))
            self.file_list.addItem(item)
            added += 1
        if added:
            self.statusBar().showMessage(f"{added}개 파일 추가됨 (총 {len(self._files)}개)")

    def _on_remove_selected(self) -> None:
        if self._thread is not None:
            QMessageBox.information(self, "설교필기", "변환 진행 중에는 파일 큐를 수정할 수 없습니다.")
            return

        for item in self.file_list.selectedItems():
            row = self.file_list.row(item)
            self.file_list.takeItem(row)
            try:
                self._files.pop(row)
            except IndexError:
                pass

    def _on_clear_files(self) -> None:
        if self._thread is not None:
            QMessageBox.information(self, "설교필기", "변환 진행 중에는 파일 큐를 비울 수 없습니다.")
            return

        self.file_list.clear()
        self._files.clear()

    def _update_file_status_text(self, index: int, status: str) -> None:
        if 0 <= index < self.file_list.count():
            item = self.file_list.item(index)
            path_str = item.data(Qt.ItemDataRole.UserRole)
            path = Path(path_str)
            item.setText(f"[{status}] {path.name}  —  {path}")

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
            confirm = QMessageBox.question(
                self,
                "변환 중단",
                "현재 진행 중인 변환 작업과 남은 대기 파일들의 처리를 모두 중단하시겠습니까?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if confirm == QMessageBox.StandardButton.Yes:
                self._append_log("사용자 요청에 의해 배치 변환이 중단되었습니다.")
                self._queue_files = []
                if 0 <= self._current_queue_index < self.file_list.count():
                    self._update_file_status_text(self._current_queue_index, "중단")
                self._current_queue_index = -1

                if self._thread is not None:
                    self._thread.terminate()
                    self._thread.wait()
            return

        if not self._files:
            QMessageBox.information(self, "설교필기", "변환할 파일을 추가하세요.")
            return

        self._queue_files = list(self._files)
        self._current_queue_index = 0

        for idx in range(len(self._queue_files)):
            self._update_file_status_text(idx, "대기")

        self.log_view.clear()
        self.preview_view.clear()
        self._start_next_queue_item()

    def _start_next_queue_item(self) -> None:
        if self._current_queue_index < 0 or self._current_queue_index >= len(self._queue_files):
            self._append_log("\n=== 모든 배치 변환 작업 완료 ===")
            self._queue_files = []
            self._current_queue_index = -1
            self._set_running(False)
            return

        target = self._queue_files[self._current_queue_index]
        self._update_file_status_text(self._current_queue_index, "진행 중")
        self._set_running(True)
        self._append_log(f"\n[큐 {self._current_queue_index + 1}/{len(self._queue_files)}] 변환 시작: {target.name}")

        language = self.language_combo.currentData()
        model = self.model_combo.currentData()
        preset = self.preset_combo.currentData()
        output_dir = Path(self.output_label.text())
        fuzzy_enabled = self.fuzzy_checkbox.isChecked()
        fuzzy_threshold = self.fuzzy_spin.value()

        try:
            self._settings_service.update(
                language=language,
                model=model,
                preset=preset,
                output_dir=str(output_dir),
                fuzzy_matching_enabled=fuzzy_enabled,
                fuzzy_threshold=fuzzy_threshold,
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
                ExportFormat.CSV,
            ),
            fuzzy_matching_enabled=fuzzy_enabled,
            fuzzy_threshold=fuzzy_threshold,
        )

        thread, worker = start_worker(request)
        worker.progress.connect(self._append_log)
        worker.finished_ok.connect(self._on_worker_done)
        worker.failed.connect(self._on_worker_failed)
        thread.finished.connect(self._on_thread_finished)
        self._thread = thread
        self._worker = worker
        thread.start()

    def _set_running(self, running: bool) -> None:
        if running:
            self.run_btn.setText("변환 중단")
            self.run_btn.setStyleSheet("background-color: #fce4ec; color: #c2185b; font-weight: bold;")
            self.progress_bar.setVisible(True)
            self.statusBar().showMessage("변환 중…")
        else:
            self.run_btn.setText("변환 시작")
            self.run_btn.setStyleSheet("")
            self.run_btn.setEnabled(True)
            self.progress_bar.setVisible(False)
            self.statusBar().showMessage("대기 중")

    def _append_log(self, msg: str) -> None:
        self.log_view.appendPlainText(msg)

    def _on_worker_done(self, result: TranscribeResult) -> None:
        self._append_log(f"완료: {result.job_id} ({result.elapsed_seconds:.2f}s)")

        if 0 <= self._current_queue_index < len(self._queue_files):
            self._update_file_status_text(self._current_queue_index, "완료")

        if result.transcription is not None:
            preview = "\n".join(seg.text for seg in result.transcription.segments[:200])
            self.preview_view.setPlainText(preview)
            self.tabs.setCurrentWidget(self.preview_view)

        try:
            self.editor.load_job(result.job_id)
        except Exception as exc:  # noqa: BLE001
            self._append_log(f"편집기 로드 실패: {exc}")

        self._refresh_recent_jobs()

        if self._current_queue_index != -1:
            self._current_queue_index += 1

    def _on_worker_failed(self, message: str) -> None:
        self._append_log(f"오류: {message}")

        if 0 <= self._current_queue_index < len(self._queue_files):
            self._update_file_status_text(self._current_queue_index, "실패")

        QMessageBox.warning(self, "설교필기", f"변환 실패:\n{message}")
        self._refresh_recent_jobs()

        if self._current_queue_index != -1:
            self._current_queue_index += 1

    def _on_thread_finished(self) -> None:
        if self._thread is not None:
            self._thread.deleteLater()
        if self._worker is not None:
            self._worker.deleteLater()
        self._thread = None
        self._worker = None

        if self._current_queue_index != -1 and self._current_queue_index < len(self._queue_files):
            self._start_next_queue_item()
        else:
            if self._current_queue_index == -1:
                self._append_log("\n=== 배치 변환 중단됨 ===")
            else:
                self._append_log("\n=== 모든 배치 변환 작업 완료 ===")
            self._queue_files = []
            self._current_queue_index = -1
            self._set_running(False)

    # ---------- recent jobs ----------

    def _refresh_recent_jobs(self) -> None:
        self.recent_list.clear()
        if not self._settings.keep_history:
            item = QListWidgetItem("(최근 작업 기록 기능이 비활성화되었습니다)")
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEnabled)
            self.recent_list.addItem(item)
            return

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

    def _on_history_toggled(self, checked: bool) -> None:
        try:
            self._settings = self._settings_service.update(keep_history=checked)
            self._refresh_recent_jobs()
            self._append_log(f"설정 변경: keep_history={checked}")
        except Exception as exc:  # noqa: BLE001
            self._append_log(f"설정 저장 실패: {exc}")

    def _show_recent_context_menu(self, pos: QPoint) -> None:
        if not self._settings.keep_history:
            return

        item = self.recent_list.itemAt(pos)
        if item is None:
            return

        job_id = item.data(Qt.ItemDataRole.UserRole)
        if not job_id:
            return

        menu = QMenu(self)
        delete_action = menu.addAction("작업 및 캐시 삭제")
        action = menu.exec(self.recent_list.mapToGlobal(pos))
        if action == delete_action:
            confirm = QMessageBox.question(
                self,
                "작업 삭제",
                f"정말로 이 작업({job_id})의 모든 DB 레코드와 전처리된 캐시 오디오 파일을 완전히 삭제하시겠습니까?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if confirm == QMessageBox.StandardButton.Yes:
                try:
                    initialise_database()
                    with connect() as conn:
                        repo = JobRepository(conn)
                        repo.delete_job(job_id)

                    import shutil
                    job_cache_dir = (Path("cache") / "jobs" / job_id).resolve()
                    if job_cache_dir.exists() and job_cache_dir.is_dir():
                        shutil.rmtree(job_cache_dir)

                    self._append_log(f"작업 및 캐시 삭제 완료: {job_id}")
                    self._refresh_recent_jobs()
                except Exception as exc:  # noqa: BLE001
                    QMessageBox.warning(self, "오류", f"작업 삭제 중 오류가 발생했습니다:\n{exc}")
