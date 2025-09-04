"""
Core configuration settings for the SubForge Dashboard Backend
"""

import os
from pathlib import Path
from typing import List, Optional, Union

from pydantic import validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Application
    APP_NAME: str = "SubForge Dashboard API"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = "Backend API for SubForge monitoring dashboard"
    DEBUG: bool = False

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    RELOAD: bool = False

    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:3001"]
    ALLOWED_METHODS: List[str] = ["*"]
    ALLOWED_HEADERS: List[str] = ["*"]
    ALLOW_CREDENTIALS: bool = True

    # Database
    DATABASE_URL: Optional[str] = None
    DATABASE_ECHO: bool = False

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_EXPIRE: int = 300  # 5 minutes

    # WebSocket
    WEBSOCKET_PATH: str = "/ws"

    # Authentication (for future use)
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = "HS256"

    # SubForge specific paths
    SUBFORGE_ROOT: Path = (
        Path.cwd().parent.parent
    )  # Go up from backend/subforge-dashboard to Claude-subagents
    CLAUDE_DIR: Path = Path.cwd().parent.parent / ".claude"
    SUBFORGE_DIR: Path = Path.cwd().parent.parent / ".subforge"
    AGENTS_DIR: Path = Path.cwd().parent.parent / ".claude" / "agents"

    # File watching
    ENABLE_FILE_WATCHER: bool = True
    WATCHER_DEBOUNCE_SECONDS: float = 1.0

    # Metrics and monitoring
    METRICS_UPDATE_INTERVAL: int = 30  # seconds
    MAX_WEBSOCKET_CONNECTIONS: int = 100

    # API Enhancement
    ENABLE_RATE_LIMITING: bool = True
    ENABLE_CACHING: bool = True
    CACHE_TTL_DEFAULT: int = 300  # seconds

    # Background Tasks
    CELERY_BROKER_URL: str = "redis://localhost:6379/2"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/3"
    ENABLE_BACKGROUND_TASKS: bool = True

    # File Upload
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    MAX_FILES_PER_UPLOAD: int = 10
    UPLOAD_DIR: str = "uploads"

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    @validator("DATABASE_URL", pre=True)
    def assemble_db_connection(cls, v: Optional[str]) -> str:
        """Set default database URL if not provided"""
        if v is None:
            # Use SQLite by default for development
            db_path = Path.cwd() / "subforge_dashboard.db"
            return f"sqlite:///{db_path}"
        return v

    @validator("SUBFORGE_ROOT", "CLAUDE_DIR", "SUBFORGE_DIR", "AGENTS_DIR", pre=True)
    def convert_to_path(cls, v: Union[str, Path]) -> Path:
        """Convert string paths to Path objects"""
        if isinstance(v, str):
            return Path(v)
        return v

    def get_database_url(self) -> str:
        """Get the database URL for SQLAlchemy"""
        return self.DATABASE_URL

    def get_async_database_url(self) -> str:
        """Get the async database URL for SQLAlchemy"""
        if self.DATABASE_URL.startswith("postgresql://"):
            return self.DATABASE_URL.replace(
                "postgresql://", "postgresql+asyncpg://", 1
            )
        elif self.DATABASE_URL.startswith("sqlite:///"):
            return self.DATABASE_URL.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
        return self.DATABASE_URL

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Global settings instance
settings = Settings()


# Environment-specific configurations
class DevelopmentConfig(Settings):
    """Development environment configuration"""

    DEBUG: bool = True
    RELOAD: bool = True
    DATABASE_ECHO: bool = True
    LOG_LEVEL: str = "DEBUG"


class ProductionConfig(Settings):
    """Production environment configuration"""

    DEBUG: bool = False
    RELOAD: bool = False
    DATABASE_ECHO: bool = False
    LOG_LEVEL: str = "WARNING"


class TestingConfig(Settings):
    """Testing environment configuration"""

    DEBUG: bool = True
    DATABASE_URL: str = "sqlite:///./test_subforge_dashboard.db"
    REDIS_URL: str = "redis://localhost:6379/1"  # Use different Redis DB for tests


def get_settings() -> Settings:
    """Get settings based on environment"""
    env = os.getenv("ENVIRONMENT", "development").lower()

    if env == "production":
        return ProductionConfig()
    elif env == "testing":
        return TestingConfig()
    else:
        return DevelopmentConfig()