# ADR 0006 — AI Vision Pipeline (V1)

- **Status:** Accepted
- **Date:** 2026-07-04
- **Phase:** 7 (AI Vision Pipeline)

## Context
V1 needs real-time object detection + tracking feeding operational intelligence.
Product direction is strict: the **AI worker is stateless and database-free** and
**outputs detections only** — the rule engine (Phase 8) turns detections into
business events; **raw detections are never persisted**.

## Decisions
1. **Pipeline:** `Camera → MediaMTX → ffmpeg sampler → Redis (frames) → AI worker
   → Redis (detections) → Rule Engine (Phase 8)`.
2. **Sampler reads from MediaMTX** (internal RTSP, on-demand paths provisioned via
   the gateway), at per-camera `sample_fps` (default 2), resized to 640×640. One
   camera connection is shared between live viewers and the sampler. JPEG frames
   go to a single capped Redis stream (`frames`, MAXLEN).
3. **Detector = YOLOv11s** (Ultralytics; PyTorch dev, ONNX prod path; GPU→CPU
   fallback). Loaded lazily so importing the code never pulls torch. Raw-result →
   `Detection` parsing is a pure function (unit-tested). Classes limited to the V1
   operational set (person primary + car/truck/motorcycle/bicycle/chair/bags).
4. **Tracking:** a deterministic IOU tracker ships as the unit-testable default
   behind a simple interface; **ByteTrack** (via `supervision`) is the intended
   production tracker and drops in without changing the worker.
5. **Statelessness:** the worker consumes frames via a Redis **consumer group**
   (horizontally scalable) and publishes detection payloads to a capped
   `detections` stream + a short-TTL `detections:latest:{camera}` key. **It never
   touches Postgres.** Nothing durable is written in Phase 7.
6. **Control-plane coupling stays in the API.** The AI engine gets the enabled
   camera list + decrypted sources from an internal, token-guarded API endpoint
   (`GET /internal/cameras/streams`) — no DB/crypto in the worker.
7. **Visible proof:** `GET /cameras/{id}/detections/latest` reads the ephemeral
   Redis key (tenant-checked); the live player overlays boxes + person count.

## Deferrals
Business events, `camera_events`/`alerts`, duplicate-prevention, cooldowns, zone
config, and all rule types (queue/occupancy/loitering/unattended/zone) →
**Phase 8** (Rule Engine + Event Service). Notifications → Phase 10.

## Verification note
Real inference (YOLO/torch/ONNX) and ffmpeg sampling require the ML deps and
ideally a GPU; they cannot run in the authoring environment. ML sits behind an
interface; non-ML logic (parsing, tracking, payloads) is unit-tested. End-to-end
detection must be confirmed on a real deployment.
