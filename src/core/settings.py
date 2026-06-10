import json
import os
import shutil
import datetime
import logging

logger = logging.getLogger(__name__)

DEFAULT_CONFIG = {
    "company_name": "PT Eco Paper Indonesia",
    "db_path": "",  # empty = default data/leadtime.db
}

CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".leadtime")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")

_DEFAULT_DB_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "leadtime.db"
)


def load_config() -> dict:
    if not os.path.exists(CONFIG_PATH):
        return dict(DEFAULT_CONFIG)
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {**DEFAULT_CONFIG, **data}
    except (json.JSONDecodeError, OSError):
        return dict(DEFAULT_CONFIG)


def save_config(config: dict) -> None:
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def get(key: str) -> str:
    return load_config().get(key, DEFAULT_CONFIG.get(key, ""))


def _resolve_db_path() -> str:
    db_path = get("db_path")
    if not db_path:
        return os.path.abspath(_DEFAULT_DB_PATH)
    return os.path.abspath(db_path)


def backup_database() -> str:
    """Backup database ke ~/.leadtime/backups/ dengan timestamp."""
    from src.core.database import database
    backup_dir = os.path.join(CONFIG_DIR, "backups")
    os.makedirs(backup_dir, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = os.path.join(backup_dir, f"leadtime_{timestamp}.db")

    db_path = _resolve_db_path()
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database tidak ditemukan: {db_path}")

    was_open = not database.is_closed()
    if was_open:
        database.close()
    try:
        shutil.copy2(db_path, dest)
        logger.info(f"Backup database berhasil: {dest}")
    finally:
        if was_open:
            database.connect(reuse_if_open=True)
    return dest


def restore_database(backup_path: str) -> bool:
    """Restore database dari file backup."""
    from src.core.database import database
    if not os.path.exists(backup_path):
        logger.error(f"File backup tidak ditemukan: {backup_path}")
        return False

    db_path = _resolve_db_path()
    was_open = not database.is_closed()
    if was_open:
        database.close()
    try:
        shutil.copy2(backup_path, db_path)
        logger.info(f"Restore database berhasil: {backup_path} -> {db_path}")
        return True
    except OSError as e:
        logger.error(f"Gagal restore database: {e}")
        return False
    finally:
        if was_open:
            database.connect(reuse_if_open=True)
