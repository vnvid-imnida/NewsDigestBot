"""Application settings using Pydantic Settings."""

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    # Telegram Bot
    bot_token: str = Field(..., alias="BOT_TOKEN")

    # Database
    database_url: str = Field(
        ...,
        alias="DATABASE_URL",
        description="PostgreSQL connection URL (postgresql+asyncpg://...)"
    )

    # GNews API
    gnews_api_key: str = Field(..., alias="GNEWS_API_KEY")

    # Optional settings
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    timezone: str = Field(default="Europe/Moscow", alias="TIMEZONE")

    # Cache settings
    cache_ttl_minutes: int = Field(default=30, alias="CACHE_TTL_MINUTES")

    # GNews API limits
    gnews_max_results: int = Field(default=10, alias="GNEWS_MAX_RESULTS")
    gnews_language: str = Field(default="ru", alias="GNEWS_LANGUAGE")

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",
    }


# Singleton instance
settings = Settings()
