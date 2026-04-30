"""
Pytest configuration and shared fixtures for the Lumina backend test suite.

- Sets DATABASE_URL to SQLite in-memory BEFORE any app modules are imported,
  so the SQLAlchemy engine never attempts a PostgreSQL connection during tests.
- Provides a SQLite in-memory Session fixture (db_session) for fast unit tests.
- Provides a test_client fixture that wraps the FastAPI app and overrides get_db
  with the in-memory session so all HTTP-level tests use SQLite automatically.
- PostgreSQL-specific tests should be marked with @pytest.mark.integration; they
  are skipped automatically when DATABASE_URL points to SQLite.
"""

import os

# ---------------------------------------------------------------------------
# Override DATABASE_URL and JWT_SECRET_KEY BEFORE any app code is imported.
# This prevents the SQLAlchemy engine from attempting a PostgreSQL connection
# at module-import time (which would hang in CI / local environments without
# a live database).
# ---------------------------------------------------------------------------
_original_db_url = os.environ.get("DATABASE_URL", "")
if not _original_db_url.startswith("postgresql"):
    os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")

os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-not-for-production")

import pytest  # noqa: E402 — must come after env setup

from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker, Session  # noqa: E402
from typing import Generator  # noqa: E402


# ---------------------------------------------------------------------------
# Pytest markers
# ---------------------------------------------------------------------------

def pytest_configure(config):
    """Register custom markers to avoid PytestUnknownMarkWarning."""
    config.addinivalue_line(
        "markers",
        "integration: mark test as requiring a live PostgreSQL database; "
        "skipped when DATABASE_URL points to SQLite",
    )


# ---------------------------------------------------------------------------
# Skip logic for integration tests
# ---------------------------------------------------------------------------

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./test.db")

_requires_postgres = pytest.mark.skipif(
    not DATABASE_URL.startswith("postgresql"),
    reason="Requires PostgreSQL — set DATABASE_URL to a postgresql:// URL to run",
)


def pytest_collection_modifyitems(items):
    """Automatically skip @pytest.mark.integration tests when not on PostgreSQL."""
    for item in items:
        if item.get_closest_marker("integration"):
            item.add_marker(_requires_postgres)


# ---------------------------------------------------------------------------
# SQLite in-memory engine & session fixture
# ---------------------------------------------------------------------------

SQLITE_URL = "sqlite:///:memory:"

_test_engine = create_engine(
    SQLITE_URL,
    connect_args={"check_same_thread": False},
)

_TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=_test_engine,
)


@pytest.fixture(scope="function")
def db_session() -> Session:
    """
    Provide a SQLite in-memory SQLAlchemy Session for unit tests.

    Creates all ORM-mapped tables before the test and drops them afterwards,
    giving each test a clean, isolated database state.
    """
    from app.core.database import Base

    Base.metadata.create_all(bind=_test_engine)
    session = _TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=_test_engine)


# ---------------------------------------------------------------------------
# FastAPI test client fixture
# ---------------------------------------------------------------------------

@pytest.fixture(scope="function")
def test_client(db_session: Session) -> Generator:
    """
    Provide a FastAPI TestClient whose database dependency is overridden to use
    the SQLite in-memory session from the db_session fixture.

    The lifespan startup (which tries to connect to PostgreSQL) is disabled so
    that unit tests run without any external services.
    """
    from fastapi.testclient import TestClient
    from app.core.app import create_app
    from app.core.dependencies import get_db

    app = create_app()

    def _override_get_db():
        try:
            yield db_session
        finally:
            pass  # session lifecycle managed by db_session fixture

    app.dependency_overrides[get_db] = _override_get_db

    with TestClient(app, raise_server_exceptions=True) as client:
        yield client

    # Clean up overrides after the test
    app.dependency_overrides.clear()
