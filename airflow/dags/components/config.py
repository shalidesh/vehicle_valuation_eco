"""
Configuration module for Airflow DAGs.
Centralizes all configuration constants and environment variables.
"""

import os
from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class DatabaseConfig:
    """Database connection configuration."""
    host: str = os.getenv("APP_DB_HOST", "postgres")
    port: str = os.getenv("APP_DB_PORT", "5432")
    database: str = os.getenv("APP_DB_NAME", "cdb_valuation_db")
    user: str = os.getenv("APP_DB_USER", "cdb")
    password: str = os.getenv("APP_DB_PASSWORD", "cdb123456")


@dataclass(frozen=True)
class ScraperConfig:
    """Web scraper configuration."""
    flaresolverr_url: str = os.getenv('FLARESOLVERR_URL', 'http://flaresolverr:8191/v1')
    chromedriver_path: str = os.getenv('CHROMEDRIVER_PATH', '/usr/bin/chromedriver')
    chrome_bin: str = os.getenv('CHROME_BIN', '/usr/bin/google-chrome')
    request_timeout: int = 70
    max_retries: int = 3
    min_delay: float = 2.5
    max_delay: float = 6.5


@dataclass(frozen=True)
class EmailConfig:
    """Email notification configuration."""
    recipient: str = os.getenv('AIRFLOW_ALERT_EMAIL', 'deshanariyarathna@gmail.com')


@dataclass(frozen=True)
class IkmanConfig:
    """Ikman scraper specific configuration."""
    base_url: str = "https://ikman.lk"
    makes: tuple = (
        'honda', 'toyota', 'nissan', 'suzuki', 'micro', 'mitsubishi',
        'mahindra', 'mazda', 'daihatsu', 'hyundai', 'kia', 'bmw',
        'perodua', 'tata', 'audi', 'isuzu', 'renault', 'ford',
        'volkswagen', 'land rover', 'jaguar', 'mg'
    )
    transmissions: tuple = ('automatic', 'manual', 'tiptronic')
    fuel_types: tuple = ('petrol', 'diesel', 'hybrid', 'electric')
    links_table: str = 'ikman_vehicle_post_links'
    data_table: str = 'ikman_post_data'
    processed_table: str = 'ikman_post_data_preprocced'


@dataclass(frozen=True)
class RiyasewanaConfig:
    """Riyasewana scraper specific configuration."""
    base_url: str = "https://riyasewana.com"
    # makes: tuple = (
    #     'nissan', 'suzuki', 'micro', 'mitsubishi', 'mahindra', 'mazda',
    #     'daihatsu', 'hyundai', 'kia', 'bmw', 'perodua', 'tata'
    # )
    makes: tuple = (
        'nissan', 'suzuki', 'micro'
    )
    vehicle_types: tuple = ('cars', 'vans', 'suvs', 'crew-cabs', 'pickups')
    links_table: str = 'riyasewana_vehicle_post_links'
    data_table: str = 'riyasewana_post_data'
    processed_table: str = 'riyasewana_post_data_preprocced'
    weeks_threshold: int = 3


@dataclass(frozen=True)
class StatisticsConfig:
    """Statistics processing configuration."""
    grouping_cols: tuple = ('make', 'model', 'yom', 'transmission', 'fuel_type')
    target_col: str = 'vehicle_price'
    consolidated_col: str = 'Fixed_value'
    min_records_for_median: int = 20
    iqr_multiplier: float = 1.8
    price_floor: int = 2000000
    ceiling_rules: tuple = (
        (2015, 9999, 30000000),  # yom >= 2015: max 30M
        (2005, 2015, 25000000),  # 2005 <= yom < 2015: max 25M
        (2000, 2005, 20000000),  # 2000 <= yom < 2005: max 20M
    )


# Table schemas
TABLE_SCHEMAS = {
    'ikman_links': [
        "link VARCHAR(255)",
        "page VARCHAR(255)",
        "transmition VARCHAR(255)",
        "fuel_type VARCHAR(255)"
    ],
    'ikman_data': [
        "post_link VARCHAR(255)",
        "posted_title VARCHAR(255)",
        "posted_date VARCHAR(255)",
        "make VARCHAR(255)",
        "model VARCHAR(255)",
        "grade VARCHAR(255)",
        "trim_edition VARCHAR(255)",
        "yom VARCHAR(255)",
        "condition VARCHAR(255)",
        "transmission VARCHAR(255)",
        "body_type VARCHAR(255)",
        "fuel_type VARCHAR(255)",
        "engine_capacity VARCHAR(255)",
        "mileage VARCHAR(255)",
        "vehicle_price VARCHAR(255)"
    ],
    'riyasewana_links': [
        "link VARCHAR(255)",
        "page VARCHAR(255)",
        "date VARCHAR(255)",
        "make VARCHAR(255)"
    ],
    'riyasewana_data': [
        "contact VARCHAR(255)",
        "posted_date VARCHAR(255)",
        "price VARCHAR(255)",
        "make VARCHAR(255)",
        "model VARCHAR(255)",
        "yom VARCHAR(255)",
        "mileage VARCHAR(255)",
        "transmission VARCHAR(255)",
        "fuel_type VARCHAR(255)",
        "options VARCHAR(255)",
        "engine_capacity VARCHAR(255)"
    ],
    'master_vehicle': [
        "make VARCHAR(255)",
        "posted_date VARCHAR(255)",
        "scrape_date VARCHAR(255)",
        "model VARCHAR(255)",
        "yom VARCHAR(255)",
        "mileage VARCHAR(255)",
        "transmission VARCHAR(255)",
        "fuel_type VARCHAR(255)",
        "engine_capacity VARCHAR(255)",
        "vehicle_price VARCHAR(255)"
    ],
    'summary_statistics': [
        "make VARCHAR(255)",
        "model VARCHAR(255)",
        "yom VARCHAR(255)",
        "transmission VARCHAR(255)",
        "fuel_type VARCHAR(255)",
        "average_price FLOAT"
    ]
}


# Singleton instances
db_config = DatabaseConfig()
scraper_config = ScraperConfig()
email_config = EmailConfig()
ikman_config = IkmanConfig()
riyasewana_config = RiyasewanaConfig()
stats_config = StatisticsConfig()
