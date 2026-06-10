import os
from datetime import date as _date

from PySide6.QtCore import QDate, Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QPushButton,
    QFileDialog,
    QMessageBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QDateEdit,
)

from src.core import settings


class SettingsWidget(QWidget):
    _SCHED_COLS = [
        "Tgl Mulai", "Tgl Akhir",
        "Shift 1 Mulai", "Shift 1 Selesai",
        "Shift 2 Mulai", "Shift 2 Selesai",
    ]
    _SCHED_KEYS = [
        "tgl_mulai", "tgl_akhir",
        "shift_1_start", "shift_1_end",
        "shift_2_start", "shift_2_end",
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setAlignment(Qt.AlignmentFlag.AlignTop)
        root.setSpacing(16)
        root.setContentsMargins(24, 24, 24, 24)

        root.addWidget(self._build_company_group())
        root.addWidget(self._build_shift_group())
        root.addWidget(self._build_database_group())
        root.addWidget(self._build_about_group())

    # ------------------------------------------------------------------
    def _build_company_group(self) -> QGroupBox:
        box = QGroupBox("Profil Perusahaan")
        layout = QVBoxLayout(box)
        layout.setSpacing(8)

        self._company_name_edit = QLineEdit()
        self._company_name_edit.setPlaceholderText("Nama perusahaan")

        save_btn = QPushButton("Simpan")
        save_btn.setFixedWidth(100)
        save_btn.clicked.connect(self._save_company)

        layout.addWidget(QLabel("Nama Perusahaan:"))
        layout.addWidget(self._company_name_edit)
        layout.addWidget(save_btn, alignment=Qt.AlignmentFlag.AlignLeft)
        return box

    # ------------------------------------------------------------------
    def _build_shift_group(self) -> QGroupBox:
        box = QGroupBox("Jadwal Shift (per Rentang Tanggal)")
        layout = QVBoxLayout(box)
        layout.setSpacing(8)

        hint = QLabel(
            "Setiap baris = satu jadwal shift untuk rentang tanggal tertentu.\n"
            "Tgl Akhir kosong = berlaku sampai sekarang (open-ended).\n"
            "Klik dua kali sel untuk edit."
        )
        hint.setStyleSheet("color: #64748B; font-size: 11px;")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        self._sched_table = QTableWidget()
        self._sched_table.setColumnCount(len(self._SCHED_COLS))
        self._sched_table.setHorizontalHeaderLabels(self._SCHED_COLS)
        self._sched_table.setMinimumHeight(120)
        self._sched_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._sched_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._sched_table.verticalHeader().setVisible(False)
        self._sched_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #E2E8F0;
                font-size: 11px;
                gridline-color: #E2E8F0;
            }
            QHeaderView::section {
                background-color: #F1F5F9;
                color: #059669;
                font-weight: 600;
                font-size: 11px;
                padding: 4px;
                border-bottom: 2px solid #059669;
                border-right: 1px solid #E2E8F0;
            }
            QTableWidget::item:alternate { background-color: #F8FAFC; }
        """)
        self._sched_table.setAlternatingRowColors(True)
        layout.addWidget(self._sched_table)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        add_btn = QPushButton("+ Tambah Jadwal")
        add_btn.clicked.connect(self._add_schedule)
        del_btn = QPushButton("Hapus Baris")
        del_btn.clicked.connect(self._delete_schedule)
        save_btn = QPushButton("Simpan & Re-Kalkulasi")
        save_btn.setStyleSheet("QPushButton { background-color: #059669; color: white; font-weight: bold; }")
        save_btn.clicked.connect(self._save_shift)

        btn_row.addWidget(add_btn)
        btn_row.addWidget(del_btn)
        btn_row.addStretch()
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

        return box

    # ------------------------------------------------------------------
    def _build_database_group(self) -> QGroupBox:
        box = QGroupBox("Database")
        layout = QVBoxLayout(box)
        layout.setSpacing(8)

        self._db_path_label = QLabel()
        self._db_path_label.setWordWrap(True)
        self._db_path_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )

        layout.addWidget(QLabel("Lokasi Database:"))
        layout.addWidget(self._db_path_label)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        backup_btn = QPushButton("Backup Database")
        restore_btn = QPushButton("Restore Database")
        open_folder_btn = QPushButton("Buka Folder Backup")

        backup_btn.clicked.connect(self._backup)
        restore_btn.clicked.connect(self._restore)
        open_folder_btn.clicked.connect(self._open_backup_folder)

        btn_row.addWidget(backup_btn)
        btn_row.addWidget(restore_btn)
        btn_row.addWidget(open_folder_btn)
        btn_row.addStretch()

        layout.addLayout(btn_row)
        return box

    # ------------------------------------------------------------------
    def _build_about_group(self) -> QGroupBox:
        box = QGroupBox("Tentang Aplikasi")
        layout = QVBoxLayout(box)
        layout.setSpacing(4)
        layout.addWidget(QLabel("Lead Time Management System v1.0"))
        layout.addWidget(QLabel("Python + PySide6 + SQLite"))
        return box

    # ------------------------------------------------------------------
    def refresh(self):
        cfg = settings.load_config()
        self._company_name_edit.setText(cfg.get("company_name", ""))

        db_path = cfg.get("db_path", "")
        if not db_path:
            default = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "..", "..", "data", "leadtime.db")
            )
            self._db_path_label.setText(f"{default} (default)")
        else:
            self._db_path_label.setText(db_path)

        # Load schedules into table
        schedules = cfg.get("shift_schedules", [])
        self._sched_table.setRowCount(len(schedules))
        for row, s in enumerate(schedules):
            for col, key in enumerate(self._SCHED_KEYS):
                val = s.get(key, "")
                if key in ("tgl_mulai", "tgl_akhir") and val:
                    d = _date.fromisoformat(val) if isinstance(val, str) else val
                    item = QTableWidgetItem(d.strftime("%d/%m/%Y"))
                else:
                    item = QTableWidgetItem(str(val) if val else "")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self._sched_table.setItem(row, col, item)

    # ------------------------------------------------------------------
    def _save_company(self):
        cfg = settings.load_config()
        cfg["company_name"] = self._company_name_edit.text().strip()
        settings.save_config(cfg)
        QMessageBox.information(self, "Tersimpan", "Nama perusahaan berhasil disimpan.")

    def _add_schedule(self):
        """Tambah baris baru ke tabel dengan default schedule."""
        row = self._sched_table.rowCount()
        self._sched_table.setRowCount(row + 1)
        defaults = ["01/01/2026", "", "07:00", "17:59", "19:00", "06:59"]
        for col, val in enumerate(defaults):
            item = QTableWidgetItem(val)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._sched_table.setItem(row, col, item)

    def _delete_schedule(self):
        rows = set(i.row() for i in self._sched_table.selectedIndexes())
        if not rows:
            QMessageBox.warning(self, "Hapus Jadwal", "Pilih baris yang ingin dihapus.")
            return
        for row in sorted(rows, reverse=True):
            self._sched_table.removeRow(row)

    def _save_shift(self):
        """Simpan jadwal shift dari tabel ke config, lalu re-kalkulasi DO."""
        schedules = []
        for row in range(self._sched_table.rowCount()):
            entry = {}
            for col, key in enumerate(self._SCHED_KEYS):
                item = self._sched_table.item(row, col)
                val = item.text().strip() if item else ""
                if key == "tgl_mulai":
                    if not val:
                        QMessageBox.warning(self, "Error", f"Baris {row+1}: Tgl Mulai wajib diisi.")
                        return
                    try:
                        d = _date.strptime(val, "%d/%m/%Y")
                        entry[key] = d.strftime("%Y-%m-%d")
                    except ValueError:
                        QMessageBox.warning(self, "Error", f"Baris {row+1}: Format Tgl Mulai salah (DD/MM/YYYY).")
                        return
                elif key == "tgl_akhir":
                    if val:
                        try:
                            d = _date.strptime(val, "%d/%m/%Y")
                            entry[key] = d.strftime("%Y-%m-%d")
                        except ValueError:
                            QMessageBox.warning(self, "Error", f"Baris {row+1}: Format Tgl Akhir salah (DD/MM/YYYY).")
                            return
                    else:
                        entry[key] = None
                else:
                    entry[key] = val if val else "00:00"
            schedules.append(entry)

        cfg = settings.load_config()
        cfg["shift_schedules"] = schedules
        settings.save_config(cfg)

        # Re-kalkulasi shift untuk semua DO
        reply = QMessageBox.question(
            self,
            "Re-Kalkulasi Shift",
            "Jadwal tersimpan. Re-kalkulasi shift untuk semua data DO?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._recalc_all_shifts()

        QMessageBox.information(self, "Tersimpan", "Jadwal shift berhasil disimpan.")

    def _recalc_all_shifts(self):
        """Re-kalkulasi shift untuk semua DO berdasarkan schedule baru."""
        try:
            from src.core.database import init_db, database
            from src.core.models import DORecord

            init_db()
            count = 0
            for rec in DORecord.select():
                rec.save()  # trigger re-detection
                count += 1
            database.close()
            QMessageBox.information(
                self,
                "Re-Kalkulasi Selesai",
                f"{count} DO berhasil di-rekalkulasi shift-nya.",
            )
        except Exception as e:
            QMessageBox.critical(self, "Gagal", f"Gagal re-kalkulasi:\n{e}")

    # ------------------------------------------------------------------
    def _backup(self):
        try:
            dest = settings.backup_database()
            QMessageBox.information(
                self,
                "Backup Berhasil",
                f"Database berhasil dibackup ke:\n{dest}",
            )
        except Exception as exc:
            QMessageBox.critical(self, "Backup Gagal", str(exc))

    def _restore(self):
        backup_dir = os.path.join(os.path.expanduser("~"), ".leadtime", "backups")
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Pilih File Backup",
            backup_dir if os.path.isdir(backup_dir) else os.path.expanduser("~"),
            "SQLite Database (*.db)",
        )
        if not path:
            return

        confirm = QMessageBox.question(
            self,
            "Konfirmasi Restore",
            f"Database aktif akan ditimpa dengan:\n{path}\n\nLanjutkan?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        if settings.restore_database(path):
            QMessageBox.information(self, "Restore Berhasil", "Database berhasil di-restore.")
        else:
            QMessageBox.critical(self, "Restore Gagal", "Gagal me-restore database.")

    def _open_backup_folder(self):
        backup_dir = os.path.join(os.path.expanduser("~"), ".leadtime", "backups")
        os.makedirs(backup_dir, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(backup_dir))
