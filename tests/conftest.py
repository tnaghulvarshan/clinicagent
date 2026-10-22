"""
Pytest fixtures for Hospital AI Agent system.
Creates isolated temporary databases for test cases to prevent test interference.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Generator
import pytest

from database.initialization import init_db
from database.seed_data import seed_database
from services.appointment_service import AppointmentService
from services.faq_service import FAQService
from services.handoff_service import HandoffService


@pytest.fixture
def temp_db_path() -> Generator[Path, None, None]:
    """Provides a fresh, isolated temporary SQLite database for tests."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_file = Path(tmp_dir) / "test_hospital.db"
        init_db(db_file)
        seed_database(db_file, days_ahead=3)
        yield db_file


@pytest.fixture
def appointment_service(temp_db_path: Path) -> AppointmentService:
    """Returns AppointmentService wired to the temporary test database."""
    return AppointmentService(db_path=temp_db_path)


@pytest.fixture
def faq_service(temp_db_path: Path) -> FAQService:
    """Returns FAQService wired to the temporary test database."""
    return FAQService(db_path=temp_db_path)


@pytest.fixture
def handoff_service(temp_db_path: Path) -> HandoffService:
    """Returns HandoffService wired to the temporary test database."""
    return HandoffService(db_path=temp_db_path)
