"""Smoke tests for the AI engine skeleton (no ML deps, no Redis required)."""

from src import __version__
from src.config import get_settings
from src.main import check_redis


def test_version() -> None:
    assert __version__ == "0.1.0"


def test_settings_load() -> None:
    settings = get_settings()
    assert settings.ai_default_fps >= 1
    assert settings.ai_device in {"cpu", "cuda"}


def test_check_redis_handles_unreachable() -> None:
    # A bogus URL must return False, not raise.
    assert check_redis("redis://127.0.0.1:6390/0") is False
