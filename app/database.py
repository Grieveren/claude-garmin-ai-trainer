"""
Database connection and session management for Garmin AI Training System.

This module provides:
- SQLAlchemy engine configuration
- Session factory for database transactions
- Base class for all models
- Context manager for safe transaction handling
"""

from contextlib import contextmanager
from typing import Generator
import os
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy.pool import StaticPool

# Base class for all models
Base = declarative_base()

# Database URL from environment or default to SQLite
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./data/training_data.db"
)

# Engine configuration with optimizations
engine_kwargs = {
    "echo": os.getenv("SQL_ECHO", "false").lower() == "true",  # SQL logging
    "pool_pre_ping": True,  # Verify connections before using
    "pool_recycle": 3600,  # Recycle connections after 1 hour
}

# SQLite-specific optimizations
if DATABASE_URL.startswith("sqlite"):
    engine_kwargs.update({
        "connect_args": {"check_same_thread": False},
        "poolclass": StaticPool,  # Use static pool for SQLite
    })


# Create engine
engine = create_engine(DATABASE_URL, **engine_kwargs)


# SQLite performance optimizations
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """Enable SQLite optimizations on connection."""
    if "sqlite" in str(engine.url):
        cursor = dbapi_conn.cursor()
        # Enable foreign key constraints
        cursor.execute("PRAGMA foreign_keys=ON")
        # Use Write-Ahead Logging for better concurrency
        cursor.execute("PRAGMA journal_mode=WAL")
        # Synchronous mode for better performance (still safe with WAL)
        cursor.execute("PRAGMA synchronous=NORMAL")
        # Increase cache size to 64MB
        cursor.execute("PRAGMA cache_size=-64000")
        # Use memory for temp storage
        cursor.execute("PRAGMA temp_store=MEMORY")
        cursor.close()


# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,  # Keep objects usable after commit
)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function for FastAPI to get database sessions.

    Yields:
        Session: SQLAlchemy database session

    Example:
        @app.get("/metrics")
        def get_metrics(db: Session = Depends(get_db)):
            return db.query(DailyMetrics).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """
    Context manager for database sessions in scripts and background tasks.

    Yields:
        Session: SQLAlchemy database session

    Example:
        with get_db_context() as db:
            metrics = db.query(DailyMetrics).filter_by(date=today).first()
            db.commit()
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db() -> None:
    """
    Initialize database by creating all tables.

    This should be called on application startup or via migration tools.
    For production, use Alembic migrations instead.
    """
    # Import all models to ensure they're registered with Base
    from app.models import database_models  # noqa: F401

    Base.metadata.create_all(bind=engine)


def drop_db() -> None:
    """
    Drop all tables from the database.

    WARNING: This will delete all data. Use with caution!
    Only intended for development/testing.
    """
    Base.metadata.drop_all(bind=engine)


def reset_db() -> None:
    """
    Reset database by dropping and recreating all tables.

    WARNING: This will delete all data. Use with caution!
    Only intended for development/testing.
    """
    drop_db()
    init_db()
