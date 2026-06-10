import os

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
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QDesktopServices
from PySide6.QtCore import QUrl

from src.core import settings


class SettingsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setAlignment(Qt.AlignmentFlag.AlignTop)
        root.setSpacing(16)
        root.setContentsMargins(24, 24, 24, 24)

        root.addWidget(self._build_company_group())
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

    # ------------------------------------------------------------------
    def _save_company(self):
        cfg = settings.load_config()
        cfg["company_name"] = self._company_name_edit.text().strip()
        settings.save_config(cfg)
        QMessageBox.information(self, "Tersimpan", "Nama perusahaan berhasil disimpan.")

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
