"""
Components package for Vehicle Valuation Airflow DAGs.

This package contains reusable modules for:
- Configuration management (config.py)
- Logging infrastructure (logging_config.py)
- Database utilities (utils.py)
- Web scraping - link extraction (post_links_extraction.py)
- Web scraping - data extraction (post_data_extraction.py)
- Data preprocessing and statistics (data_preprocces.py)
"""

from components.config import (
    db_config,
    scraper_config,
    email_config,
    ikman_config,
    riyasewana_config,
    stats_config,
)

from components.logging_config import get_logger, TaskLogger

from components.utils import (
    check_table,
    read_table,
    create_table,
    populate_table,
    bulk_insert,
    success_email,
    failure_email,
)

__all__ = [
    # Config
    "db_config",
    "scraper_config",
    "email_config",
    "ikman_config",
    "riyasewana_config",
    "stats_config",
    # Logging
    "get_logger",
    "TaskLogger",
    # Utils
    "check_table",
    "read_table",
    "create_table",
    "populate_table",
    "bulk_insert",
    "success_email",
    "failure_email",
]
