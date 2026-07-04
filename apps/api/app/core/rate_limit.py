"""Redis-backed fixed-window rate limiting.

A dependency factory that limits requests per client IP per scope. Backed by
Redis so limits are shared across API replicas. Fails **open** if Redis is
unavailable — availability of auth is prioritized over strict limiting, and
the error is logged.
"""

from __future__ import annotations

from fastapi import Request
from redis.exceptions import RedisError

from app.core.exceptions import RateLimitedError
from app.core.logging import get_logger
from app.core.redis_client import get_redis

logger = get_logger("rate_limit")


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def rate_limit(scope: str, *, limit: int, window_seconds: int):
    """Return a dependency enforcing `limit` requests per `window_seconds`."""

    async def _dependency(request: Request) -> None:
        key = f"ratelimit:{scope}:{_client_ip(request)}"
        try:
            redis = get_redis()
            count = await redis.incr(key)
            if count == 1:
                await redis.expire(key, window_seconds)
            if count > limit:
                raise RateLimitedError("Too many requests. Please try again shortly.")
        except RedisError as exc:  # fail open
            logger.warning("rate_limit_unavailable", scope=scope, error=str(exc))

    return _dependency
