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


@lru_cache
def get_settings() -> WorkerSettings:
    return WorkerSettings()
