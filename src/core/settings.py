import json
import os
import shutil
import datetime
import logging

logger = logging.getLogger(__name__)

DEFAULT_CONFIG = {
    "company_name": "PT Eco Paper Indonesia",
    "db_path": "",  # empty = default data/leadtime.db
    "shift_schedules": [
        {
            "tgl_mulai": "2026-01-01",
            "tgl_akhir": None,  # None = berlaku sampai sekarang
            "shift_1_start": "07:00",
            "shift_1_end": "17:59",
            "shift_2_start": "19:00",
            "shift_2_end": "06:59",
        }
    ],
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


def get_shift_for_date(tgl: "datetime.date") -> dict:
    """Return shift schedule yang berlaku untuk tanggal tertentu.

    Mencari schedule dengan tgl_mulai <= tgl <= tgl_akhir.
    tgl_akhir = None berarti "sampai sekarang".
    Return default schedule pertama jika tidak ada yang cocok.
    """
    from datetime import date as _date

    cfg = load_config()
    schedules = cfg.get("shift_schedules", DEFAULT_CONFIG["shift_schedules"])

    if isinstance(tgl, str):
        tgl = _date.fromisoformat(tgl)

    # Sorting: tgl_akhir=None (open-ended) ditaruh terakhir
    def _sort_key(s):
        end = s.get("tgl_akhir")
        if not end or not str(end).strip():
            return (_date.max,)
        return (_date.fromisoformat(str(end)),)

    sorted_sched = sorted(schedules, key=_sort_key)

    for s in sorted_sched:
        start = _date.fromisoformat(s["tgl_mulai"])
        end_str = s.get("tgl_akhir")
        end = _date.fromisoformat(str(end_str)) if end_str and str(end_str).strip() else _date.max
        if start <= tgl <= end:
            return s

    # Fallback ke schedule pertama
    return schedules[0] if schedules else DEFAULT_CONFIG["shift_schedules"][0]



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
