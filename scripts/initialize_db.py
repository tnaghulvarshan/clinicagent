"""
Command-line script to initialize the SQLite database and seed synthetic demo data.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

# Ensure project root is in sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from database.initialization import init_db
from database.seed_data import seed_database
from config.settings import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("initialize_db")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Initialize database and seed demo hospital data."
    )
    parser.add_argument(
        "--db",
        type=str,
        default=str(settings.database_path),
        help="Path to SQLite database file (default from settings).",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Number of days of slots to generate ahead (default 7).",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete existing database file before initializing.",
    )

    args = parser.parse_args()
    db_path = Path(args.db)

    if args.reset and db_path.exists():
        logger.warning("Resetting database: deleting %s", db_path)
        db_path.unlink()

    logger.info("Initializing schema at %s...", db_path)
    init_db(db_path)

    logger.info("Seeding demo data (doctors, schedules, slots, FAQs)...")
    seed_database(db_path, days_ahead=args.days)

    logger.info("Database initialization and seeding complete!")


if __name__ == "__main__":
    main()
