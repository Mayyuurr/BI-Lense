"""Database Connection and Session Management Module.

Provides SQLAlchemy engine, session factories, and dependency injection
helpers for FastAPI request lifecycles with graceful fallback.
"""

from typing import Generator, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.core.logging_config import logger

# Declarative Base for all ORM models
Base = declarative_base()

# SQLAlchemy Engine Configuration
# Uses connect_args for timeout handling so failed connections fail fast
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_pre_ping=True,
    connect_args={"connect_timeout": settings.DB_TIMEOUT_SECONDS},
)

# Session factory bound to engine
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that provides a database session.

    Yields a SQLAlchemy Session and ensures proper closure.
    """
    db = SessionLocal()
    try:
        yield db
    except SQLAlchemyError as exc:
        logger.error(f"Database error during request lifecycle: {exc}")
        db.rollback()
        raise
    finally:
        db.close()


_db_online_status: Optional[bool] = None


def check_db_connection(force_recheck: bool = False) -> bool:
    """Checks whether the PostgreSQL database is reachable.

    Returns:
        bool: True if connection succeeded, False otherwise.
    """
    global _db_online_status
    if _db_online_status is not None and not force_recheck:
        return _db_online_status

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        _db_online_status = True
        return True
    except Exception as exc:
        _db_online_status = False
        logger.info(f"Database currently offline/unreachable: {exc}. Running in fault-tolerant mode.")
        return False


def is_database_online() -> bool:
    """Returns whether database is currently reachable without re-triggering slow timeouts."""
    global _db_online_status
    if _db_online_status is None:
        return check_db_connection()
    return _db_online_status
