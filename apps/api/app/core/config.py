"""Application configuration (12-factor, environment-driven).

All settings are validated at startup by Pydantic. Nothing is hardcoded;
values come from the environment / .env file.
"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # General
    environment: str = Field(default="development")
    log_level: str = Field(default="INFO")

    # API
    api_v1_prefix: str = Field(default="/api/v1")
    project_name: str = Field(default="VisionOps AI")
    cors_origins: str = Field(default="http://localhost:3000")

    # Security
    secret_key: str = Field(default="change-me-in-production")
    jwt_algorithm: str = Field(default="RS256")
    access_token_expire_minutes: int = Field(default=15)
    refresh_token_expire_days: int = Field(default=30)

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://visionops:visionops_dev_password@localhost:5432/visionops"
    )

    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0")

    @property
    def cors_origins_list(self) -> list[str]:
        """CORS origins as a list."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance (single source of truth)."""
    return Settings()
