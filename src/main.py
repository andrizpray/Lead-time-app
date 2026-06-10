import sys

from PySide6.QtWidgets import QApplication

from src.core.database import init_db, close_db
from src.ui.main_window import MainWindow


def main():
    init_db()
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    window = MainWindow()
    window.show()

    exit_code = app.exec()
    close_db()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
