"""Logging configuration for the code search CLI."""

import sys
from pathlib import Path

from loguru import logger

def setup_logger():
    """Configure and return the logger instance."""
    # Remove default handler
    logger.remove()

    # Add console handler for warnings and errors
    logger.add(
        sys.stderr,
        format="<level>{level}</level> | {message}",
        level="WARNING",
        colorize=True,
    )

    # Add file handler for all levels
    log_file = Path("logs/search_audit.log")
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    logger.add(
        log_file,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
        level="INFO",
        rotation="10 MB",
        retention="1 month",
    )

    return logger
