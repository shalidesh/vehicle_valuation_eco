"""
Structured logging configuration with automatic log cleanup.
Logs are rotated daily and automatically deleted after 30 days.
"""
import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from logging.handlers import TimedRotatingFileHandler
from apscheduler.schedulers.background import BackgroundScheduler
from app.config import settings


def setup_logging() -> logging.Logger:
    """
    Configure structured logging with file and console handlers.
    Returns configured logger instance.
    """
    # Create logs directory if it doesn't exist
    log_dir = Path(settings.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    # Create logger
    logger = logging.getLogger("api_uat")
    logger.setLevel(getattr(logging, settings.log_level.upper()))

    # Remove existing handlers to avoid duplicates
    logger.handlers = []

    # Create formatters
    detailed_formatter = logging.Formatter(
        fmt="[%(asctime)s] %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    console_formatter = logging.Formatter(
        fmt="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%H:%M:%S"
    )

    # File handler with daily rotation
    log_file = log_dir / f"api_uat_{datetime.now().strftime('%Y-%m-%d')}.log"
    file_handler = TimedRotatingFileHandler(
        filename=log_file,
        when=settings.log_rotation,
        interval=1,
        backupCount=settings.log_backup_count,
        encoding="utf-8",
        utc=True
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)

    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


def cleanup_old_logs(log_dir: str, retention_days: int = 30):
    """
    Delete log files older than the specified number of days.

    Args:
        log_dir: Directory containing log files
        retention_days: Number of days to retain logs (default: 30)
    """
    try:
        log_path = Path(log_dir)
        if not log_path.exists():
            return

        cutoff_date = datetime.now() - timedelta(days=retention_days)
        deleted_count = 0

        # Find and delete old log files
        for log_file in log_path.glob("*.log*"):
            # Get file modification time
            file_mtime = datetime.fromtimestamp(log_file.stat().st_mtime)

            if file_mtime < cutoff_date:
                try:
                    log_file.unlink()
                    deleted_count += 1
                    logger.info(f"Deleted old log file: {log_file.name}")
                except Exception as e:
                    logger.error(f"Failed to delete log file {log_file.name}: {e}")

        if deleted_count > 0:
            logger.info(f"Log cleanup completed: deleted {deleted_count} old log file(s)")
        else:
            logger.debug("Log cleanup completed: no old files to delete")

    except Exception as e:
        logger.error(f"Error during log cleanup: {e}")


def start_log_cleanup_scheduler():
    """
    Start background scheduler to automatically delete old logs.
    Runs daily at 2 AM.
    """
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        cleanup_old_logs,
        trigger='cron',
        hour=2,
        minute=0,
        args=[settings.log_dir, settings.log_retention_days],
        id='log_cleanup',
        name='Clean up old log files',
        replace_existing=True
    )
    scheduler.start()
    logger.info(f"Log cleanup scheduler started (retention: {settings.log_retention_days} days)")
    return scheduler


# Initialize logger
logger = setup_logging()


def sanitize_sensitive_data(data: dict) -> dict:
    """
    Sanitize sensitive data before logging.
    Masks passwords, tokens, and other sensitive fields.

    Args:
        data: Dictionary potentially containing sensitive data

    Returns:
        Dictionary with sensitive fields masked
    """
    sensitive_fields = {'password', 'token', 'secret', 'api_key', 'auth'}
    sanitized = data.copy()

    for key in sanitized:
        if any(field in key.lower() for field in sensitive_fields):
            sanitized[key] = "***REDACTED***"

    return sanitized


# Export logger and utilities
__all__ = [
    'logger',
    'setup_logging',
    'cleanup_old_logs',
    'start_log_cleanup_scheduler',
    'sanitize_sensitive_data'
]
