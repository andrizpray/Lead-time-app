import json
import os
import shutil
import datetime

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
    backup_dir = os.path.join(CONFIG_DIR, "backups")
    os.makedirs(backup_dir, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = os.path.join(backup_dir, f"leadtime_{timestamp}.db")
    shutil.copy2(_resolve_db_path(), dest)
    return dest


def restore_database(backup_path: str) -> bool:
    try:
        shutil.copy2(backup_path, _resolve_db_path())
        return True
    except OSError:
        return False
