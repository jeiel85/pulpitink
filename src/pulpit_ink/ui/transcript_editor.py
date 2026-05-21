"""Per-job transcript editor (PySide6).

A widget the main window embeds (in a separate tab) to inspect and
correct a job's segments. The editor is intentionally a thin wrapper
around :class:`JobRepository` — every interaction persists immediately.

Capabilities (Goal 3):

* Table view with start / end / 확인 / 텍스트 columns.
* In-place text editing that writes ``edited_text`` (never ``raw_text``).
* Toggle for ``needs_review`` (and automatic highlight when STT
  confidence indicates the segment is risky).
* Search and replace across all segments — replacements feed
  ``edited_text``.
* Side panel with pending correction suggestions and Apply / Ignore
  buttons.
* Export priority preserved: edited_text > clean_text > raw_text.
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtGui import QBrush, QColor
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSlider,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from pulpit_ink.core.export.base import ExportFormat
from pulpit_ink.core.export.pipeline import ExportPipeline
from pulpit_ink.core.reference.corrections import apply_correction_to_segment
from pulpit_ink.core.transcription.base import (
    TranscriptionResult,
    TranscriptSegment,
)
from pulpit_ink.storage.database import connect, initialise_database
from pulpit_ink.storage.job_repository import (
    CorrectionSuggestionRecord,
    JobRepository,
    SegmentRecord,
)

REVIEW_HIGHLIGHT = QColor(255, 244, 200)
EDITED_HIGHLIGHT = QColor(220, 248, 220)


def _format_time(value: float) -> str:
    minutes, seconds = divmod(max(0.0, value), 60)
    return f"{int(minutes):02d}:{seconds:05.2f}"


class TranscriptEditorWidget(QWidget):
    """Edit a single job's segments + manage its correction suggestions."""

    segment_updated = Signal(int)
    suggestion_changed = Signal(int, str)

    def __init__(
        self,
        *,
        db_path: Path | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._db_path = db_path
        self._job_id: str | None = None
        self._segments: list[SegmentRecord] = []
        self._suggestions: list[CorrectionSuggestionRecord] = []
        self._suppress_table_change = False
        self._suppress_slider_change = False

        self._player = QMediaPlayer()
        self._audio_output = QAudioOutput()
        self._player.setAudioOutput(self._audio_output)

        self._build_ui()

    # ---------- UI ----------

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        search_row = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("검색어 (Enter)")
        self.search_edit.returnPressed.connect(self._on_search)
        self.replace_edit = QLineEdit()
        self.replace_edit.setPlaceholderText("치환할 텍스트")
        self.case_sensitive = QCheckBox("대/소문자 구분")
        self.review_only = QCheckBox("확인 필요만")
        self.review_only.stateChanged.connect(self._refresh_segment_view)
        find_btn = QPushButton("찾기")
        find_btn.clicked.connect(self._on_search)
        replace_btn = QPushButton("모두 치환")
        replace_btn.clicked.connect(self._on_replace_all)
        export_btn = QPushButton("Export…")
        export_btn.clicked.connect(self._on_export)
        search_row.addWidget(QLabel("검색"))
        search_row.addWidget(self.search_edit, 2)
        search_row.addWidget(QLabel("치환"))
        search_row.addWidget(self.replace_edit, 2)
        search_row.addWidget(self.case_sensitive)
        search_row.addWidget(self.review_only)
        search_row.addWidget(find_btn)
        search_row.addWidget(replace_btn)
        search_row.addWidget(export_btn)
        layout.addLayout(search_row)

        splitter = QSplitter(Qt.Orientation.Horizontal, self)
        layout.addWidget(splitter, 1)

        self.segment_table = QTableWidget(0, 6)
        self.segment_table.setHorizontalHeaderLabels(
            ["시작", "종료", "확인", "화자", "텍스트", "원문(raw)"]
        )
        self.segment_table.horizontalHeader().setSectionResizeMode(
            4, QHeaderView.ResizeMode.Stretch
        )
        self.segment_table.horizontalHeader().setSectionResizeMode(
            5, QHeaderView.ResizeMode.Stretch
        )
        self.segment_table.verticalHeader().setVisible(False)
        self.segment_table.setEditTriggers(
            QAbstractItemView.EditTrigger.DoubleClicked
            | QAbstractItemView.EditTrigger.SelectedClicked
            | QAbstractItemView.EditTrigger.EditKeyPressed
        )
        self.segment_table.itemChanged.connect(self._on_table_item_changed)
        splitter.addWidget(self.segment_table)

        side = QWidget()
        side_layout = QVBoxLayout(side)
        side_layout.setContentsMargins(0, 0, 0, 0)
        side_layout.addWidget(QLabel("교정 후보 (pending)"))
        self.suggestion_list = QListWidget()
        self.suggestion_list.itemSelectionChanged.connect(self._on_suggestion_selected)
        side_layout.addWidget(self.suggestion_list, 1)
        btn_row = QHBoxLayout()
        self.apply_btn = QPushButton("적용")
        self.apply_btn.clicked.connect(self._on_apply_suggestion)
        self.ignore_btn = QPushButton("무시")
        self.ignore_btn.clicked.connect(self._on_ignore_suggestion)
        btn_row.addWidget(self.apply_btn)
        btn_row.addWidget(self.ignore_btn)
        side_layout.addLayout(btn_row)
        self.show_all_status = QCheckBox("이미 처리한 후보도 표시")
        self.show_all_status.stateChanged.connect(self._refresh_suggestion_view)
        side_layout.addWidget(self.show_all_status)
        splitter.addWidget(side)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)

        self.status_label = QLabel("작업이 선택되지 않았습니다.")
        layout.addWidget(self.status_label)

        # 오디오 싱크 플레이어 UI 바 구성
        player_row = QHBoxLayout()
        self.play_btn = QPushButton("재생")
        self.play_btn.clicked.connect(self._on_play_clicked)
        self.play_btn.setEnabled(False)

        self.position_slider = QSlider(Qt.Orientation.Horizontal)
        self.position_slider.setRange(0, 0)
        self.position_slider.sliderMoved.connect(self._on_slider_moved)
        self.position_slider.setEnabled(False)

        self.time_label = QLabel("00:00.00 / 00:00.00")

        self.play_segment_btn = QPushButton("선택 구간 재생")
        self.play_segment_btn.clicked.connect(self._on_play_segment_clicked)
        self.play_segment_btn.setEnabled(False)

        self.sync_scroll_check = QCheckBox("재생 싱크 스크롤 활성화")
        self.sync_scroll_check.setChecked(True)

        player_row.addWidget(self.play_btn)
        player_row.addWidget(self.position_slider, 1)
        player_row.addWidget(self.time_label)
        player_row.addWidget(self.play_segment_btn)
        player_row.addWidget(self.sync_scroll_check)

        layout.addLayout(player_row)

        # 플레이어 시그널 연동
        self._player.positionChanged.connect(self._on_player_position_changed)
        self._player.durationChanged.connect(self._on_player_duration_changed)
        self.segment_table.cellDoubleClicked.connect(self._on_table_double_clicked)

    # ---------- DB helpers ----------

    def _open_repo(self) -> tuple[object, JobRepository]:
        initialise_database(self._db_path)
        conn = connect(self._db_path)
        return conn, JobRepository(conn)

    # ---------- public API ----------

    def load_job(self, job_id: str) -> None:
        """Load segments + suggestions for ``job_id`` and refresh the view."""

        self._job_id = job_id
        conn, repo = self._open_repo()
        try:
            self._segments = repo.list_segments(job_id)
            self._suggestions = repo.list_correction_suggestions(job_id)
        finally:
            conn.close()
        self._refresh_segment_view()
        self._refresh_suggestion_view()
        self.status_label.setText(
            f"job={job_id} · 세그먼트 {len(self._segments)}개 · "
            f"교정 후보 {sum(1 for s in self._suggestions if s.status == 'pending')}개 pending"
        )

        # 오디오 소스 자동 매핑
        processed_path = Path("cache") / "jobs" / job_id / "processed.wav"
        audio_source = None
        if processed_path.exists():
            audio_source = str(processed_path.resolve())
        else:
            conn, repo = self._open_repo()
            try:
                job_rec = repo.get_job(job_id)
                if job_rec and job_rec.source_path:
                    audio_source = job_rec.source_path
            finally:
                conn.close()

        if audio_source:
            self._player.setSource(QUrl.fromLocalFile(audio_source))
            self.play_btn.setEnabled(True)
            self.position_slider.setEnabled(True)
            self.play_segment_btn.setEnabled(True)
        else:
            self._player.setSource(QUrl())
            self.play_btn.setEnabled(False)
            self.position_slider.setEnabled(False)
            self.play_segment_btn.setEnabled(False)

        self.play_btn.setText("재생")
        self.position_slider.setRange(0, 0)
        self.time_label.setText("00:00.00 / 00:00.00")

    def clear(self) -> None:
        self._player.stop()
        self._player.setSource(QUrl())
        self.play_btn.setText("재생")
        self.play_btn.setEnabled(False)
        self.position_slider.setRange(0, 0)
        self.position_slider.setEnabled(False)
        self.time_label.setText("00:00.00 / 00:00.00")
        self.play_segment_btn.setEnabled(False)

        self._job_id = None
        self._segments = []
        self._suggestions = []
        self._refresh_segment_view()
        self._refresh_suggestion_view()
        self.status_label.setText("작업이 선택되지 않았습니다.")

    # ---------- 오디오 싱크 플레이어 제어 ----------

    def _on_play_clicked(self) -> None:
        if self._player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self._player.pause()
            self.play_btn.setText("재생")
        else:
            self._player.play()
            self.play_btn.setText("일시정지")

    def _on_player_position_changed(self, position: int) -> None:
        if self._suppress_slider_change:
            return
        self._suppress_slider_change = True
        try:
            self.position_slider.setValue(position)
        finally:
            self._suppress_slider_change = False

        self._update_time_label(position, self._player.duration())

        # 테이블 싱크 및 자동 스크롤
        if not self._segments:
            return

        curr_sec = position / 1000.0
        visible = [
            seg
            for seg in self._segments
            if not self.review_only.isChecked() or seg.needs_review
        ]

        target_row = -1
        for idx, seg in enumerate(visible):
            if seg.start_sec <= curr_sec <= seg.end_sec:
                target_row = idx
                break

        if target_row != -1:
            self._suppress_table_change = True
            try:
                self.segment_table.selectRow(target_row)
                if self.sync_scroll_check.isChecked():
                    item = self.segment_table.item(target_row, 4)
                    if item:
                        self.segment_table.scrollToItem(item, QAbstractItemView.ScrollHint.PositionAtCenter)
            finally:
                self._suppress_table_change = False

    def _on_player_duration_changed(self, duration: int) -> None:
        self.position_slider.setRange(0, duration)
        self._update_time_label(self._player.position(), duration)

    def _on_slider_moved(self, position: int) -> None:
        self._player.setPosition(position)

    def _update_time_label(self, position: int, duration: int) -> None:
        pos_sec = position / 1000.0
        dur_sec = duration / 1000.0
        self.time_label.setText(f"{_format_time(pos_sec)} / {_format_time(dur_sec)}")

    def _on_table_double_clicked(self, row: int, column: int) -> None:
        visible = [
            seg
            for seg in self._segments
            if not self.review_only.isChecked() or seg.needs_review
        ]
        if 0 <= row < len(visible):
            seg = visible[row]
            self._player.setPosition(int(seg.start_sec * 1000))
            self._player.play()
            self.play_btn.setText("일시정지")

    def _on_play_segment_clicked(self) -> None:
        row = self.segment_table.currentRow()
        visible = [
            seg
            for seg in self._segments
            if not self.review_only.isChecked() or seg.needs_review
        ]
        if 0 <= row < len(visible):
            seg = visible[row]
            self._player.setPosition(int(seg.start_sec * 1000))
            self._player.play()
            self.play_btn.setText("일시정지")

    # ---------- segment view ----------

    def _refresh_segment_view(self) -> None:
        self._suppress_table_change = True
        try:
            visible = [
                seg
                for seg in self._segments
                if not self.review_only.isChecked() or seg.needs_review
            ]
            self.segment_table.setRowCount(len(visible))
            for row, seg in enumerate(visible):
                start_item = QTableWidgetItem(_format_time(seg.start_sec))
                start_item.setFlags(start_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                end_item = QTableWidgetItem(_format_time(seg.end_sec))
                end_item.setFlags(end_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                review_item = QTableWidgetItem()
                review_item.setCheckState(
                    Qt.CheckState.Checked if seg.needs_review else Qt.CheckState.Unchecked
                )
                review_item.setText("확인" if seg.needs_review else "")
                review_item.setFlags(
                    Qt.ItemFlag.ItemIsEnabled
                    | Qt.ItemFlag.ItemIsUserCheckable
                    | Qt.ItemFlag.ItemIsSelectable
                )
                review_item.setData(Qt.ItemDataRole.UserRole, seg.id)

                speaker_item = QTableWidgetItem(seg.speaker or "")
                speaker_item.setData(Qt.ItemDataRole.UserRole, seg.id)

                display = seg.edited_text or seg.clean_text or seg.raw_text
                text_item = QTableWidgetItem(display)
                text_item.setData(Qt.ItemDataRole.UserRole, seg.id)
                raw_item = QTableWidgetItem(seg.raw_text)
                raw_item.setFlags(raw_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                if seg.needs_review:
                    bg = QBrush(REVIEW_HIGHLIGHT)
                    for it in (start_item, end_item, review_item, speaker_item, text_item, raw_item):
                        it.setBackground(bg)
                if seg.edited_text:
                    text_item.setBackground(QBrush(EDITED_HIGHLIGHT))
                self.segment_table.setItem(row, 0, start_item)
                self.segment_table.setItem(row, 1, end_item)
                self.segment_table.setItem(row, 2, review_item)
                self.segment_table.setItem(row, 3, speaker_item)
                self.segment_table.setItem(row, 4, text_item)
                self.segment_table.setItem(row, 5, raw_item)
            self.segment_table.resizeColumnsToContents()
            self.segment_table.horizontalHeader().setSectionResizeMode(
                4, QHeaderView.ResizeMode.Stretch
            )
            self.segment_table.horizontalHeader().setSectionResizeMode(
                5, QHeaderView.ResizeMode.Stretch
            )
        finally:
            self._suppress_table_change = False

    def _on_table_item_changed(self, item: QTableWidgetItem) -> None:
        if self._suppress_table_change:
            return
        segment_id = item.data(Qt.ItemDataRole.UserRole)
        if segment_id is None:
            return
        seg = self._find_segment(segment_id)
        if seg is None:
            return
        column = item.column()
        if column == 2:
            checked = item.checkState() == Qt.CheckState.Checked
            self._persist_segment(seg.id, needs_review=checked)
            seg.needs_review = checked
            self._refresh_segment_view()
        elif column == 3:
            new_speaker = item.text()
            if new_speaker == seg.speaker:
                return
            self._persist_segment(seg.id, speaker=new_speaker)
            seg.speaker = new_speaker
            self.segment_updated.emit(seg.id or 0)
        elif column == 4:
            new_text = item.text()
            if new_text == seg.edited_text:
                return
            self._persist_segment(seg.id, edited_text=new_text)
            seg.edited_text = new_text
            self.segment_updated.emit(seg.id or 0)

    def _find_segment(self, segment_id: int) -> SegmentRecord | None:
        for seg in self._segments:
            if seg.id == segment_id:
                return seg
        return None

    def _persist_segment(
        self,
        segment_id: int | None,
        *,
        edited_text: str | None = None,
        needs_review: bool | None = None,
        speaker: str | None = None,
    ) -> None:
        if segment_id is None:
            return
        conn, repo = self._open_repo()
        try:
            repo.update_segment_text(
                segment_id,
                edited_text=edited_text,
                needs_review=needs_review,
                speaker=speaker,
            )
        finally:
            conn.close()

    # ---------- search / replace ----------

    def _on_search(self) -> None:
        needle = self.search_edit.text()
        if not needle:
            return
        case_sensitive = self.case_sensitive.isChecked()

        def contains(haystack: str) -> bool:
            if case_sensitive:
                return needle in haystack
            return needle.lower() in haystack.lower()

        current_row = self.segment_table.currentRow()
        for row in range(current_row + 1, self.segment_table.rowCount()):
            item = self.segment_table.item(row, 4)
            if item and contains(item.text()):
                self.segment_table.setCurrentItem(item)
                return
        # wrap around
        for row in range(0, current_row + 1):
            item = self.segment_table.item(row, 4)
            if item and contains(item.text()):
                self.segment_table.setCurrentItem(item)
                return
        QMessageBox.information(self, "설교필기", "검색어를 찾지 못했습니다.")

    def _on_replace_all(self) -> None:
        needle = self.search_edit.text()
        if not needle:
            return
        replacement = self.replace_edit.text()
        case_sensitive = self.case_sensitive.isChecked()
        changes = 0
        for seg in self._segments:
            base = seg.edited_text or seg.clean_text or seg.raw_text
            if case_sensitive:
                if needle not in base:
                    continue
                new_text = base.replace(needle, replacement)
            else:
                if needle.lower() not in base.lower():
                    continue
                new_text = _case_insensitive_replace(base, needle, replacement)
            self._persist_segment(seg.id, edited_text=new_text)
            seg.edited_text = new_text
            changes += 1
        self._refresh_segment_view()
        QMessageBox.information(
            self, "설교필기", f"{changes}개 세그먼트를 치환했습니다."
        )

    # ---------- suggestions ----------

    def _refresh_suggestion_view(self) -> None:
        self.suggestion_list.clear()
        show_all = self.show_all_status.isChecked()
        for sug in self._suggestions:
            if not show_all and sug.status != "pending":
                continue
            label = (
                f"#{sug.id} [{sug.kind}] {sug.original_text} → "
                f"{sug.suggested_text}  ({sug.status})"
            )
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, sug.id)
            if sug.status == "applied":
                item.setForeground(QBrush(QColor(80, 130, 80)))
            elif sug.status == "ignored":
                item.setForeground(QBrush(QColor(150, 150, 150)))
            self.suggestion_list.addItem(item)

    def _on_suggestion_selected(self) -> None:
        items = self.suggestion_list.selectedItems()
        if not items:
            return
        sug_id = items[0].data(Qt.ItemDataRole.UserRole)
        sug = self._find_suggestion(sug_id)
        if sug is None:
            return
        for row in range(self.segment_table.rowCount()):
            item = self.segment_table.item(row, 4)
            if item and item.data(Qt.ItemDataRole.UserRole) == sug.segment_id:
                self.segment_table.setCurrentItem(item)
                break

    def _find_suggestion(self, sug_id: int) -> CorrectionSuggestionRecord | None:
        for sug in self._suggestions:
            if sug.id == sug_id:
                return sug
        return None

    def _on_apply_suggestion(self) -> None:
        items = self.suggestion_list.selectedItems()
        if not items:
            return
        sug_id = items[0].data(Qt.ItemDataRole.UserRole)
        sug = self._find_suggestion(sug_id)
        if sug is None or sug.status == "applied":
            return
        seg = self._find_segment(sug.segment_id)
        if seg is None:
            QMessageBox.warning(self, "설교필기", "대상 세그먼트를 찾지 못했습니다.")
            return
        new_edited = apply_correction_to_segment(
            raw_text=seg.raw_text,
            clean_text=seg.clean_text,
            edited_text=seg.edited_text,
            original=sug.original_text,
            suggested=sug.suggested_text,
        )
        conn, repo = self._open_repo()
        try:
            repo.update_segment_text(seg.id, edited_text=new_edited)
            repo.update_correction_status(sug.id, status="applied")
        finally:
            conn.close()
        seg.edited_text = new_edited
        sug.status = "applied"
        self.suggestion_changed.emit(sug.id or 0, "applied")
        self._refresh_segment_view()
        self._refresh_suggestion_view()

    def _on_ignore_suggestion(self) -> None:
        items = self.suggestion_list.selectedItems()
        if not items:
            return
        sug_id = items[0].data(Qt.ItemDataRole.UserRole)
        sug = self._find_suggestion(sug_id)
        if sug is None or sug.status == "ignored":
            return
        conn, repo = self._open_repo()
        try:
            repo.update_correction_status(sug.id, status="ignored")
        finally:
            conn.close()
        sug.status = "ignored"
        self.suggestion_changed.emit(sug.id or 0, "ignored")
        self._refresh_suggestion_view()

    # ---------- export ----------

    def _on_export(self) -> None:
        if not self._job_id or not self._segments:
            return
        target = QFileDialog.getExistingDirectory(self, "Export 폴더 선택")
        if not target:
            return
        result = _build_transcription_result(self._segments, self._job_id)
        pipeline = ExportPipeline(
            (
                ExportFormat.TXT,
                ExportFormat.JSON,
                ExportFormat.MD,
                ExportFormat.SRT,
                ExportFormat.VTT,
                ExportFormat.CSV,
            )
        )
        out_paths = pipeline.run(result, Path(target), self._job_id)
        QMessageBox.information(
            self,
            "설교필기",
            f"{len(out_paths)}개 파일을 생성했습니다.\n{target}",
        )


def _case_insensitive_replace(text: str, needle: str, replacement: str) -> str:
    if not needle:
        return text
    lowered_needle = needle.lower()
    out: list[str] = []
    i = 0
    while i < len(text):
        if text[i : i + len(needle)].lower() == lowered_needle:
            out.append(replacement)
            i += len(needle)
        else:
            out.append(text[i])
            i += 1
    return "".join(out)


def _build_transcription_result(
    segments: Iterable[SegmentRecord], job_id: str
) -> TranscriptionResult:
    """Render the editor's current state back into a :class:`TranscriptionResult`.

    Used by the Export button so the user gets the same priority order
    (``edited_text > clean_text > raw_text``) as the CLI export pipeline.
    """

    seg_list = list(segments)
    out_segments = [
        TranscriptSegment(
            start=s.start_sec,
            end=s.end_sec,
            text=s.raw_text,
            avg_logprob=s.avg_logprob,
            no_speech_prob=s.no_speech_prob,
            speaker=s.speaker,
            clean_text=s.clean_text,
            edited_text=s.edited_text,
        )
        for s in seg_list
    ]
    return TranscriptionResult(
        source_path=Path(job_id),
        audio_path=Path(job_id),
        language=None,
        model_name="-",
        preset="-",
        segments=out_segments,
        duration=seg_list[-1].end_sec if seg_list else None,
    )
