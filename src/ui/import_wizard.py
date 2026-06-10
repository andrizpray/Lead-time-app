"""
3-step Import Wizard for Excel DO records.

Step 1 – Pick file
Step 2 – Preview (valid rows = green, duplicates = red)
Step 3 – Confirm: choose skip/replace duplicates, then save
"""

from __future__ import annotations

import logging
from typing import Any

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QSizePolicy,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.utils.excel_handler import insert_records, parse_excel
from src.ui.loading_overlay import LoadingOverlay

logger = logging.getLogger(__name__)

_GREEN = QColor("#d1fae5")   # valid rows
_RED = QColor("#fee2e2")     # duplicate rows
_YELLOW = QColor("#fef9c3")  # error rows


# ---------------------------------------------------------------------------
# Background worker
# ---------------------------------------------------------------------------

class _InsertWorker(QThread):
    progress = Signal(int)
    finished = Signal(int, int)   # (inserted, replaced)
    error = Signal(str)

    def __init__(
        self,
        records: list[dict],
        replace_duplicates: list[dict],
        parent=None,
    ):
        super().__init__(parent)
        self._records = records
        self._replace = replace_duplicates

    def run(self):
        try:
            total = len(self._records) + len(self._replace)
            # emit rough progress in chunks
            from src.core.models import DORecord
            from src.core.database import database

            inserted = 0
            replaced = 0
            done = 0

            with database.atomic():
                for rec in self._records:
                    try:
                        DORecord.create(**rec)
                        inserted += 1
                    except Exception as exc:
                        logger.warning("Insert error: %s", exc)
                    done += 1
                    if total > 0:
                        self.progress.emit(int(done / total * 100))

                for dup in self._replace:
                    existing = dup["existing"]
                    incoming = dup["incoming"]
                    try:
                        for k, v in incoming.items():
                            setattr(existing, k, v)
                        existing.save()
                        replaced += 1
                    except Exception as exc:
                        logger.warning("Replace error: %s", exc)
                    done += 1
                    if total > 0:
                        self.progress.emit(int(done / total * 100))

            self.progress.emit(100)
            self.finished.emit(inserted, replaced)
        except Exception as exc:
            self.error.emit(str(exc))


# ---------------------------------------------------------------------------
# Step widgets
# ---------------------------------------------------------------------------

class _Step1(QWidget):
    """File picker."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(16)

        title = QLabel("Import Data Excel")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        hint = QLabel("Pilih file .xlsx yang berisi sheet \"LOADING TIME 2026\"")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setStyleSheet("color: #9ca3af;")
        layout.addWidget(hint)

        self._path_label = QLabel("Belum ada file dipilih")
        self._path_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._path_label.setStyleSheet(
            "background:#f1f5f9; border:1px solid #cbd5e1; border-radius:6px; padding:8px 16px;"
        )
        layout.addWidget(self._path_label)

        btn_row = QHBoxLayout()
        btn_row.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._browse_btn = QPushButton("Pilih File...")
        self._browse_btn.setFixedWidth(140)
        self._browse_btn.clicked.connect(self._browse)
        btn_row.addWidget(self._browse_btn)

        self._import_btn = QPushButton("Import →")
        self._import_btn.setFixedWidth(140)
        self._import_btn.setEnabled(False)
        self._import_btn.setStyleSheet(
            "QPushButton:enabled { background:#3b82f6; color:#fff; border-radius:6px; padding:8px; font-weight:bold; }"
        )
        btn_row.addWidget(self._import_btn)

        layout.addLayout(btn_row)

        self._file_path: str = ""

    # ------------------------------------------------------------------
    def _browse(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Pilih File Excel",
            "",
            "Excel Files (*.xlsx *.xls)",
        )
        if path:
            self._file_path = path
            short = path if len(path) < 60 else "…" + path[-57:]
            self._path_label.setText(short)
            self._import_btn.setEnabled(True)

    @property
    def file_path(self) -> str:
        return self._file_path

    @property
    def import_button(self) -> QPushButton:
        return self._import_btn


# ---------------------------------------------------------------------------

_PREVIEW_HEADERS = [
    "Row", "TGL", "No DO", "No Shipment", "Customer",
    "Kota/Kab", "Jenis", "Ekspedisi", "Jenis Truk",
    "Loading Mulai", "Loading Selesai",
    "Tonase Roll", "Tonase Sheet", "Status",
]


class _Step2(QWidget):
    """Preview table."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        title = QLabel("Preview Data")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)

        self._summary = QLabel()
        self._summary.setStyleSheet("color: #475569;")
        layout.addWidget(self._summary)

        self._error_detail = QLabel()
        self._error_detail.setStyleSheet("color: #dc2626; font-size: 11px; padding: 4px 0;")
        self._error_detail.setWordWrap(True)
        layout.addWidget(self._error_detail)

        legend_row = QHBoxLayout()
        for color, text in [(_GREEN, "Valid"), (_RED, "Duplikat"), (_YELLOW, "Error")]:
            box = QLabel()
            box.setFixedSize(16, 16)
            box.setStyleSheet(f"background:{color.name()}; border:1px solid #94a3b8; border-radius:3px;")
            legend_row.addWidget(box)
            legend_row.addWidget(QLabel(text))
            legend_row.addSpacing(12)
        legend_row.addStretch()
        layout.addLayout(legend_row)

        self._table = QTableWidget()
        self._table.setColumnCount(len(_PREVIEW_HEADERS))
        self._table.setHorizontalHeaderLabels(_PREVIEW_HEADERS)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self._table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self._table)

        btn_row = QHBoxLayout()
        self._back_btn = QPushButton("← Kembali")
        self._next_btn = QPushButton("Lanjut →")
        self._next_btn.setStyleSheet(
            "QPushButton { background:#3b82f6; color:#fff; border-radius:6px; padding:8px 16px; font-weight:bold; }"
        )
        btn_row.addWidget(self._back_btn)
        btn_row.addStretch()
        btn_row.addWidget(self._next_btn)
        layout.addLayout(btn_row)

    # ------------------------------------------------------------------
    def populate(self, result: dict):
        success: list[dict] = result["success"]
        duplicates: list[dict] = result["duplicates"]
        errors: list[dict] = result["errors"]

        all_rows: list[tuple[dict | None, str, int | str]] = []
        # (record_dict_or_None, status_label, row_number)
        for rec in success:
            all_rows.append((rec, "Valid", ""))
        for dup in duplicates:
            all_rows.append((dup["incoming"], "Duplikat", ""))
        for err in errors:
            all_rows.append((None, f"Error: {err['reason']}", err["row"]))

        self._table.setRowCount(len(all_rows))

        color_map = {"Valid": _GREEN, "Duplikat": _RED}

        for r_idx, (rec, status, row_num) in enumerate(all_rows):
            bg = color_map.get(status, _YELLOW)

            def _item(text: str) -> QTableWidgetItem:
                item = QTableWidgetItem(str(text))
                item.setBackground(bg)
                return item

            self._table.setItem(r_idx, 0, _item(str(row_num)))
            if rec:
                self._table.setItem(r_idx, 1, _item(str(rec.get("tgl", ""))))
                self._table.setItem(r_idx, 2, _item(rec.get("no_do", "")))
                self._table.setItem(r_idx, 3, _item(rec.get("no_shipment", "")))
                self._table.setItem(r_idx, 4, _item(rec.get("customer", "")))
                self._table.setItem(r_idx, 5, _item(rec.get("kota_kab", "")))
                self._table.setItem(r_idx, 6, _item(rec.get("jenis", "")))
                self._table.setItem(r_idx, 7, _item(rec.get("ekspedisi", "")))
                self._table.setItem(r_idx, 8, _item(rec.get("jenis_truk", "")))
                self._table.setItem(r_idx, 9, _item(str(rec.get("loading_mulai", ""))))
                self._table.setItem(r_idx, 10, _item(str(rec.get("loading_selesai", ""))))
                self._table.setItem(r_idx, 11, _item(str(rec.get("tonase_roll", ""))))
                self._table.setItem(r_idx, 12, _item(str(rec.get("tonase_sheet", ""))))
            else:
                for col in range(1, 13):
                    self._table.setItem(r_idx, col, _item(""))
            self._table.setItem(r_idx, 13, _item(status))

        self._summary.setText(
            f"Total baris: {len(all_rows)}  |  "
            f"✅ Valid: {len(success)}  |  "
            f"⚠️ Duplikat: {len(duplicates)}  |  "
            f"❌ Error: {len(errors)}"
        )

        # Error detail — show first 3 error reasons
        if errors:
            from collections import Counter
            reason_counts = Counter(e["reason"] for e in errors)
            samples = [f"{reason} (×{cnt})" for reason, cnt in reason_counts.most_common(3)]
            self._error_detail.setText("  • " + "\n  • ".join(samples))
        else:
            self._error_detail.setText("")

    @property
    def back_button(self) -> QPushButton:
        return self._back_btn

    @property
    def next_button(self) -> QPushButton:
        return self._next_btn


# ---------------------------------------------------------------------------

class _Step3(QWidget):
    """Confirmation + save."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        title = QLabel("Konfirmasi & Simpan")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)

        self._info = QLabel()
        self._info.setWordWrap(True)
        layout.addWidget(self._info)

        dup_box = QWidget()
        dup_box.setStyleSheet(
            "background:#fef2f2; border:1px solid #fca5a5; border-radius:8px; padding:12px;"
        )
        dup_layout = QVBoxLayout(dup_box)
        dup_layout.setContentsMargins(12, 12, 12, 12)
        dup_label = QLabel("Penanganan Duplikat:")
        dup_label.setStyleSheet("font-weight: bold;")
        dup_layout.addWidget(dup_label)

        self._radio_skip = QRadioButton("Lewati duplikat (biarkan data lama)")
        self._radio_replace = QRadioButton("Timpa duplikat dengan data baru")
        self._radio_skip.setChecked(True)
        dup_layout.addWidget(self._radio_skip)
        dup_layout.addWidget(self._radio_replace)
        layout.addWidget(dup_box)

        self._progress = QProgressBar()
        self._progress.setRange(0, 100)
        self._progress.setValue(0)
        self._progress.setVisible(False)
        layout.addWidget(self._progress)

        self._status_label = QLabel()
        self._status_label.setStyleSheet("color: #475569;")
        layout.addWidget(self._status_label)

        layout.addStretch()

        btn_row = QHBoxLayout()
        self._back_btn = QPushButton("← Kembali")
        self._save_btn = QPushButton("Simpan ke Database")
        self._save_btn.setStyleSheet(
            "QPushButton { background:#16a34a; color:#fff; border-radius:6px; "
            "padding:10px 20px; font-weight:bold; font-size:14px; } "
            "QPushButton:disabled { background:#94a3b8; }"
        )
        btn_row.addWidget(self._back_btn)
        btn_row.addStretch()
        btn_row.addWidget(self._save_btn)
        layout.addLayout(btn_row)

    # ------------------------------------------------------------------
    def set_summary(self, n_valid: int, n_dup: int):
        self._info.setText(
            f"Akan menyimpan <b>{n_valid}</b> baris valid ke database.<br>"
            f"Terdapat <b>{n_dup}</b> baris duplikat — pilih penanganan di bawah."
        )
        self._dup_box_visible(n_dup > 0)

    def _dup_box_visible(self, visible: bool):
        # find the dup_box widget (second child of layout at index 2)
        item = self.layout().itemAt(2)
        if item and item.widget():
            item.widget().setVisible(visible)

    @property
    def replace_duplicates(self) -> bool:
        return self._radio_replace.isChecked()

    @property
    def back_button(self) -> QPushButton:
        return self._back_btn

    @property
    def save_button(self) -> QPushButton:
        return self._save_btn

    @property
    def progress_bar(self) -> QProgressBar:
        return self._progress

    @property
    def status_label(self) -> QLabel:
        return self._status_label


# ---------------------------------------------------------------------------
# Main wizard widget
# ---------------------------------------------------------------------------

class ImportWizardWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._result: dict = {"success": [], "duplicates": [], "errors": []}
        self._worker: _InsertWorker | None = None

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)

        # step indicator
        self._step_label = QLabel()
        self._step_label.setStyleSheet("color: #94a3b8; font-size: 12px;")
        root.addWidget(self._step_label)

        # stacked pages
        self._stack = QStackedWidget()
        self._step1 = _Step1()
        self._step2 = _Step2()
        self._step3 = _Step3()
        self._stack.addWidget(self._step1)   # 0
        self._stack.addWidget(self._step2)   # 1
        self._stack.addWidget(self._step3)   # 2
        root.addWidget(self._stack)

        self._update_step_label()

        # wire buttons
        self._step1.import_button.clicked.connect(self._on_import)
        self._step2.back_button.clicked.connect(lambda: self._goto(0))
        self._step2.next_button.clicked.connect(lambda: self._goto(2))
        self._step3.back_button.clicked.connect(lambda: self._goto(1))
        self._step3.save_button.clicked.connect(self._on_save)

    # ------------------------------------------------------------------
    def _goto(self, idx: int):
        self._stack.setCurrentIndex(idx)
        self._update_step_label()

    def _update_step_label(self):
        idx = self._stack.currentIndex()
        steps = ["Pilih File", "Preview", "Konfirmasi"]
        parts = []
        for i, name in enumerate(steps):
            if i == idx:
                parts.append(f"<b>{name}</b>")
            else:
                parts.append(name)
        self._step_label.setText(" › ".join(parts))

    # ------------------------------------------------------------------
    def _on_import(self):
        path = self._step1.file_path
        if not path:
            return

        self._step1.import_button.setEnabled(False)
        self._step1.import_button.setText("Memproses...")

        overlay = LoadingOverlay(self)
        overlay.show_with_message('Mengimpor data...')
        QApplication.processEvents()

        try:
            self._result = parse_excel(path)
        except Exception as exc:
            QMessageBox.critical(self, "Error", f"Gagal membaca file:\n{exc}")
            self._step1.import_button.setEnabled(True)
            self._step1.import_button.setText("Import →")
            return
        finally:
            overlay.hide_overlay()
            self._step1.import_button.setEnabled(True)
            self._step1.import_button.setText("Import →")

        if not self._result["success"] and not self._result["duplicates"]:
            QMessageBox.warning(
                self,
                "Tidak Ada Data",
                "Tidak ditemukan baris yang valid.\n"
                "Periksa format file dan nama kolom.",
            )
            return

        self._step2.populate(self._result)
        self._goto(1)

        n_dup = len(self._result["duplicates"])
        n_valid = len(self._result["success"])
        self._step3.set_summary(n_valid, n_dup)

    # ------------------------------------------------------------------
    def _on_save(self):
        if not self._result["success"] and not self._result["duplicates"]:
            QMessageBox.warning(self, "Tidak Ada Data", "Tidak ada data untuk disimpan.")
            return

        self._step3.save_button.setEnabled(False)
        self._step3.back_button.setEnabled(False)
        self._step3.progress_bar.setVisible(True)
        self._step3.progress_bar.setValue(0)
        self._step3.status_label.setText("Menyimpan data…")

        replace = self._result["duplicates"] if self._step3.replace_duplicates else []

        self._worker = _InsertWorker(
            self._result["success"],
            replace,
            parent=self,
        )
        self._worker.progress.connect(self._step3.progress_bar.setValue)
        self._worker.finished.connect(self._on_save_done)
        self._worker.error.connect(self._on_save_error)
        self._worker.start()

    def _on_save_done(self, inserted: int, replaced: int):
        self._step3.progress_bar.setValue(100)
        self._step3.status_label.setText(
            f"Selesai! {inserted} baris disimpan, {replaced} baris diperbarui."
        )
        self._step3.status_label.setStyleSheet("color: #16a34a; font-weight: bold;")
        self._step3.save_button.setText("Selesai ✓")
        self._step3.back_button.setEnabled(True)

        QMessageBox.information(
            self,
            "Import Berhasil",
            f"Data berhasil disimpan.\n{inserted} baris baru, {replaced} baris diperbarui.",
        )
        # reset wizard
        self._result = {"success": [], "duplicates": [], "errors": []}
        self._goto(0)
        self._step3.save_button.setEnabled(True)
        self._step3.save_button.setText("Simpan ke Database")
        self._step3.progress_bar.setVisible(False)
        self._step3.status_label.setText("")
        self._step3.status_label.setStyleSheet("color: #475569;")

    def _on_save_error(self, msg: str):
        self._step3.progress_bar.setVisible(False)
        self._step3.status_label.setText(f"Error: {msg}")
        self._step3.status_label.setStyleSheet("color: #dc2626;")
        self._step3.save_button.setEnabled(True)
        self._step3.back_button.setEnabled(True)
        QMessageBox.critical(self, "Error Simpan", f"Gagal menyimpan:\n{msg}")
