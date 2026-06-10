"""Database migration system using Peewee playhouse migrate."""
from __future__ import annotations
import logging
from datetime import datetime

from peewee import OperationalError
from playhouse.migrate import SqliteMigrator, migrate

logger = logging.getLogger(__name__)

SCHEMA_VERSION = 1

_migrations: dict[int, callable] = {}


def register(version: int):
    """Decorator to register a migration function."""
    def wrapper(fn):
        _migrations[version] = fn
        return fn
    return wrapper


def run_migrations():
    """Run pending migrations in order."""
    from src.core.database import database

    migrator = SqliteMigrator(database)
    current = _get_version()

    for ver in sorted(_migrations):
        if ver > current:
            logger.info(f"Menjalankan migrasi v{ver}...")
            try:
                _migrations[ver](migrator)
                _set_version(ver)
                logger.info(f"Migrasi v{ver} berhasil")
            except OperationalError as e:
                if "duplicate column" in str(e).lower():
                    logger.warning(f"Kolom sudah ada di v{ver}, skip")
                    _set_version(ver)
                else:
                    logger.error(f"Migrasi v{ver} gagal: {e}")
                    raise


def _get_version() -> int:
    from src.core.database import database
    try:
        row = database.execute_sql(
            "SELECT version FROM _schema_version ORDER BY version DESC LIMIT 1"
        ).fetchone()
        return row[0] if row else 0
    except OperationalError:
        database.execute_sql(
            "CREATE TABLE IF NOT EXISTS _schema_version "
            "(version INTEGER PRIMARY KEY, applied_at TEXT)"
        )
        return 0


def _set_version(version: int):
    from src.core.database import database
    database.execute_sql(
        "INSERT INTO _schema_version (version, applied_at) VALUES (?, ?)",
        (version, datetime.now().isoformat()),
    )
