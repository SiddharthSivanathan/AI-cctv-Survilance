"""WebSocket authentication tests (rejection paths — no Redis required)."""

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.core.security.jwt import create_access_token
from app.main import app


def test_ws_rejects_missing_token() -> None:
    client = TestClient(app)
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/ws/events?token="):
            pass


def test_ws_rejects_invalid_token() -> None:
    client = TestClient(app)
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/ws/events?token=not-a-jwt"):
            pass


def test_ws_rejects_token_without_org() -> None:
    # A valid token for a user who hasn't onboarded (no org claim) is refused.
    token = create_access_token("user-123")
    client = TestClient(app)
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect(f"/ws/events?token={token}"):
            pass
