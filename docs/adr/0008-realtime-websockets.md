# ADR 0008 — Real-time delivery via WebSockets (V1)

- **Status:** Accepted
- **Date:** 2026-07-05
- **Phase:** 9 (Dashboard & Analytics — real-time layer)

## Context
Alerts and camera status must reach the dashboard instantly. Product direction:
WebSockets only (no SSE/Kafka/RabbitMQ/push/Slack/Teams/WhatsApp in V1), one
authenticated connection per user, strictly org-scoped, broadcasting only
committed events.

## Decisions
1. **One JWT-authenticated WebSocket per user** (`/ws/events?token=`). The org
   is read from the signed access-token `org` claim — no DB hit — and the socket
   subscribes only to that org's channel, so a user can only ever receive their
   organization's events (authorization at subscription time).
2. **Redis pub/sub is the fan-out.** The Event Service publishes to
   `events:{org_id}`; each WebSocket connection subscribes to its org channel and
   forwards. This decouples producers from connections and lets the API scale to
   multiple replicas.
3. **Broadcast strictly after commit.** The internal `/events` and health-sweep
   endpoints persist + `commit()` first, then publish — so clients only ever
   receive committed events.
4. **Event envelope** is camelCase per spec:
   `{ type, organizationId, cameraId, storeId, severity, title, message,
   timestamp, metadata }`. Types: `alert.created`, `alert.resolved`,
   `camera.offline`, `camera.online`, `camera.reconnected`.
5. **Connection handling:** server heartbeat ping every 30s; client sends keepalive
   and auto-reconnects with backoff, showing "Reconnecting…". A concurrent reader
   task detects disconnects.
6. **Frontend:** a single `RealtimeProvider` in the dashboard shell opens the
   socket, shows toasts (sonner), optionally plays a sound (configurable in
   settings), invalidates the alerts/events/cameras queries, and exposes the
   connection status indicator.
7. **Modular for V2:** the notification path is a clean seam — email/SMS/Slack/
   Teams/WhatsApp channels attach at the Event Service without touching the
   WebSocket hub (Phase 10).

## Deferred (still Phase 9, pending owner decision)
KPI dashboard charts, analytics aggregation endpoints, command palette / global
search, and footfall/occupancy trends (needs an aggregated metrics store).
