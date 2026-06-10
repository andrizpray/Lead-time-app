from PySide6.QtWidgets import (
    QMainWindow,
    QPushButton,
    QFrame,
    QSplitter,
    QStackedWidget,
    QStatusBar,
    QVBoxLayout,
    QWidget,
    QLabel,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QShortcut, QKeySequence

from src.ui.dashboard import DashboardWidget
from src.ui.do_table import DOTableWidget
from src.ui.do_form import DOFormDialog
from src.ui.import_wizard import ImportWizardWidget
from src.ui.report_widget import ReportWidget
from src.ui.settings_widget import SettingsWidget


_SIDEBAR_STYLE = """
QWidget#sidebar {
    background-color: #1e293b;
    min-width: 220px;
    max-width: 220px;
}

QLabel#appTitle {
    color: #34d399;
    font-size: 16px;
    font-weight: bold;
    padding: 4px 8px 16px 8px;
}

QPushButton {
    background-color: transparent;
    color: #f1f5f9;
    border: none;
    border-radius: 6px;
    padding: 10px 16px;
    text-align: left;
    font-size: 13px;
}

QPushButton:hover {
    background-color: #334155;
}

QPushButton[active="true"] {
    background-color: #059669;
    color: #ffffff;
    font-weight: bold;
}
"""

_NAV_ITEMS = [
    ("◉ Dashboard", 0),
    ("☰ Data DO", 1),
    ("＋ Input DO", None),   # opens dialog, no page index
    ("⇧ Import Excel", 2),
    ("▤ Laporan", 3),
    ("⚙ Pengaturan", 4),
]


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # ── Light theme ────────────────────────────────────────────────────
        self.setStyleSheet("""
            QMainWindow {
                background-color: #F5F7FA;
            }
            QWidget {
                color: #0F172A;
                font-family: "Segoe UI", "Inter", Arial, sans-serif;
                font-size: 12px;
            }
            QGroupBox {
                background-color: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 8px;
                margin-top: 16px;
                padding: 16px;
                font-weight: 600;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
                color: #059669;
            }
            QPushButton {
                background-color: #059669;
                color: #FFFFFF;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #047857;
            }
            QPushButton:pressed {
                background-color: #065f46;
            }
            QPushButton:disabled {
                background-color: #CBD5E1;
                color: #94A3B8;
            }
            QLineEdit, QDateEdit, QTimeEdit, QComboBox, QSpinBox, QDoubleSpinBox,
            QTextEdit, QPlainTextEdit {
                background-color: #FFFFFF;
                color: #0F172A;
                border: 1px solid #E2E8F0;
                border-radius: 4px;
                padding: 4px 8px;
            }
            QLineEdit:focus, QDateEdit:focus, QTimeEdit:focus, QComboBox:focus,
            QSpinBox:focus, QDoubleSpinBox:focus {
                border: 1px solid #059669;
            }
            QComboBox::drop-down {
                border: none;
                padding-right: 6px;
            }
            QComboBox QAbstractItemView {
                background-color: #FFFFFF;
                color: #0F172A;
                selection-background-color: #059669;
                selection-color: #FFFFFF;
                border: 1px solid #E2E8F0;
            }
            QTableWidget, QTableView {
                background-color: #FFFFFF;
                color: #0F172A;
                gridline-color: #E2E8F0;
                border: 1px solid #E2E8F0;
                selection-background-color: #D1FAE5;
                selection-color: #0F172A;
            }
            QTableWidget::item, QTableView::item {
                padding: 4px;
            }
            QHeaderView::section {
                background-color: #F1F5F9;
                color: #059669;
                font-weight: bold;
                padding: 8px;
                border: none;
                border-right: 1px solid #E2E8F0;
                border-bottom: 2px solid #059669;
            }
            QLabel {
                color: #0F172A;
                background: transparent;
            }
            QScrollBar:vertical {
                background: #F1F5F9;
                width: 10px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #CBD5E1;
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #94A3B8;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar:horizontal {
                background: #F1F5F9;
                height: 10px;
                border-radius: 4px;
            }
            QScrollBar::handle:horizontal {
                background: #CBD5E1;
                border-radius: 4px;
                min-width: 20px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #94A3B8;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
            QProgressBar {
                background-color: #E2E8F0;
                border-radius: 4px;
                text-align: center;
                color: #0F172A;
            }
            QProgressBar::chunk {
                background-color: #059669;
                border-radius: 3px;
            }
            QTabWidget::pane {
                background-color: #FFFFFF;
                border: 1px solid #E2E8F0;
            }
            QTabBar::tab {
                background-color: #F1F5F9;
                color: #64748B;
                padding: 8px 16px;
                border: 1px solid #E2E8F0;
                border-bottom: none;
            }
            QTabBar::tab:selected {
                background-color: #FFFFFF;
                color: #059669;
                border-top: 2px solid #059669;
            }
            QTabBar::tab:hover {
                background-color: #E2E8F0;
            }
            QDialog {
                background-color: #F5F7FA;
            }
            QMessageBox {
                background-color: #F5F7FA;
            }
            QStatusBar {
                background-color: #0F172A;
                color: #F1F5F9;
            }
            QToolTip {
                background-color: #0F172A;
                color: #F1F5F9;
                border: 1px solid #059669;
                padding: 4px;
            }
            QSplitter::handle {
                background-color: #E2E8F0;
                width: 1px;
            }
        """)

        self.setWindowTitle("Lead Time App")
        self.resize(1100, 680)
        self._active_btn = None
        self._build_ui()
        self._setup_shortcuts()

    # ------------------------------------------------------------------
    def _build_ui(self):
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(0)

        # --- sidebar ---
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setStyleSheet(_SIDEBAR_STYLE)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(8, 16, 8, 16)
        sidebar_layout.setSpacing(4)

        app_title = QLabel("◆ LeadTime")
        app_title.setObjectName("appTitle")
        sidebar_layout.addWidget(app_title)

        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("color: #334155; max-height: 1px;")
        sidebar_layout.addWidget(separator)

        self._nav_buttons: list[QPushButton] = []
        for label, page_idx in _NAV_ITEMS:
            btn = QPushButton(label)
            btn.setProperty("active", False)
            btn.clicked.connect(lambda checked, idx=page_idx, b=btn: self._navigate(idx, b))
            sidebar_layout.addWidget(btn)
            self._nav_buttons.append(btn)

        sidebar_layout.addStretch()

        # --- content area with header ---
        content_container = QWidget()
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        self._page_header = QLabel("Dashboard")
        self._page_header.setStyleSheet(
            "font-size: 22px; font-weight: bold; color: #0F172A;"
            "padding: 16px 24px 8px 24px; background: transparent;"
        )
        content_layout.addWidget(self._page_header)

        self._stack = QStackedWidget()
        self._stack.addWidget(DashboardWidget())        # 0
        self._stack.addWidget(DOTableWidget())          # 1
        self._stack.addWidget(ImportWizardWidget())     # 2
        self._stack.addWidget(ReportWidget())           # 3
        self._stack.addWidget(SettingsWidget())             # 4

        content_layout.addWidget(self._stack, 1)

        splitter.addWidget(sidebar)
        splitter.addWidget(content_container)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        self.setCentralWidget(splitter)

        # --- status bar ---
        self._status_total = QLabel("Total DO: -")
        self._status_refresh = QLabel("Terakhir refresh: -")
        self._status_db = QLabel("DB: -")
        status = QStatusBar()
        status.addWidget(self._status_total)
        status.addWidget(self._status_refresh)
        status.addPermanentWidget(self._status_db)
        self.setStatusBar(status)

        # activate Dashboard by default
        self._navigate(0, self._nav_buttons[0])

    # ------------------------------------------------------------------
    def _setup_shortcuts(self):
        """Keyboard shortcuts for sidebar navigation."""
        mapping = [
            ("Ctrl+1", 0, self._nav_buttons[0]),       # Dashboard
            ("Ctrl+2", 1, self._nav_buttons[1]),       # Data DO
            ("Ctrl+3", 2, self._nav_buttons[3]),       # Import
            ("Ctrl+4", 3, self._nav_buttons[4]),       # Laporan
            ("Ctrl+5", 4, self._nav_buttons[5]),       # Pengaturan
        ]
        for key, idx, btn in mapping:
            sc = QShortcut(QKeySequence(key), self)
            sc.activated.connect(lambda i=idx, b=btn: self._navigate(i, b))

        # Ctrl+N = New DO (dialog)
        sc_new = QShortcut(QKeySequence("Ctrl+N"), self)
        sc_new.activated.connect(lambda: self._navigate(None, self._nav_buttons[2]))

        # Ctrl+Q = Quit
        QShortcut(QKeySequence("Ctrl+Q"), self).activated.connect(self.close)

    # ------------------------------------------------------------------
    def _navigate(self, page_idx, btn: QPushButton):
        if page_idx is None:
            # "Input DO" opens a dialog instead of switching pages
            dlg = DOFormDialog(self)
            if dlg.exec():
                from src.core.models import DORecord
                data = dlg.get_data()
                try:
                    DORecord.create(**data)
                except Exception as exc:
                    from PySide6.QtWidgets import QMessageBox
                    QMessageBox.critical(self, "Error", f"Gagal menyimpan:\n{exc}")
                # Refresh DO table so it reflects the new record if visible
                do_widget = self._stack.widget(1)
                do_widget.refresh()
            return

        if self._active_btn:
            self._active_btn.setProperty("active", False)
            self._active_btn.style().unpolish(self._active_btn)
            self._active_btn.style().polish(self._active_btn)

        btn.setProperty("active", True)
        btn.style().unpolish(btn)
        btn.style().polish(btn)
        self._active_btn = btn

        self._stack.setCurrentIndex(page_idx)

        # Update page header title
        titles = {0: "Dashboard", 1: "Data DO", 2: "Import Excel", 3: "Laporan", 4: "Pengaturan"}
        self._page_header.setText(titles.get(page_idx, ""))

        # Update status bar
        from datetime import datetime
        self._status_refresh.setText(f"Terakhir refresh: {datetime.now().strftime('%H:%M:%S')}")

        # Refresh widgets when navigating to them
        if page_idx == 0:
            self._stack.widget(0).refresh()
        if page_idx == 1:
            self._stack.widget(1).refresh()
        if page_idx == 3:
            self._stack.widget(3).refresh()
        if page_idx == 4:
            self._stack.widget(4).refresh()
