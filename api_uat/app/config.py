"""
Application configuration using Pydantic settings.
All sensitive values are loaded from environment variables.
"""
from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # Application
    app_name: str = "CDB Vehicle Valuation API"
    app_version: str = "2.0.0"
    debug: bool = False

    # Database Configuration
    database_url: str
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_pool_timeout: int = 30
    db_pool_recycle: int = 3600

    # Security
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Authentication
    auth_username: str = "cdb"
    auth_password: str ="cdb123456" # Should be loaded from environment
    fixed_access_token: Optional[str] = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyIjoiY2RiIn0.ohLUJ7PZpd7uYR9qqolf1MDXmwt5IYUI5cOKkuTySdw"  # Fixed token that never expires

    # CORS
    cors_origins: str = "http://localhost:3000"

    # Logging
    log_level: str = "INFO"
    log_dir: str = "logs"
    log_retention_days: int = 30
    log_rotation: str = "midnight"
    log_backup_count: int = 30

    # Rate Limiting
    rate_limit_enabled: bool = True
    rate_limit_per_minute: int = 100

    # Server
    host: str = "0.0.0.0"
    port: int = 8443
    workers: int = 4

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",")]


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    Uses LRU cache to ensure single instance (singleton pattern).
    """
    return Settings()


# Export settings instance for easy import
settings = get_settings()
