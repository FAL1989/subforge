"""
Logging configuration for SubForge Dashboard Backend
"""

import logging
import logging.config
import sys
from pathlib import Path

from ..core.config import settings


def setup_logging() -> None:
    """
    Setup logging configuration for the application
    """
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Determine log level
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    # Configure logging based on format preference
    if settings.LOG_FORMAT.lower() == "json":
        setup_json_logging(log_level)
    else:
        setup_standard_logging(log_level)


def setup_standard_logging(log_level: int) -> None:
    """
    Setup standard text-based logging
    """
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "detailed": {
                "format": "%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(funcName)s(): %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": log_level,
                "formatter": "standard",
                "stream": sys.stdout,
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": log_level,
                "formatter": "detailed",
                "filename": "logs/subforge_dashboard.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
            },
            "error_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": logging.ERROR,
                "formatter": "detailed",
                "filename": "logs/subforge_dashboard_errors.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
            },
        },
        "loggers": {
            "": {  # Root logger
                "handlers": ["console", "file"],
                "level": log_level,
                "propagate": False,
            },
            "subforge_dashboard": {
                "handlers": ["console", "file", "error_file"],
                "level": log_level,
                "propagate": False,
            },
            "uvicorn": {
                "handlers": ["console"],
                "level": logging.INFO,
                "propagate": False,
            },
            "uvicorn.error": {
                "handlers": ["console", "error_file"],
                "level": logging.INFO,
                "propagate": False,
            },
            "uvicorn.access": {
                "handlers": ["console"],
                "level": logging.INFO,
                "propagate": False,
            },
            "fastapi": {
                "handlers": ["console", "file"],
                "level": logging.INFO,
                "propagate": False,
            },
            "sqlalchemy.engine": {
                "handlers": ["file"],
                "level": logging.INFO if settings.DATABASE_ECHO else logging.WARNING,
                "propagate": False,
            },
        },
    }

    logging.config.dictConfig(logging_config)


def setup_json_logging(log_level: int) -> None:
    """
    Setup JSON-formatted logging
    """
    try:
        from pythonjsonlogger import jsonlogger
    except ImportError:
        # Fall back to standard logging if pythonjsonlogger is not available
        setup_standard_logging(log_level)
        return

    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "()": jsonlogger.JsonFormatter,
                "format": "%(asctime)s %(name)s %(levelname)s %(message)s %(pathname)s %(lineno)d %(funcName)s",
            },
            "standard": {
                "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": log_level,
                "formatter": "standard",
                "stream": sys.stdout,
            },
            "json_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": log_level,
                "formatter": "json",
                "filename": "logs/subforge_dashboard.json",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
            },
            "error_json_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": logging.ERROR,
                "formatter": "json",
                "filename": "logs/subforge_dashboard_errors.json",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
            },
        },
        "loggers": {
            "": {  # Root logger
                "handlers": ["console", "json_file"],
                "level": log_level,
                "propagate": False,
            },
            "subforge_dashboard": {
                "handlers": ["console", "json_file", "error_json_file"],
                "level": log_level,
                "propagate": False,
            },
            "uvicorn": {
                "handlers": ["console"],
                "level": logging.INFO,
                "propagate": False,
            },
            "uvicorn.error": {
                "handlers": ["console", "error_json_file"],
                "level": logging.INFO,
                "propagate": False,
            },
            "fastapi": {
                "handlers": ["console", "json_file"],
                "level": logging.INFO,
                "propagate": False,
            },
            "sqlalchemy.engine": {
                "handlers": ["json_file"],
                "level": logging.INFO if settings.DATABASE_ECHO else logging.WARNING,
                "propagate": False,
            },
        },
    }

    logging.config.dictConfig(logging_config)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name
    """
    return logging.getLogger(f"subforge_dashboard.{name}")