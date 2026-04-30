"""
Root-level conftest.py for the Lumina backend.

This file is loaded by pytest BEFORE any test modules or sub-conftest files are
imported.  Its sole responsibility is to set environment variables to safe test
values so that module-level code in config.py and database.py never attempts a
live PostgreSQL connection during the test run.

All fixtures and markers are defined in tests/conftest.py.
"""

import os

# Set test-safe environment variables before any application code is imported.
# os.environ takes precedence over .env file values loaded by pydantic-settings.
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-not-for-production")
os.environ.setdefault("ENVIRONMENT", "test")
