"""
Module for logger setup
"""

import logging
import sys
from pathlib import Path
import config


def setup_logger() -> logging.Logger:
    """
    Sets up a logger for writing to console and file

    Returns:
        Configured logger
    """
    # Create main logger
    logger = logging.getLogger('deduplicator')
    logger.setLevel(logging.INFO)

    # Clear existing handlers
    logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Create file handler (overwrite mode)
    log_file = Path(config.LOG_FILE)
    file_handler = logging.FileHandler(log_file, mode='w', encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


def get_logger() -> logging.Logger:
    """
    Gets the configured logger

    Returns:
        Logger for use in other modules
    """
    return logging.getLogger('deduplicator')
