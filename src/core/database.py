import os
from peewee import SqliteDatabase

DB_PATH = os.environ.get(
    "LEADTIME_DB_PATH",
    os.path.join(os.path.dirname(__file__), "..", "..", "data", "leadtime.db"),
)

database = SqliteDatabase(
    None,
    pragmas={
        "journal_mode": "wal",
        "foreign_keys": 1,
        "cache_size": -32 * 1024,
    },
)


def init_db(path: str = DB_PATH) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    database.init(path)
    database.connect(reuse_if_open=True)
    _create_tables()


def _create_tables() -> None:
    from src.core.models import DORecord

    database.create_tables([DORecord], safe=True)


def close_db() -> None:
    if not database.is_closed():
        database.close()
