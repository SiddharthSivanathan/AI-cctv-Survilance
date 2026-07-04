# ADR 0007 — Rule Engine & Event Service (V1)

- **Status:** Accepted
- **Date:** 2026-07-04
- **Phase:** 8 (Rule Engine)

## Context
Detections must become operational intelligence. Product direction: the rule
engine runs **inside the AI worker** as a clean module, keeps **in-memory**
temporal state, and never touches the database; the **Event Service (API)** is
the sole writer of business events + alerts.

## Decisions
1. **Rule engine = a module in `apps/ai-engine`** (`src/rules/`), invoked by the
   DetectionWorker after detect+track. Pure and deterministic given
   `(detections, rules, zones, now)` — fully unit-tested. Designed behind a clean
   interface so it can be extracted into its own service in V2 without touching
   the detection pipeline.
2. **In-memory, per-camera state** (dwell timers, occupancy, open events,
   cooldowns) — ephemeral, reconstructed from live detections, reset on restart.
   Redis-backed HA is a V2 note.
3. **Zones** are polygons in 640×640 sampled-frame space (same as detections);
   membership uses the person's foot point (bbox bottom-center) via ray-casting.
4. **OPEN → RESOLVED lifecycle.** Each rule emits on start and on resolve; the
   engine suppresses duplicates with in-memory **cooldowns**. V1 rule types:
   queue_threshold, occupancy_limit, loitering (per track), unattended_billing_counter.
5. **Event Service (API) is the sole DB writer.** It dedupes (one open event per
   `event_key`), manages open/resolved persistence (`started_at`/`ended_at`/
   `duration_seconds`), and creates/resolves **alerts**. Business events carry
   `organization_id`/`store_id` (from the rules-config) so the internal endpoint
   persists under the correct RLS tenant context without a cross-tenant lookup.
6. **Config delivery.** The engine fetches per-camera rules + zones from a cached
   internal API endpoint (`GET /internal/rules-config`), refreshed periodically.
   It posts events to `POST /internal/events`.
7. **No raw detections persisted** — only business events + alerts (all RLS).

## Deferrals
Real-time WebSocket push and richer analytics → Phase 9; notification delivery
(email/SMS/etc.) → Phase 10. Zone entry/exit and camera_frozen/black-screen
rules are straightforward future additions on the same interface.
