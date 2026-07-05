"""Unit test for the WebSocket message envelope."""

from app.core.pubsub import build_message, org_channel


def test_org_channel() -> None:
    assert org_channel("abc") == "events:abc"


def test_build_message_shape() -> None:
    msg = build_message(
        type="alert.created",
        organization_id="org-1",
        timestamp="2026-07-05T00:00:00+00:00",
        camera_id="cam-1",
        store_id="store-1",
        severity="high",
        title="Queue threshold exceeded",
        message="6 detected.",
        metadata={"eventType": "queue_threshold_exceeded"},
    )
    assert msg["type"] == "alert.created"
    assert msg["organizationId"] == "org-1"
    assert msg["cameraId"] == "cam-1"
    assert msg["storeId"] == "store-1"
    assert msg["severity"] == "high"
    assert msg["metadata"]["eventType"] == "queue_threshold_exceeded"
