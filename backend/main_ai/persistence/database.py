from contextlib import contextmanager
import os
from pathlib import Path
import sqlite3
from collections.abc import Iterator

from dotenv import load_dotenv

from .models import SCHEMA_STATEMENTS

load_dotenv()


def get_database_path() -> str:
    return os.getenv("DATABASE_PATH", "data/conversations.sqlite3").strip()


class SQLiteDatabase:
    """Small database boundary that can be replaced by a PostgreSQL backend later."""

    def __init__(self, path: str):
        self.path = path
        self._memory_connection: sqlite3.Connection | None = None

    def _new_connection(self) -> sqlite3.Connection:
        if self.path == ":memory:":
            if self._memory_connection is None:
                self._memory_connection = sqlite3.connect(self.path)
                self._memory_connection.row_factory = sqlite3.Row
                self._memory_connection.execute("PRAGMA foreign_keys = ON")
            return self._memory_connection
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        connection = self._new_connection()
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            if self.path != ":memory:":
                connection.close()


def create_database(database_path: str | None = None) -> SQLiteDatabase:
    path = database_path or get_database_path()
    if path != ":memory:":
        Path(path).expanduser().parent.mkdir(parents=True, exist_ok=True)
    database = SQLiteDatabase(str(Path(path).expanduser()) if path != ":memory:" else path)
    initialize_database(database)
    return database


def initialize_database(database: SQLiteDatabase) -> None:
    with database.connection() as connection:
        connection.executescript(";".join(SCHEMA_STATEMENTS))
