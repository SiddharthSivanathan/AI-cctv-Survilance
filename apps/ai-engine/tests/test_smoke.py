"""Smoke tests for the AI engine skeleton (no ML deps, no Redis required)."""

from src import __version__
from src.config import get_settings


def test_version() -> None:
    assert __version__ == "0.1.0"


def test_settings_load() -> None:
    settings = get_settings()
    assert settings.default_sample_fps >= 1
    assert settings.ai_device in {"cpu", "cuda"}
    assert 0 in settings.class_ids  # person is always included
