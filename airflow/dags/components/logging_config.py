"""
Logging configuration module for Airflow DAGs.
Provides consistent logging across all pipeline components.
"""

import logging
import sys
from typing import Optional


def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Get a configured logger instance for the specified module.

    Args:
        name: The name of the logger (typically __name__ of the calling module)
        level: The logging level (default: INFO)

    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger(name)

    if not logger.handlers:
        logger.setLevel(level)

        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)

        formatter = logging.Formatter(
            fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        logger.propagate = False

    return logger


class TaskLogger:
    """
    Context manager for task-level logging with automatic start/end logging.

    Usage:
        with TaskLogger(logger, "processing_data") as task_log:
            task_log.info("Processing record 1")
            # ... do work
    """

    def __init__(self, logger: logging.Logger, task_name: str):
        self.logger = logger
        self.task_name = task_name

    def __enter__(self):
        self.logger.info(f"Starting task: {self.task_name}")
        return self.logger

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.logger.error(
                f"Task '{self.task_name}' failed with error: {exc_val}",
                exc_info=True
            )
        else:
            self.logger.info(f"Completed task: {self.task_name}")
        return False
