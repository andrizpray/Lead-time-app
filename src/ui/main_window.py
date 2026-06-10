from PySide6.QtWidgets import (
    QMainWindow,
    QPushButton,
    QSplitter,
    QStackedWidget,
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
    min-width: 200px;
    max-width: 200px;
}

QPushButton {
    background-color: transparent;
    color: #f1f5f9;
    border: none;
    border-radius: 6px;
    padding: 10px 14px;
    text-align: left;
    font-size: 13px;
}

QPushButton:hover {
    background-color: #334155;
}

QPushButton[active="true"] {
    background-color: #3b82f6;
    color: #ffffff;
    font-weight: bold;
}
"""

_NAV_ITEMS = [
    ("📊 Dashboard", 0),
    ("📋 Data DO", 1),
    ("➕ Input DO", None),   # opens dialog, no page index
    ("📥 Import Excel", 2),
    ("📄 Laporan", 3),
    ("⚙️ Pengaturan", 4),
]


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # ── Industrial dark theme ──────────────────────────────────────────
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #0f1724;
                color: #f1f5f9;
                font-family: "Inter", "Segoe UI", Arial, sans-serif;
                font-size: 12px;
            }
            QStackedWidget, QScrollArea, QAbstractScrollArea {
                background-color: #0f1724;
                border: none;
            }
            QGroupBox {
                color: #f1f5f9;
                border: 1px solid #334155;
                border-radius: 6px;
                margin-top: 14px;
                padding-top: 10px;
                font-size: 12px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 4px;
                color: #059669;
                font-weight: 600;
            }
            QPushButton {
                background-color: #059669;
                color: #ffffff;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 12px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #047857;
            }
            QPushButton:pressed {
                background-color: #065f46;
            }
            QPushButton:disabled {
                background-color: #1e293b;
                color: #475569;
            }
            QLineEdit, QTextEdit, QPlainTextEdit,
            QSpinBox, QDoubleSpinBox, QDateEdit, QTimeEdit, QComboBox {
                background-color: #1e293b;
                color: #f1f5f9;
                border: 1px solid #475569;
                border-radius: 4px;
                padding: 6px 8px;
                font-size: 12px;
            }
            QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus,
            QSpinBox:focus, QDoubleSpinBox:focus,
            QDateEdit:focus, QTimeEdit:focus, QComboBox:focus {
                border: 1px solid #059669;
            }
            QLineEdit:hover, QDateEdit:hover, QTimeEdit:hover,
            QComboBox:hover, QSpinBox:hover, QDoubleSpinBox:hover {
                border-color: #64748b;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox QAbstractItemView {
                background-color: #1e293b;
                color: #f1f5f9;
                border: 1px solid #334155;
                selection-background-color: #059669;
                selection-color: #ffffff;
            }
            QTableWidget, QTableView {
                background-color: #0f1724;
                color: #f1f5f9;
                gridline-color: #334155;
                alternate-background-color: #1e293b;
                selection-background-color: #059669;
                selection-color: #ffffff;
                border: 1px solid #334155;
            }
            QTableWidget::item, QTableView::item {
                padding: 4px 8px;
            }
            QHeaderView::section {
                background-color: #1e293b;
                color: #059669;
                padding: 6px 8px;
                border: none;
                border-right: 1px solid #334155;
                border-bottom: 1px solid #334155;
                font-weight: 600;
                font-size: 12px;
            }
            QLabel {
                color: #f1f5f9;
                background-color: transparent;
            }
            QTabWidget::pane {
                background-color: #0f1724;
                border: 1px solid #334155;
            }
            QTabBar::tab {
                background-color: #1e293b;
                color: #94a3b8;
                padding: 8px 16px;
                border: 1px solid #334155;
                border-bottom: none;
                border-radius: 4px 4px 0 0;
            }
            QTabBar::tab:selected {
                background-color: #0f1724;
                color: #f1f5f9;
                border-top: 2px solid #059669;
            }
            QTabBar::tab:hover {
                background-color: #334155;
                color: #f1f5f9;
            }
            QScrollBar:vertical {
                background-color: #0f1724;
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background-color: #475569;
                border-radius: 5px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #64748b;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0;
            }
            QScrollBar:horizontal {
                background-color: #0f1724;
                height: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:horizontal {
                background-color: #475569;
                border-radius: 5px;
                min-width: 20px;
            }
            QScrollBar::handle:horizontal:hover {
                background-color: #64748b;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0;
            }
            QProgressBar {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 4px;
                text-align: center;
                color: #f1f5f9;
                font-size: 11px;
            }
            QProgressBar::chunk {
                background-color: #059669;
                border-radius: 3px;
            }
            QDialog {
                background-color: #0f1724;
                color: #f1f5f9;
            }
            QMessageBox {
                background-color: #0f1724;
                color: #f1f5f9;
            }
            QToolTip {
                background-color: #1e293b;
                color: #f1f5f9;
                border: 1px solid #059669;
                padding: 6px 8px;
                border-radius: 4px;
                font-size: 11px;
            }
            QSplitter::handle {
                background-color: #334155;
            }
            QStatusBar {
                background-color: #1e293b;
                color: #94a3b8;
                font-size: 11px;
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

        app_title = QLabel("LeadTime")
        app_title.setStyleSheet(
            "color: #f1f5f9; font-size: 16px; font-weight: bold; padding: 4px 8px 16px 8px;"
        )
        sidebar_layout.addWidget(app_title)

        self._nav_buttons: list[QPushButton] = []
        for label, page_idx in _NAV_ITEMS:
            btn = QPushButton(label)
            btn.setProperty("active", False)
            btn.clicked.connect(lambda checked, idx=page_idx, b=btn: self._navigate(idx, b))
            sidebar_layout.addWidget(btn)
            self._nav_buttons.append(btn)

        sidebar_layout.addStretch()

        # --- content area ---
        self._stack = QStackedWidget()
        self._stack.addWidget(DashboardWidget())        # 0
        self._stack.addWidget(DOTableWidget())          # 1
        self._stack.addWidget(ImportWizardWidget())     # 2
        self._stack.addWidget(ReportWidget())           # 3
        self._stack.addWidget(SettingsWidget())             # 4

        splitter.addWidget(sidebar)
        splitter.addWidget(self._stack)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        self.setCentralWidget(splitter)

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

        # Refresh widgets when navigating to them
        if page_idx == 0:
            self._stack.widget(0).refresh()
        if page_idx == 1:
            self._stack.widget(1).refresh()
        if page_idx == 3:
            self._stack.widget(3).refresh()
        if page_idx == 4:
            self._stack.widget(4).refresh()


# ------------------------------------------------------------------
def _placeholder(name: str) -> QWidget:
    w = QWidget()
    layout = QVBoxLayout(w)
    lbl = QLabel("Coming Soon")
    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    layout.addWidget(lbl)
    return w
