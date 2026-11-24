"""Database session and engine management optimized for Cloud PostgreSQL (Render, Neon, Supabase)."""

import logging
import time
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker
from app.core.config import settings
from app.db.base import Base

logger = logging.getLogger("app.database")

configured_url = settings.get_normalized_database_url()


def _build_engine(url: str):
    """Instantiate a SQLAlchemy engine with dialect-specific connection pooling."""
    if url.startswith("sqlite"):
        return create_engine(
            url,
            connect_args={"check_same_thread": False},
        )

    # Cloud PostgreSQL with psycopg v3
    return create_engine(
        url,
        connect_args={"connect_timeout": settings.DB_CONNECT_TIMEOUT},
        pool_pre_ping=True,       # Auto-reconnect on dropped idle cloud connections
        pool_size=5,              # Conservative pool size for cloud free-tier limits
        max_overflow=10,
        pool_recycle=1800,        # Recycle connections after 30 minutes
        pool_timeout=30,
    )


def _initialize_database():
    """Attempt connecting to configured database (PostgreSQL), with cloud retries and local fallback."""
    target_url = configured_url
    engine_instance = _build_engine(target_url)

    if not target_url.startswith("sqlite"):
        max_retries = settings.DB_MAX_RETRIES
        connected = False

        for attempt in range(1, max_retries + 1):
            try:
                with engine_instance.connect() as conn:
                    conn.execute(text("SELECT 1"))
                logger.info(
                    "Connected successfully to Cloud PostgreSQL: %s",
                    engine_instance.url.render_as_string(hide_password=True),
                )
                connected = True
                break
            except Exception as err:
                if attempt < max_retries:
                    logger.warning(
                        "Cloud PostgreSQL connection attempt %d/%d failed: %s. Retrying in %ds...",
                        attempt,
                        max_retries,
                        err,
                        settings.DB_RETRY_DELAY,
                    )
                    time.sleep(settings.DB_RETRY_DELAY)
                else:
                    if settings.DB_FALLBACK_TO_SQLITE:
                        fallback_url = "sqlite:///./todo.db"
                        logger.warning(
                            "Cloud PostgreSQL unreachable at '%s' after %d attempts. "
                            "Falling back to local SQLite (%s) for offline local development. "
                            "In production on Render, set DB_FALLBACK_TO_SQLITE=false.",
                            engine_instance.url.render_as_string(hide_password=True),
                            max_retries,
                            fallback_url,
                        )
                        target_url = fallback_url
                        engine_instance = _build_engine(target_url)
                    else:
                        logger.critical(
                            "Failed to connect to Cloud PostgreSQL at '%s': %s",
                            engine_instance.url.render_as_string(hide_password=True),
                            err,
                        )
                        raise

    # Initialize tables
    Base.metadata.create_all(bind=engine_instance)
    return engine_instance


# Primary engine and session factory
engine = _initialize_database()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Ensure database tables are created."""
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a SQLAlchemy session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
