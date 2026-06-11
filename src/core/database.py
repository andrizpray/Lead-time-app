"""Database connection and initialization — SQLite with WAL mode."""
import os
import logging
from peewee import SqliteDatabase, OperationalError

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Path database persisten — disimpan di ~/.leadtime/data/leadtime.db
# Ini penting untuk PyInstaller one-file mode: saat exe dijalankan,
# __file__ menunjuk ke folder temp (_MEIxxxxxx) yang dihapus setiap kali
# aplikasi ditutup, sehingga database harus di lokasi permanen.
# ---------------------------------------------------------------------------

_PERSISTENT_DB_DIR  = os.path.join(os.path.expanduser("~"), ".leadtime", "data")
_PERSISTENT_DB_PATH = os.path.join(_PERSISTENT_DB_DIR, "leadtime.db")


def _get_db_path() -> str:
    """Return absolute path ke file database yang persisten.

    Prioritas:
    1. Env var LEADTIME_DB_PATH  (testing / custom deployment)
    2. Config user db_path       (set dari UI Pengaturan)
    3. ~/.leadtime/data/leadtime.db  ← default persisten
    """
    # Prioritas 1: environment variable
    env_path = os.environ.get("LEADTIME_DB_PATH", "").strip()
    if env_path:
        return env_path

    # Prioritas 2: config file (baca langsung JSON, hindari circular import)
    try:
        import json
        config_path = os.path.join(os.path.expanduser("~"), ".leadtime", "config.json")
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            custom = cfg.get("db_path", "").strip()
            if custom:
                return os.path.abspath(custom)
    except Exception:
        pass

    # Prioritas 3: default persisten
    return os.path.abspath(_PERSISTENT_DB_PATH)


database = SqliteDatabase(None)


def init_db():
    """Initialize database connection and create tables if needed."""
    db_path = _get_db_path()
    db_dir  = os.path.dirname(db_path)

    try:
        os.makedirs(db_dir, exist_ok=True)
    except OSError as e:
        logger.critical(f"Gagal membuat direktori database {db_dir}: {e}")
        raise RuntimeError(f"Tidak dapat membuat direktori database: {e}") from e

    # ── Migrasi otomatis dari lokasi lama (relative path dalam bundle) ──────
    # Cari kandidat database lama di lokasi yang mungkin dipakai sebelumnya
    _migrate_old_db_if_needed(db_path)

    try:
        database.init(
            db_path,
            pragmas={
                "journal_mode": "wal",
                "foreign_keys": 1,
                "cache_size": -64000,
                "synchronous": "normal",
                "busy_timeout": 5000,
            },
        )
        logger.info(f"Database terhubung: {db_path} (WAL mode)")
    except OperationalError as e:
        logger.critical(f"Gagal inisialisasi database {db_path}: {e}")
        raise RuntimeError(f"Tidak dapat terhubung ke database: {e}") from e

    _create_tables()


def _migrate_old_db_if_needed(target_path: str):
    """Pindahkan database lama ke lokasi persisten jika belum ada di sana."""
    import shutil

    if os.path.exists(target_path):
        # Sudah ada di lokasi baru, tidak perlu migrasi
        return

    # Kandidat lokasi lama yang mungkin dipakai versi sebelumnya
    old_candidates = [
        # Relatif terhadap lokasi source/bundle (dev mode)
        os.path.join(os.path.dirname(__file__), "..", "..", "data", "leadtime.db"),
        # Relatif terhadap folder kerja saat ini
        os.path.join(os.getcwd(), "data", "leadtime.db"),
        # Relatif terhadap exe (untuk PyInstaller onedir mode)
        os.path.join(os.path.dirname(os.path.abspath(
            getattr(__import__("sys"), "executable", __file__)
        )), "data", "leadtime.db"),
    ]

    for old_path in old_candidates:
        old_path = os.path.normpath(os.path.abspath(old_path))
        if os.path.exists(old_path) and os.path.getsize(old_path) > 0:
            try:
                shutil.copy2(old_path, target_path)
                logger.info(f"Database lama dimigrasikan: {old_path} → {target_path}")
                return
            except Exception as exc:
                logger.error(
                    f"GAGAL migrasi database dari {old_path} ke {target_path}: {exc}. "
                    f"Data lama mungkin tidak tersedia. Periksa permission folder atau salin manual."
                )
                # Catat ke file fallback agar user tahu
                try:
                    err_log = os.path.join(os.path.dirname(target_path), "migration_error.log")
                    with open(err_log, "a", encoding="utf-8") as f:
                        from datetime import datetime as _dt
                        f.write(f"[{_dt.now().isoformat()}] Gagal migrasi dari {old_path}: {exc}\n")
                except Exception:
                    pass

    logger.info(f"Database baru akan dibuat di: {target_path}")


def _create_tables():
    """Create all tables if they do not exist."""
    from src.core.models import DORecord

    try:
        database.connect(reuse_if_open=True)
        database.create_tables([DORecord], safe=True)
        from src.core.migration import run_migrations
        run_migrations()
        logger.info("Tabel database siap")
    except OperationalError as e:
        logger.error(f"Gagal membuat tabel: {e}")
        raise
    # NOTE: koneksi TIDAK ditutup di sini agar sesi aplikasi tetap terbuka.
    # Peewee akan reuse koneksi yang sudah ada pada setiap query.


def close_db():
    """Close database connection gracefully."""
    try:
        if not database.is_closed():
            database.close()
            logger.debug("Database connection closed")
    except Exception as e:
        logger.warning(f"Error saat menutup database: {e}")
