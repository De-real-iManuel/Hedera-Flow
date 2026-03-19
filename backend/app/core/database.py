"""
Database Connection Pool
Manages PostgreSQL connections using SQLAlchemy with connection pooling
"""
from sqlalchemy import create_engine, event, pool, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from typing import Generator
import logging

import os
from config import settings

# Configure logging
logger = logging.getLogger(__name__)

# Create SQLAlchemy Base for models
Base = declarative_base()


def get_database_url() -> str:
    """Get database URL, checking all possible sources."""
    # Priority: Railway DATABASE_URL env var > settings.database_url
    url = os.getenv('DATABASE_URL') or settings.database_url
    if not url:
        raise ValueError("DATABASE_URL is not configured. Set it in Railway environment variables.")
    # Railway sometimes provides postgres:// but SQLAlchemy needs postgresql://
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url


def create_database_engine():
    """Create SQLAlchemy engine with connection pooling."""
    db_url = get_database_url()

    pool_size = int(getattr(settings, 'db_pool_size', 5))
    max_overflow = int(getattr(settings, 'db_max_overflow', 10))
    pool_timeout = int(getattr(settings, 'db_pool_timeout', 30))

    engine = create_engine(
        db_url,
        poolclass=QueuePool,
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_timeout=pool_timeout,
        pool_recycle=3600,
        pool_pre_ping=True,
        echo=settings.debug,
        future=True,
    )

    logger.info(f"Database engine created (pool_size={pool_size}, max_overflow={max_overflow})")
    return engine


# Create global engine instance
engine = create_database_engine()

# Create SessionLocal class for database sessions
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    future=True,
)


def get_db() -> Generator[Session, None, None]:
    """
    Database session dependency for FastAPI
    
    Usage in FastAPI endpoints:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            items = db.query(Item).all()
            return items
    
    Yields:
        SQLAlchemy Session instance
        
    Note:
        Session is automatically closed after request completes,
        even if an exception occurs
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize database
    Creates all tables defined in models
    
    Note:
        In production, use Alembic migrations instead of this function
        This is primarily for development and testing
    """
    logger.info("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")


def close_db():
    """
    Close database connections
    Should be called on application shutdown
    """
    logger.info("Closing database connection pool...")
    engine.dispose()
    logger.info("Database connection pool closed")


def get_db_stats():
    """
    Get database connection pool statistics
    
    Returns:
        Dictionary with pool statistics
    """
    pool_obj = engine.pool
    return {
        "pool_size": pool_obj.size(),
        "checked_in": pool_obj.checkedin(),
        "checked_out": pool_obj.checkedout(),
        "overflow": pool_obj.overflow(),
        "total_connections": pool_obj.size() + pool_obj.overflow(),
    }


# Health check function
def check_db_connection() -> bool:
    """
    Check if database connection is healthy
    
    Returns:
        True if connection is successful, False otherwise
    """
    try:
        # Try to execute a simple query
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False
