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
    frontend_url: str = Field(default="http://localhost:3000")

    # Security
    secret_key: str = Field(default="change-me-in-production")
    jwt_algorithm: str = Field(default="RS256")
    access_token_expire_minutes: int = Field(default=15)
    refresh_token_expire_days: int = Field(default=30)
    # RS256 keys: provide inline PEM or a filesystem path. In non-production,
    # an ephemeral keypair is generated if neither is set (see core.security.jwt).
    jwt_private_key: str | None = Field(default=None)
    jwt_public_key: str | None = Field(default=None)
    jwt_private_key_path: str | None = Field(default=None)
    jwt_public_key_path: str | None = Field(default=None)

    # Email verification / password reset
    email_verification_expire_hours: int = Field(default=24)
    password_reset_expire_hours: int = Field(default=2)
    email_from: str = Field(default="no-reply@visionops.ai")

    # Auth rate limits (requests per window, for slowapi)
    auth_rate_limit: str = Field(default="10/minute")

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://visionops:visionops_dev_password@localhost:5432/visionops"
    )

    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0")

    # Object storage (S3 / MinIO)
    s3_endpoint: str = Field(default="http://localhost:9000")
    s3_access_key: str = Field(default="visionops")
    s3_secret_key: str = Field(default="visionops_dev_password")
    s3_bucket: str = Field(default="visionops-media")
    s3_region: str = Field(default="us-east-1")
    # Public base URL for objects (defaults to endpoint). For MinIO dev this is
    # the endpoint; in production this is typically a CDN/bucket public URL.
    s3_public_url: str | None = Field(default=None)

    @property
    def s3_public_base(self) -> str:
        return (self.s3_public_url or self.s3_endpoint).rstrip("/")

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
