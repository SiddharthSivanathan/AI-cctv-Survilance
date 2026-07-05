"""Authenticated WebSocket hub for real-time events.

The frontend opens one connection after login, authenticated by the user's
JWT. The org is taken from the (signed, trusted) token claim, and the socket
only ever receives that organization's events — authorization is enforced at
subscription time.
"""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.core.logging import get_logger
from app.core.pubsub import org_channel
from app.core.redis_client import get_redis
from app.core.security.jwt import TokenError, decode_access_token

router = APIRouter()
logger = get_logger("ws")

_HEARTBEAT_SECONDS = 30


@router.websocket("/ws/events")
async def events_ws(websocket: WebSocket, token: str = Query(...)) -> None:
    try:
        payload = decode_access_token(token)
    except TokenError:
        await websocket.close(code=4401)
        return

    organization_id = payload.get("org")
    if not organization_id:
        await websocket.close(code=4403)  # not onboarded / no org
        return

    await websocket.accept()
    pubsub = get_redis().pubsub()
    await pubsub.subscribe(org_channel(organization_id))
    logger.info("ws_connected", organization_id=organization_id)

    try:
        await _pump(websocket, pubsub)
    except WebSocketDisconnect:
        pass
    finally:
        await pubsub.unsubscribe(org_channel(organization_id))
        await pubsub.aclose()
        logger.info("ws_disconnected", organization_id=organization_id)


async def _pump(websocket: WebSocket, pubsub) -> None:
    """Forward org events, send heartbeats, and detect disconnects."""

    async def forward() -> None:
        async for message in pubsub.listen():
            if message.get("type") == "message":
                data = message["data"]
                await websocket.send_text(data if isinstance(data, str) else data.decode())

    async def heartbeat() -> None:
        while True:
            await asyncio.sleep(_HEARTBEAT_SECONDS)
            await websocket.send_json({"type": "ping"})

    async def receive() -> None:
        # Drains client messages (incl. pong); raises WebSocketDisconnect on close.
        while True:
            await websocket.receive_text()

    tasks = [asyncio.create_task(t()) for t in (forward, heartbeat, receive)]
    done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
    for task in pending:
        task.cancel()
    for task in done:
        exc = task.exception()
        if exc and not isinstance(exc, WebSocketDisconnect):
            raise exc
