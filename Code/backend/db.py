"""Database connection and initialization utilities."""

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Optional, Union

DEFAULT_DB_PATH = os.environ.get(
    "GREENPROOF_DB_PATH",
    str(Path(__file__).resolve().parent / "greenproof.db")
)
SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"


def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Create a new SQLite connection with foreign keys enabled and row factory configured."""
    target_path = db_path if db_path is not None else DEFAULT_DB_PATH
    conn = sqlite3.connect(target_path, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def db_session(db_path: Optional[str] = None) -> Generator[sqlite3.Connection, None, None]:
    """Context manager managing an explicit transaction with commit/rollback."""
    conn = get_connection(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def apply_schema(conn: sqlite3.Connection) -> None:
    """Execute the schema DDL against an open database connection."""
    conn.execute("PRAGMA foreign_keys = ON;")
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        conn.executescript(f.read())


def init_db(target: Optional[Union[str, sqlite3.Connection]] = None) -> None:
    """Execute the schema DDL against a target path or connection."""
    if isinstance(target, sqlite3.Connection):
        apply_schema(target)
    else:
        with db_session(target) as conn:
            apply_schema(conn)
