"""
Logging configuration for the Dividend Portfolio Dashboard API.

Provides environment-aware structured logging with rotation and formatting.
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from app.config import get_settings


def setup_logging() -> logging.Logger:
    """
    Configure application logging with rotation and environment-specific levels.

    Development: DEBUG to console
    Production: INFO to console + file with rotation

    Returns:
        Configured logger instance
    """
    settings = get_settings()

    # Create logger
    logger = logging.getLogger("dividends_app")

    # Set level based on environment
    log_level = logging.DEBUG if settings.environment == "development" else logging.INFO
    logger.setLevel(log_level)

    # Prevent duplicate handlers if called multiple times
    if logger.handlers:
        return logger

    # Console handler (always enabled)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handlers with rotation (all environments)
    log_dir = Path(__file__).parent.parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)

    file_formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Main log file - captures INFO and above
    file_handler = logging.handlers.RotatingFileHandler(
        filename=log_dir / "app.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # Error log file - captures WARNING and above for quick error review
    error_handler = logging.handlers.RotatingFileHandler(
        filename=log_dir / "errors.log",
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=3,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.WARNING)
    error_handler.setFormatter(file_formatter)
    logger.addHandler(error_handler)

    return logger


def get_logger() -> logging.Logger:
    """
    Get the application logger instance.

    Returns:
        The dividends_app logger instance
    """
    return logging.getLogger("dividends_app")
