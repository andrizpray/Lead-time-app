"""Lead Time Management System — Entry Point."""
import sys, os, logging
from datetime import datetime
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

# ── Logging setup ──────────────────────────────────────────────────────
LOG_DIR = os.path.join(os.path.expanduser("~"), ".leadtime", "logs")
os.makedirs(LOG_DIR, exist_ok=True)
log_file = os.path.join(LOG_DIR, f"leadtime_{datetime.now().strftime('%Y%m')}.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(log_file, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("leadtime")

# ── Global exception handler ───────────────────────────────────────────
def global_excepthook(exc_type, exc_value, exc_traceback):
    logger.critical("Unhandled exception", exc_info=(exc_type, exc_value, exc_traceback))
    import traceback
    msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    try:
        from src.core.database import close_db
        close_db()
    except Exception:
        pass
    app = QApplication.instance()
    if app:
        QMessageBox.critical(None, "Error Kritis",
            f"Terjadi error yang tidak terduga:\n\n{exc_value}\n\nDetail telah di-log ke {log_file}")

sys.excepthook = global_excepthook

# ── Main ───────────────────────────────────────────────────────────────
from src.core.database import init_db, close_db
from src.core.settings import CONFIG_DIR
from src.ui.main_window import MainWindow

def main():
    logger.info("Aplikasi dimulai")
    init_db()
    app = QApplication(sys.argv)
    app.setApplicationName("Lead Time Management")
    app.setOrganizationName("PT Eco Paper Indonesia")

    # Set app icon
    icon_path = os.path.join(os.path.dirname(__file__), "..", "assets", "icon.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    window = MainWindow()
    window.show()

    exit_code = app.exec()
    close_db()
    logger.info(f"Aplikasi ditutup (exit code {exit_code})")
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
