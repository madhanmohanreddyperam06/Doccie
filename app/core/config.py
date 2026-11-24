"""Application configuration settings supporting Render deployment and Cloud PostgreSQL."""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Application settings loaded from environment variables."""

    # Project Information
    PROJECT_NAME: str = "Autonomous AI Document Agent"
    VERSION: str = "1.1.0"
    API_PREFIX: str = ""

    # Deployment Environment Detection (Render sets the RENDER environment variable automatically)
    IS_RENDER: bool = os.getenv("RENDER") is not None

    # Database Configuration
    # Defaults to PostgreSQL with psycopg v3 driver
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://postgres:postgres@localhost:5432/todo_db",
    )

    # In Render production, fallback to SQLite is disabled to prevent ephemeral data loss
    # In local development, fallback is enabled so offline local PostgreSQL does not block work
    DB_FALLBACK_TO_SQLITE: bool = os.getenv(
        "DB_FALLBACK_TO_SQLITE",
        "false" if os.getenv("RENDER") is not None else "true",
    ).lower() in ("true", "1", "yes")

    # Connect timeout in seconds (fast 2s locally to avoid blocking test suites, 10s on Render cloud)
    DB_CONNECT_TIMEOUT: int = int(
        os.getenv("DB_CONNECT_TIMEOUT", "10" if os.getenv("RENDER") is not None else "2")
    )

    # Retries for Cloud PostgreSQL (retry 5 times on Render cloud boot; 1 attempt locally)
    DB_MAX_RETRIES: int = int(
        os.getenv("DB_MAX_RETRIES", "5" if os.getenv("RENDER") is not None else "1")
    )
    DB_RETRY_DELAY: int = int(
        os.getenv("DB_RETRY_DELAY", "3" if os.getenv("RENDER") is not None else "1")
    )

    # JWT Authentication Configuration
    SECRET_KEY: str = os.getenv(
        "SECRET_KEY", "7d4b9b9a67e24694b912f7193240e34a6c8e3128d8b94f9ea93e4d7589d311ef"
    )
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440")
    )  # 24 hours

    # Server Configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # Generated Files
    GENERATED_DIR: Path = Path(os.getenv("GENERATED_DIR", "generated"))

    @classmethod
    def get_normalized_database_url(cls, raw_url: str | None = None) -> str:
        """Normalize database URL for SQLAlchemy 2.0 with psycopg v3.
        
        Handles Render's 'postgres://' and 'postgresql://' prefixes and maintains query parameters (such as sslmode).
        """
        url = (raw_url or cls.DATABASE_URL).strip()
        if url.startswith("postgres://"):
            return url.replace("postgres://", "postgresql+psycopg://", 1)
        if url.startswith("postgresql://") and not url.startswith("postgresql+"):
            return url.replace("postgresql://", "postgresql+psycopg://", 1)
        return url


settings = Settings()
