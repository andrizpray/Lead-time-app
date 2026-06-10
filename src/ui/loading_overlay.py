"""Loading overlay widget — ditampilkan saat operasi berat."""
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QProgressBar
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QPainter


class LoadingOverlay(QWidget):
    """Overlay semi-transparan dengan indeterminate progress bar."""

    def __init__(self, parent=None, message="Memproses..."):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._label = QLabel(message)
        self._label.setStyleSheet(
            "color: #e94560; font-size: 14px; font-weight: bold; background: transparent;"
        )
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._progress = QProgressBar()
        self._progress.setRange(0, 0)  # indeterminate
        self._progress.setFixedWidth(200)
        self._progress.setFixedHeight(6)

        layout.addWidget(self._label)
        layout.addSpacing(10)
        layout.addWidget(self._progress, alignment=Qt.AlignmentFlag.AlignCenter)

        self.hide()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 160))
        super().paintEvent(event)

    def show_with_message(self, message: str):
        """Show overlay with custom message."""
        self._label.setText(message)
        self.setGeometry(self.parent().rect())
        self.raise_()
        self.show()
        QTimer.singleShot(100, self.raise_)

    def hide_overlay(self):
        """Hide overlay."""
        self.hide()
