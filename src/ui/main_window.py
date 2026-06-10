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
        self.setWindowTitle("Lead Time App")
        self.resize(1100, 680)
        self._active_btn = None
        self._build_ui()

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
