"""Database connection and initialization — SQLite with WAL mode."""
import os
import logging
from peewee import SqliteDatabase, OperationalError

logger = logging.getLogger(__name__)

DB_PATH = os.environ.get(
    "LEADTIME_DB_PATH",
    os.path.join(os.path.dirname(__file__), "..", "..", "data", "leadtime.db"),
)

database = SqliteDatabase(None)


def init_db(db_path: str | None = None):
    """Initialize database connection and create tables if needed.

    Parameters
    ----------
    db_path : str or None
        Custom database path. Defaults to DB_PATH env var or data/leadtime.db.
    """
    path = db_path or DB_PATH
    db_dir = os.path.dirname(os.path.abspath(path))
    try:
        os.makedirs(db_dir, exist_ok=True)
    except OSError as e:
        logger.critical(f"Gagal membuat direktori database {db_dir}: {e}")
        raise RuntimeError(f"Tidak dapat membuat direktori database: {e}") from e

    try:
        database.init(
            path,
            pragmas={
                "journal_mode": "wal",
                "foreign_keys": 1,
                "cache_size": -64000,
                "synchronous": "normal",
                "busy_timeout": 5000,
            },
        )
        logger.info(f"Database terhubung: {DB_PATH} (WAL mode)")
    except OperationalError as e:
        logger.critical(f"Gagal inisialisasi database {DB_PATH}: {e}")
        raise RuntimeError(f"Tidak dapat terhubung ke database: {e}") from e

    _create_tables()


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
    finally:
        if not database.is_closed():
            database.close()


def close_db():
    """Close database connection gracefully."""
    try:
        if not database.is_closed():
            database.close()
            logger.debug("Database connection closed")
    except Exception as e:
        logger.warning(f"Error saat menutup database: {e}")
