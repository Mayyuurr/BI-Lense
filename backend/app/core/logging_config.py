"""Logging Configuration Module.

Provides structured and clean logging across the application.
"""

import logging
import sys
from app.core.config import settings


def setup_logging() -> logging.Logger:
    """Configures and returns the root logger for the application."""
    log_format = "[%(asctime)s] [%(levelname)s] [%(name)s:%(lineno)d] - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    logging.basicConfig(
        level=log_level,
        format=log_format,
        datefmt=date_format,
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    # Mute noisy third-party loggers if needed
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    logger = logging.getLogger("bi_lense")
    logger.setLevel(log_level)
    return logger


logger = setup_logging()
