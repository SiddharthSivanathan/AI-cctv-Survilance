"""Configuration for the AI engine (environment-driven)."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# COCO class ids detected by the platform (Phase 1 target classes).
DEFAULT_CLASSES: dict[int, str] = {
    0: "person",
    1: "bicycle",
    2: "car",
    3: "motorcycle",
    5: "bus",
    7: "truck",
    15: "cat",
    16: "dog",
}


class AIEngineSettings(BaseSettings):
    """Typed settings for the inference service."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    environment: str = Field(default="development")
    log_level: str = Field(default="INFO")

    redis_url: str = Field(default="redis://localhost:6379/0")

    # Internal API (camera stream list) + gateway (path provisioning).
    api_internal_url: str = Field(default="http://localhost:8000")
    internal_api_token: str = Field(default="change-me-internal-token")
    gateway_internal_url: str = Field(default="http://localhost:8080")

    # MediaMTX internal RTSP base — the sampler reads from here, not the camera.
    mediamtx_rtsp_url: str = Field(default="rtsp://localhost:8554")

    # Inference. "auto" uses CUDA when available and falls back to CPU;
    # "cpu"/"cuda" force a specific device (cuda still falls back if absent).
    ai_device: str = Field(default="auto")  # "auto" | "cpu" | "cuda"
    model_name: str = Field(default="yolo11s.pt")
    model_dir: str = Field(default="/models")
    model_confidence: float = Field(default=0.35)
    model_imgsz: int = Field(default=640)

    # Sampling / streams
    default_sample_fps: int = Field(default=2)
    frames_stream_maxlen: int = Field(default=10)
    detections_stream_maxlen: int = Field(default=50)
    stream_poll_interval_seconds: int = Field(default=15)

    # Rule engine
    rules_refresh_seconds: int = Field(default=30)

    @property
    def class_ids(self) -> list[int]:
        return list(DEFAULT_CLASSES.keys())


@lru_cache
def get_settings() -> AIEngineSettings:
    return AIEngineSettings()
