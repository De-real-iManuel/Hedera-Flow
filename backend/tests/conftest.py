"""
Pytest configuration for using Docker PostgreSQL instead of SQLite
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
from pathlib import Path
import os
from dotenv import load_dotenv

# Load test environment variables
test_env_path = Path(__file__).parent / ".env.test"
if test_env_path.exists():
    load_dotenv(test_env_path)

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import Base

# Use Docker PostgreSQL for testing
TEST_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://hedera_user:hedera_dev_password@localhost:5432/hedera_flow_test"
)

engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test"""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Create test database schema once per test session"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
