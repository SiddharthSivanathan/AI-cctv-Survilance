"""Configuration for the Celery worker (environment-driven)."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class WorkerSettings(BaseSettings):
    """Typed settings for the background worker."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    environment: str = Field(default="development")
    log_level: str = Field(default="INFO")

    celery_broker_url: str = Field(default="redis://localhost:6379/1")
    celery_result_backend: str = Field(default="redis://localhost:6379/2")

    # Internal API trigger (camera health sweep etc.)
    api_internal_url: str = Field(default="http://localhost:8000")
    internal_api_token: str = Field(default="change-me-internal-token")
    camera_health_interval_seconds: int = Field(default=60)

    # SMTP (email delivery). If unset, emails are logged instead of sent.
    smtp_host: str | None = Field(default=None)
    smtp_port: int = Field(default=587)
    smtp_user: str | None = Field(default=None)
    smtp_password: str | None = Field(default=None)
    smtp_use_tls: bool = Field(default=True)
    email_from: str = Field(default="no-reply@visionops.ai")


@lru_cache
def get_settings() -> WorkerSettings:
    return WorkerSettings()
