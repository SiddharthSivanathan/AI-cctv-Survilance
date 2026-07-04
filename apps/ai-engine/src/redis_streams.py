"""Redis Streams helpers.

Redis is the ephemeral transport between the sampler, the AI worker, and the
rule engine (Phase 8). Streams are capped (MAXLEN) — nothing here is durable.

A single shared `frames` stream (with a camera_id field) lets multiple AI
workers share one consumer group and scale horizontally.
"""

from __future__ import annotations

import redis

from src.config import get_settings

FRAMES_STREAM = "frames"
DETECTIONS_STREAM = "detections"
CONSUMER_GROUP = "ai-workers"


def latest_detection_key(camera_id: str) -> str:
    """Key holding the most recent detection payload for a camera (for the UI)."""
    return f"detections:latest:{camera_id}"


def get_client() -> redis.Redis:
    """Binary-safe Redis client (frames are raw JPEG bytes)."""
    return redis.from_url(get_settings().redis_url)
