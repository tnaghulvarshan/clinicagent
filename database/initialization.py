"""
Database initialization routines for Hospital AI Agent.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional, Union

from database.connection import create_connection, get_db_path
from database.models import SCHEMA_SQL

logger = logging.getLogger(__name__)


def init_db(db_path: Optional[Union[str, Path]] = None) -> Path:
    """
    Initializes the SQLite database with all required tables, constraints, and indexes.
    Idempotent: safe to run multiple times.
    """
    target_path = get_db_path(db_path)
    logger.info("Initializing database at %s", target_path)

    conn = create_connection(target_path)
    try:
        with conn:
            conn.executescript(SCHEMA_SQL)
        logger.info("Database schema initialized successfully.")
    finally:
        conn.close()

    return target_path
