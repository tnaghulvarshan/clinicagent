"""
SQLite connection manager with transactions, foreign keys, and WAL mode.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Optional, Union

from config.settings import settings


def get_db_path(custom_path: Optional[Union[str, Path]] = None) -> Path:
    """Return resolved Path to the SQLite database."""
    if custom_path is not None:
        return Path(custom_path)
    return settings.database_path


def create_connection(db_path: Optional[Union[str, Path]] = None) -> sqlite3.Connection:
    """Create a configured SQLite connection with foreign keys and WAL mode."""
    target_path = get_db_path(db_path)
    target_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(
        str(target_path),
        timeout=20.0,
        detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
        check_same_thread=False,
    )
    conn.row_factory = sqlite3.Row

    # Enforce SQLite foreign keys and WAL mode for reliability and concurrency
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    conn.execute("PRAGMA busy_timeout = 5000;")

    return conn


@contextmanager
def get_db_connection(
    db_path: Optional[Union[str, Path]] = None,
) -> Generator[sqlite3.Connection, None, None]:
    """Context manager yielding a SQLite connection, automatically closing it."""
    conn = create_connection(db_path)
    try:
        yield conn
    finally:
        conn.close()


@contextmanager
def transaction(
    conn: sqlite3.Connection,
) -> Generator[sqlite3.Connection, None, None]:
    """
    Context manager for atomic database transactions.
    Rolls back automatically on exception, commits on success.
    """
    try:
        conn.execute("BEGIN IMMEDIATE;")
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
