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

from config import settings

# Configure logging
logger = logging.getLogger(__name__)

# Create SQLAlchemy Base for models
Base = declarative_base()


def create_database_engine():
    """
    Create SQLAlchemy engine with connection pooling
    
    Connection Pool Configuration:
    - pool_size: Number of connections to maintain in the pool (default: 20)
    - max_overflow: Additional connections that can be created beyond pool_size (default: 10)
    - pool_timeout: Seconds to wait before giving up on getting a connection (default: 30)
    - pool_recycle: Recycle connections after this many seconds (prevents stale connections)
    - pool_pre_ping: Test connections before using them (ensures connection is alive)
    
    Returns:
        SQLAlchemy Engine instance
    """
    # Get pool settings from environment or use defaults
    pool_size = int(getattr(settings, 'db_pool_size', 20))
    max_overflow = int(getattr(settings, 'db_max_overflow', 10))
    pool_timeout = int(getattr(settings, 'db_pool_timeout', 30))
    
    # Create engine with connection pooling
    engine = create_engine(
        settings.database_url,
        poolclass=QueuePool,
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_timeout=pool_timeout,
        pool_recycle=3600,  # Recycle connections after 1 hour
        pool_pre_ping=True,  # Test connections before using
        echo=settings.debug,  # Log SQL queries in debug mode
        future=True,  # Use SQLAlchemy 2.0 style
    )
    
    # Log pool configuration
    logger.info(f"Database engine created with connection pool:")
    logger.info(f"  - Pool size: {pool_size}")
    logger.info(f"  - Max overflow: {max_overflow}")
    logger.info(f"  - Pool timeout: {pool_timeout}s")
    logger.info(f"  - Pool recycle: 3600s")
    logger.info(f"  - Pre-ping enabled: True")
    
    # Add event listeners for connection lifecycle
    @event.listens_for(engine, "connect")
    def receive_connect(dbapi_conn, connection_record):
        """Event listener for new connections"""
        logger.debug("New database connection established")
    
    @event.listens_for(engine, "checkout")
    def receive_checkout(dbapi_conn, connection_record, connection_proxy):
        """Event listener for connection checkout from pool"""
        logger.debug("Connection checked out from pool")
    
    @event.listens_for(engine, "checkin")
    def receive_checkin(dbapi_conn, connection_record):
        """Event listener for connection return to pool"""
        logger.debug("Connection returned to pool")
    
    return engine


# Create global engine instance
engine = create_database_engine()

# Create SessionLocal class for database sessions
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    future=True,  # Use SQLAlchemy 2.0 style
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
