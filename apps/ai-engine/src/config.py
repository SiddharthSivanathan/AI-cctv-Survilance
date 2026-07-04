"""Configuration for the AI engine (environment-driven)."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AIEngineSettings(BaseSettings):
    """Typed settings for the inference service."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    environment: str = Field(default="development")
    log_level: str = Field(default="INFO")

    redis_url: str = Field(default="redis://localhost:6379/0")

    # Inference
    ai_device: str = Field(default="cpu")  # "cpu" | "cuda"
    ai_model_dir: str = Field(default="/models")
    ai_default_fps: int = Field(default=2)


@lru_cache
def get_settings() -> AIEngineSettings:
    return AIEngineSettings()
