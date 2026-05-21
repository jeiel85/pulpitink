"""User glossary dict editor tab (PySide6).

Allows users to manage their custom dictionary (Canonical Word -> Misspellings)
and export/import them via CSV.
"""

from __future__ import annotations

import csv
import json
import logging
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from pulpit_ink.app.paths import get_app_paths
from pulpit_ink.core.postprocess.lexicon import save_user_lexicon
from pulpit_ink.core.utils.i18n import tr

logger = logging.getLogger("pulpit_ink.ui.glossary")


class GlossaryAddEditDialog(QDialog):
    """Dialog to add or edit a glossary entry."""

    def __init__(
        self,
        parent: QWidget | None = None,
        canonical: str = "",
        wrong_forms: list[str] | None = None,
    ) -> None:
        super().__init__(parent)
        self.is_edit = bool(canonical)
        self.setWindowTitle(
            tr("용어 수정") if self.is_edit else tr("새 용어 추가")
        )
        self.resize(400, 180)

        layout = QFormLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        self.canonical_input = QLineEdit(canonical)
        if self.is_edit:
            # Editing canonical word is not recommended (can just recreate it),
            # but we can let them edit it or make it read-only.
            # Making it read-only is cleaner to prevent key collision issues.
            self.canonical_input.setReadOnly(True)
            self.canonical_input.setStyleSheet("background-color: #f1f5f9; color: #64748b;")

        self.wrong_input = QLineEdit(
            ", ".join(wrong_forms) if wrong_forms else ""
        )
        self.wrong_input.setPlaceholderText(tr("예: 멜로힘, 엘로임 (쉼표로 구분)"))

        layout.addRow(tr("올바른 단어 (Canonical):"), self.canonical_input)
        layout.addRow(tr("오인식 발음 패턴들:"), self.wrong_input)

        # Help label
        help_label = QLabel(
            tr("* 오인식 발음 패턴이 여러 개인 경우 쉼표(,)로 구분하여 입력해 주세요.")
        )
        help_label.setStyleSheet("color: #64748b; font-size: 9pt;")
        layout.addRow("", help_label)

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            self,
        )
        self.buttons.button(QDialogButtonBox.StandardButton.Ok).setText(tr("확인"))
        self.buttons.button(QDialogButtonBox.StandardButton.Cancel).setText(tr("취소"))
        self.buttons.accepted.connect(self.validate_and_accept)
        self.buttons.rejected.connect(self.reject)
        layout.addRow("", self.buttons)

    def validate_and_accept(self) -> None:
        canonical = self.canonical_input.text().strip()
        if not canonical:
            QMessageBox.warning(
                self, tr("경고"), tr("올바른 단어(Canonical)를 입력해 주세요.")
            )
            return
        self.accept()

    def get_data(self) -> tuple[str, list[str]]:
        canonical = self.canonical_input.text().strip()
        wrong_raw = self.wrong_input.text()
        # Split by comma and clean whitespace
        wrong_forms = [
            w.strip() for w in wrong_raw.split(",") if w.strip()
        ]
        return canonical, wrong_forms


class GlossaryTab(QWidget):
    """Tab widget for managing the user's custom STT dictionary."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._dict_path = get_app_paths().data_dir / "user_dict.json"
        self._entries: dict[str, list[str]] = {}

        self._build_ui()
        self.load_data()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # Premium header info banner
        info_label = QLabel(
            tr("💡 <b>사용자 맞춤 용어 사전</b>: 음성 인식(STT) 과정에서 기독교 전용 단어, 인명, "
               "교회 명칭 등이 엉뚱한 한글로 오역될 때 등록해두면 자동으로 교정됩니다.")
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("""
            background-color: #f8fafc;
            border-left: 4px solid #1e3c72;
            padding: 8px 12px;
            border-radius: 4px;
            color: #334155;
        """)
        layout.addWidget(info_label)

        # Toolbar layout
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(tr("등록된 단어 검색..."))
        self.search_input.textChanged.connect(self._on_search_changed)
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 6px 12px;
                border: 1px solid #cbd5e1;
                border-radius: 4px;
                background-color: #ffffff;
            }
            QLineEdit:focus {
                border: 1px solid #1e3c72;
            }
        """)
        toolbar.addWidget(self.search_input, 1)

        self.add_btn = QPushButton(tr("단어 추가"))
        self.add_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.add_btn.clicked.connect(self._on_add)
        self.add_btn.setStyleSheet("""
            QPushButton {
                background-color: #1e3c72;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 4px;
                padding: 6px 14px;
            }
            QPushButton:hover {
                background-color: #2a5298;
            }
        """)
        toolbar.addWidget(self.add_btn)

        self.import_btn = QPushButton(tr("CSV 가져오기"))
        self.import_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.import_btn.clicked.connect(self._on_import)
        self.import_btn.setStyleSheet("""
            QPushButton {
                background-color: #f1f5f9;
                color: #334155;
                border: 1px solid #cbd5e1;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #e2e8f0;
            }
        """)
        toolbar.addWidget(self.import_btn)

        self.export_btn = QPushButton(tr("CSV 내보내기"))
        self.export_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.export_btn.clicked.connect(self._on_export)
        self.export_btn.setStyleSheet("""
            QPushButton {
                background-color: #f1f5f9;
                color: #334155;
                border: 1px solid #cbd5e1;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #e2e8f0;
            }
        """)
        toolbar.addWidget(self.export_btn)

        layout.addLayout(toolbar)

        # Table widget
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels([
            tr("올바른 단어 (Canonical)"),
            tr("오인식 발음 패턴들 (Wrong Spellings)"),
            tr("관리")
        ])

        # Table Styling
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                gridline-color: #f1f5f9;
                border-radius: 6px;
            }
            QHeaderView::section {
                background-color: #f8fafc;
                padding: 8px;
                border: none;
                border-bottom: 2px solid #e2e8f0;
                font-weight: bold;
                color: #475569;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #f1f5f9;
            }
        """)

        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 200)
        self.table.setColumnWidth(2, 120)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.doubleClicked.connect(self._on_table_double_clicked)
        layout.addWidget(self.table, 1)

    def load_data(self) -> None:
        """Load dictionary entries from the user_dict.json file."""
        self._entries.clear()
        if self._dict_path.exists():
            try:
                data = json.loads(self._dict_path.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    for k, v in data.items():
                        if isinstance(v, list):
                            self._entries[k] = [str(item) for item in v]
                        elif isinstance(v, str):
                            self._entries[k] = [v]
            except Exception as e:
                logger.error("사용자 사전을 불러오는데 실패했습니다: %s", e)

        self._refresh_table()

    def save_data(self) -> bool:
        """Save the memory entries into user_dict.json."""
        try:
            save_user_lexicon(self._dict_path, self._entries)
            return True
        except Exception as e:
            QMessageBox.critical(
                self, tr("저장 오류"), tr("용어 사전을 저장하지 못했습니다.\n오류:") + f" {e}"
            )
            return False

    def _refresh_table(self) -> None:
        """Render the database entries onto QTableWidget."""
        self.table.setRowCount(0)

        # Sort key alphabetically for easier lookup
        sorted_keys = sorted(self._entries.keys())
        self.table.setRowCount(len(sorted_keys))

        for row, canonical in enumerate(sorted_keys):
            wrong_list = self._entries[canonical]

            # 1. Canonical item
            canonical_item = QTableWidgetItem(canonical)
            canonical_item.setData(Qt.ItemDataRole.UserRole, canonical)
            self.table.setItem(row, 0, canonical_item)

            # 2. Wrong forms
            wrong_text = ", ".join(wrong_list)
            wrong_item = QTableWidgetItem(wrong_text)
            self.table.setItem(row, 1, wrong_item)

            # 3. Actions cell (Edit & Delete buttons)
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(4, 2, 4, 2)
            actions_layout.setSpacing(6)

            edit_sub_btn = QPushButton(tr("수정"))
            edit_sub_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            edit_sub_btn.setStyleSheet("""
                QPushButton {
                    background-color: #f1f5f9;
                    color: #0f172a;
                    border: 1px solid #cbd5e1;
                    border-radius: 3px;
                    padding: 2px 6px;
                    font-size: 9pt;
                }
                QPushButton:hover {
                    background-color: #cbd5e1;
                }
            """)
            # Store key for slot mapping
            edit_sub_btn.clicked.connect(
                lambda checked=False, key=canonical: self._on_edit_key(key)
            )

            del_sub_btn = QPushButton(tr("삭제"))
            del_sub_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            del_sub_btn.setStyleSheet("""
                QPushButton {
                    background-color: #fee2e2;
                    color: #991b1b;
                    border: 1px solid #fca5a5;
                    border-radius: 3px;
                    padding: 2px 6px;
                    font-size: 9pt;
                }
                QPushButton:hover {
                    background-color: #fca5a5;
                }
            """)
            del_sub_btn.clicked.connect(
                lambda checked=False, key=canonical: self._on_delete_key(key)
            )

            actions_layout.addWidget(edit_sub_btn)
            actions_layout.addWidget(del_sub_btn)
            self.table.setCellWidget(row, 2, actions_widget)

        self._on_search_changed(self.search_input.text())

    def _on_search_changed(self, text: str) -> None:
        """Filter table items by search keyword."""
        query = text.strip().lower()
        for row in range(self.table.rowCount()):
            canonical_item = self.table.item(row, 0)
            wrong_item = self.table.item(row, 1)

            if canonical_item is None or wrong_item is None:
                continue

            canonical = canonical_item.text().lower()
            wrong = wrong_item.text().lower()

            if not query or query in canonical or query in wrong:
                self.table.setRowHidden(row, False)
            else:
                self.table.setRowHidden(row, True)

    def _on_add(self) -> None:
        """Open add dialog."""
        dialog = GlossaryAddEditDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            canonical, wrong_forms = dialog.get_data()

            if canonical in self._entries:
                reply = QMessageBox.question(
                    self,
                    tr("중복된 단어"),
                    tr(f"'{canonical}' 단어는 이미 사전에 존재합니다.\n덮어쓰시겠습니까?"),
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                )
                if reply == QMessageBox.StandardButton.No:
                    return

            self._entries[canonical] = wrong_forms
            if self.save_data():
                self._refresh_table()

    def _on_edit_key(self, key: str) -> None:
        """Open edit dialog for specific key."""
        wrong_forms = self._entries.get(key, [])
        dialog = GlossaryAddEditDialog(self, canonical=key, wrong_forms=wrong_forms)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            _, updated_wrongs = dialog.get_data()
            self._entries[key] = updated_wrongs
            if self.save_data():
                self._refresh_table()

    def _on_table_double_clicked(self) -> None:
        """Trigger edit when double clicking a row."""
        selected_ranges = self.table.selectedRanges()
        if not selected_ranges:
            return
        row = selected_ranges[0].topRow()
        item = self.table.item(row, 0)
        if item is not None:
            key = item.data(Qt.ItemDataRole.UserRole)
            self._on_edit_key(key)

    def _on_delete_key(self, key: str) -> None:
        """Delete specific entry with confirmation."""
        reply = QMessageBox.question(
            self,
            tr("삭제 확인"),
            tr(f"정말로 '{key}' 용어 정의를 삭제하시겠습니까?"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            if key in self._entries:
                del self._entries[key]
                if self.save_data():
                    self._refresh_table()

    def _on_import(self) -> None:
        """Import from CSV."""
        path_str, _ = QFileDialog.getOpenFileName(
            self, tr("CSV 파일 가져오기"), "", tr("CSV 파일 (*.csv);;모든 파일 (*.*)")
        )
        if not path_str:
            return

        import_path = Path(path_str)
        try:
            imported_count = 0
            with open(import_path, newline="", encoding="utf-8-sig") as f:
                reader = csv.reader(f)
                for row in reader:
                    if not row:
                        continue
                    canonical = row[0].strip()
                    if not canonical:
                        continue
                    # Extra cells are the misrenderings
                    wrong_forms = [w.strip() for w in row[1:] if w.strip()]

                    # Merge or add
                    if canonical in self._entries:
                        # Append new unique ones to existing list
                        existing = self._entries[canonical]
                        for wf in wrong_forms:
                            if wf not in existing:
                                existing.append(wf)
                        self._entries[canonical] = existing
                    else:
                        self._entries[canonical] = wrong_forms
                    imported_count += 1

            if imported_count > 0:
                if self.save_data():
                    self._refresh_table()
                    QMessageBox.information(
                        self,
                        tr("가져오기 완료"),
                        tr(f"총 {imported_count}개의 용어 정의를 가져왔습니다.")
                    )
            else:
                QMessageBox.warning(
                    self, tr("경고"), tr("가져올 수 있는 유효한 데이터가 CSV 파일에 존재하지 않습니다.")
                )
        except Exception as e:
            QMessageBox.critical(
                self, tr("가져오기 오류"), tr("CSV 파일 가져오기 중 오류가 발생했습니다.\n오류:") + f" {e}"
            )

    def _on_export(self) -> None:
        """Export to CSV."""
        if not self._entries:
            QMessageBox.warning(
                self, tr("경고"), tr("내보낼 사전에 데이터가 없습니다.")
            )
            return

        path_str, _ = QFileDialog.getSaveFileName(
            self, tr("CSV 파일 내보내기"), "user_dict_export.csv", tr("CSV 파일 (*.csv);;모든 파일 (*.*)")
        )
        if not path_str:
            return

        export_path = Path(path_str)
        try:
            with open(export_path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                for canonical in sorted(self._entries.keys()):
                    row = [canonical] + self._entries[canonical]
                    writer.writerow(row)
            QMessageBox.information(
                self, tr("내보내기 완료"), tr("사전 데이터를 CSV 파일로 안전하게 저장했습니다!")
            )
        except Exception as e:
            QMessageBox.critical(
                self, tr("내보내기 오류"), tr("CSV 파일 내보내기 중 오류가 발생했습니다.\n오류:") + f" {e}"
            )
