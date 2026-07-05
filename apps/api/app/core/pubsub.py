"""Redis pub/sub for real-time event broadcasting.

The Event Service publishes committed events to a per-organization channel;
the WebSocket hub subscribes per connection and forwards to the browser. This
keeps broadcasting decoupled and lets the API scale to multiple replicas.
"""

from __future__ import annotations

import json
from typing import Any

from app.core.logging import get_logger
from app.core.redis_client import get_redis

logger = get_logger("pubsub")


def org_channel(organization_id: str) -> str:
    return f"events:{organization_id}"


def build_message(
    *,
    type: str,
    organization_id: str,
    timestamp: str,
    camera_id: str | None = None,
    store_id: str | None = None,
    severity: str | None = None,
    title: str | None = None,
    message: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the camelCase WebSocket event envelope sent to the browser."""
    return {
        "type": type,
        "organizationId": organization_id,
        "cameraId": camera_id,
        "storeId": store_id,
        "severity": severity,
        "title": title,
        "message": message,
        "timestamp": timestamp,
        "metadata": metadata or {},
    }


async def publish(organization_id: str, message: dict[str, Any]) -> None:
    """Publish a single event to an organization's channel."""
    try:
        await get_redis().publish(org_channel(organization_id), json.dumps(message))
    except Exception as exc:  # noqa: BLE001 - broadcasting must never break the request
        logger.warning("publish_failed", error=str(exc))


async def publish_many(messages: list[dict[str, Any]]) -> None:
    for msg in messages:
        await publish(msg["organizationId"], msg)
