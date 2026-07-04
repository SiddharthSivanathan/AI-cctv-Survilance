# VisionOps AI — System Architecture (Phase 1)

> AI-powered Video Intelligence SaaS. Turns existing CCTV into operations intelligence.
> Multi-tenant, real-time, GPU-accelerated computer vision + VLM reasoning.

**Status:** Architecture proposal. No application code written yet — awaiting approval per workflow.

---

## 1. Guiding Principles

1. **Separation of the three planes.** Video is not like normal SaaS data. We keep three distinct planes:
   - **Control plane** (FastAPI): tenants, users, cameras, rules, billing — normal request/response SaaS.
   - **Data/streaming plane** (Go/Python media workers): RTSP ingest, decode, frame sampling. High-throughput, GPU-adjacent.
   - **AI plane** (inference workers): detection, tracking, VLM scene understanding. GPU-bound, horizontally scaled.
   These scale independently. A tenant adding 500 cameras must not degrade the login API.

2. **Tenant isolation is a security boundary, not a `WHERE` clause.** Postgres Row-Level Security (RLS) enforced at the DB, with `tenant_id` on every row. App bugs cannot leak across tenants.

3. **Events, not video, are the product.** We do NOT store or ship raw video by default (cost + privacy + liability). We store *events*, *short clips*, and *thumbnails*. Video is ephemeral unless a rule captures it.

4. **Everything async past the edge.** Ingest → detect → track → reason → rule-eval → notify is an event pipeline (Redis Streams / Kafka), not a synchronous call chain.

5. **Privacy & compliance are first-class** (GDPR/CCPA, biometric consent for face recognition). Face recognition is **opt-in, per-tenant, region-gated**, and legally dangerous (BIPA-style laws) — treated as a feature flag with audit + consent records.

---

## 2. High-Level Component Map

```
                          ┌──────────────────────────────┐
   Cameras (RTSP/ONVIF)   │        EDGE / GATEWAY         │
   ───────────────────►   │  Media Gateway (Go)          │
                          │  - RTSP pull / ONVIF discover │
                          │  - H.264/265 decode           │
                          │  - FPS sampling (1–5 fps)     │
                          │  - Frame → JPEG/tensor        │
                          └───────────────┬──────────────┘
                                          │ frames (Redis Stream / gRPC)
                                          ▼
                          ┌──────────────────────────────┐
                          │      AI INFERENCE PLANE        │
                          │  Detector (YOLOv11 + ONNX/TRT) │
                          │  Tracker  (ByteTrack)          │
                          │  VLM      (Qwen2.5-VL / Gemini)│  ← scene understanding, RCA
                          │  Specialized: LPR, OCR, Pose,  │
                          │               Fire/Smoke        │
                          └───────────────┬──────────────┘
                                          │ structured detections
                                          ▼
                          ┌──────────────────────────────┐
                          │       RULE ENGINE (Celery)     │
                          │  - stateful temporal rules     │
                          │  - dwell / absence / threshold │
                          │  → Events → Alerts             │
                          └───────────────┬──────────────┘
                                          │
        ┌──────────────────┬──────────────┼───────────────┬───────────────┐
        ▼                  ▼              ▼               ▼               ▼
   PostgreSQL         TimescaleDB      Redis          Object Store    Notification
   (control plane)    (event TS data)  (cache/stream) (clips/thumbs)  Fanout (Celery)
        │                                                                  │
        └───────────────────────┬──────────────────────────────┐         ▼
                                 ▼                              ▼    Email/SMS/WA/Slack/
                        FastAPI Control API              WebSocket Hub  Teams/Push/Webhook
                        (REST v1 + OpenAPI)              (live alerts)
                                 │
                                 ▼
                        Next.js 15 Frontend (App Router)
                        Dashboard · Live Grid · Alerts · Analytics · Reports · Billing
```

---

## 3. Technology Decisions (with rationale)

| Layer | Choice | Why (and what I'd push back on) |
|---|---|---|
| Control API | **FastAPI + SQLAlchemy 2.0 (async) + Pydantic v2** | Async fits I/O-heavy tenant APIs; Pydantic gives us OpenAPI + validation for free. |
| Media Gateway | **Go** (recommended) or Python+PyAV fallback | RTSP/decode at scale is where Python's GIL hurts. Go handles thousands of concurrent streams cheaply. *If the team is Python-only, we start with PyAV and accept lower density.* |
| Inference | **YOLOv11 → ONNX Runtime / TensorRT**, **ByteTrack** | ONNX for portability, TensorRT for NVIDIA prod throughput. Triton Inference Server for multi-model GPU sharing. |
| Scene reasoning | **Qwen2.5-VL** (self-host) + **Gemini Vision** (managed fallback) | Self-host for cost/privacy at volume; managed for burst + hardest queries. Router picks per query. |
| Relational DB | **PostgreSQL 16 + RLS** | Multi-tenant isolation at the DB. |
| Time-series events | **TimescaleDB** (Postgres extension) | Footfall/heatmap/event streams are time-series; hypertables + continuous aggregates make analytics fast and cheap. Keeps ops surface small (still Postgres). |
| Cache / streams / locks | **Redis** (+ Redis Streams for the pipeline bus) | Start here; graduate the pipeline bus to **Kafka/Redpanda** when >~a few thousand cameras. |
| Background work | **Celery** (rules, reports, notifications, billing jobs) | Mature, good Beat scheduling for reports. |
| Object storage | **S3 / GCS / Azure Blob** (via one storage abstraction) | Clips, thumbnails, report PDFs, model artifacts. |
| Frontend | **Next.js 15 (App Router, RSC) + React 19 + TS + Tailwind + shadcn/ui + Framer Motion + TanStack Query + Zustand** | Exactly your stack. RSC for fast dashboards, Query for server state, Zustand for UI/client state. |
| Live video in browser | **WebRTC** (via MediaMTX/mediasoup) with **HLS/LL-HLS** fallback | WebRTC for low-latency live; HLS for scale/recording playback. |
| Auth | **JWT access (short) + rotating refresh tokens** (httpOnly cookie), Argon2id passwords, TOTP MFA | Refresh rotation + reuse detection. OIDC/SSO (SAML) for enterprise tenants later. |
| Infra | **Docker → Docker Compose (dev) → Kubernetes (prod)**, GPU node pools, Nginx/Ingress | GPU workers on autoscaling node groups; control plane on cheap CPU nodes. |
| Observability | **OpenTelemetry → Prometheus + Grafana + Loki**, Sentry | Pipeline needs per-stage latency/throughput SLOs. |

**Two decisions I'd flag for you now (they shape everything):**
- **(A) Media Gateway language:** Go (recommended, higher camera density) vs. pure-Python (simpler, one language). 
- **(B) Event store:** TimescaleDB (recommended) vs. plain Postgres tables now + migrate later.

---

## 4. Multi-Tenancy Model

- **Shared DB, shared schema, RLS-isolated** (industry standard for SaaS at this stage; cheapest to operate).
- Every tenant-owned table has `organization_id UUID NOT NULL`.
- Postgres RLS policy: `USING (organization_id = current_setting('app.current_org')::uuid)`.
- The API sets `app.current_org` per request from the validated JWT — **defense in depth** on top of query-level scoping.
- Path to enterprise: large tenants can later be promoted to a **dedicated schema or dedicated DB** without app changes (the repository layer abstracts it).

---

## 5. The AI Pipeline (detailed)

```
Camera registered → Gateway pulls RTSP → decode → sample at rule-driven FPS
   → publish frame to stream:{camera_id}
      → Detector consumer: YOLOv11 → boxes+classes (batched on GPU via Triton)
        → Tracker: ByteTrack assigns stable track_ids (dwell/entry/exit)
          → Enrichment (conditional, only when a rule needs it):
              LPR / OCR / Pose / Fire-Smoke / VLM scene caption
            → emit Detection record (structured, to TimescaleDB + rule bus)
              → Rule Engine evaluates stateful temporal rules
                → on match: create Event → Alert → capture clip+thumb to S3
                  → Notification fanout (email/SMS/WA/Slack/Teams/push/webhook)
                    → WebSocket push to live Alert Center
                      → feeds Report aggregation (daily/weekly/monthly)
```

**Optimization levers:** per-camera FPS, region-of-interest masks, model selection per use-case (a warehouse doesn't run LPR), GPU batching across cameras, and "only run expensive VLM when a cheap detector fires."

**Rule Engine design:** rules compile to a small typed AST (no arbitrary code execution from users). Conditions are temporal and stateful — e.g. `ABSENCE(class=employee, zone=billing_counter, for=60s)`, `THRESHOLD(count(class=person, zone=queue) > 8)`, `DWELL(track, zone=restricted, for=120s)`. State lives in Redis keyed by `(camera, zone, track)`. This is what makes "no-code rules" real and safe.

---

## 6. Repository / Monorepo Layout (proposed)

```
visionops-ai/
├── apps/
│   ├── web/                  # Next.js 15 frontend
│   ├── api/                  # FastAPI control plane
│   ├── gateway/              # Media gateway (Go or Python)
│   └── inference/            # AI workers (detector/tracker/vlm)
├── packages/
│   ├── shared-types/         # OpenAPI-generated TS types (single source of truth)
│   └── ui/                   # shared shadcn component library
├── services/
│   ├── rules-engine/         # Celery rule workers
│   ├── notifications/        # notification fanout
│   └── reporting/            # report generation (Celery Beat)
├── infra/
│   ├── docker/               # Dockerfiles + docker-compose.yml
│   ├── k8s/                  # Helm charts / manifests
│   └── terraform/            # cloud infra (optional)
├── db/
│   └── migrations/           # Alembic migrations
├── docs/                     # architecture, ADRs, API docs, runbooks
└── ARCHITECTURE.md
```

---

## 7. Security Baseline (built in from module 1)

- JWT (RS256) access + rotating refresh w/ reuse detection · Argon2id · TOTP MFA
- Postgres RLS tenant isolation · per-request org context
- RBAC: roles (Owner, Admin, Manager, Analyst, Viewer) + granular permissions
- Secrets in vault/KMS (camera RTSP creds **encrypted at rest**, never returned in API)
- Input validation (Pydantic), parameterized queries (no raw SQL from user), rate limiting, CORS allowlist, CSRF for cookie flows, security headers (CSP/HSTS)
- Full audit log (who/what/when/ip) on every mutating action
- Face recognition & LPR: consent records + regional feature-gating + retention policies

---

## 8. Proposed Build Order (each = one reviewable module, then we stop)

Following your workflow, adjusted so each module is independently runnable and testable:

| # | Module | Deliverable |
|---|---|---|
| 0 | **Foundation** | Monorepo, docker-compose (Postgres/Timescale/Redis/MinIO), CI, linting, health checks — a repo that boots. |
| 1 | **Database & migrations** | Full schema (all tables §DB), RLS policies, Alembic migrations, seed data. |
| 2 | **Backend core + Auth** | FastAPI skeleton, DI, repository pattern, JWT/refresh/MFA, RBAC, OpenAPI. Tested. |
| 3 | **Organizations & Users** | Multi-tenant onboarding, invitations, roles, audit logs. |
| 4 | **Stores / Branches / Cameras** | CRUD + encrypted RTSP creds + ONVIF discovery stub. |
| 5 | **Frontend shell** | Next.js app: auth flows, layout, command palette, dark/light, dashboard skeleton wired to real API. |
| 6 | **Media gateway + live streaming** | RTSP ingest, WebRTC/HLS live view in the camera grid. |
| 7 | **AI inference** | YOLOv11+ByteTrack worker, detection events into Timescale. |
| 8 | **Rule engine** | No-code rule builder (UI + AST) + real-time alerts. |
| 9 | **Notifications** | Multi-channel fanout. |
| 10 | **Reports & analytics** | Aggregations, heatmaps, footfall, AI-generated PDF reports. |
| 11 | **Billing & subscriptions** | Stripe, plans, metering, invoices. |
| 12 | **Deployment** | K8s manifests, GPU node pools, observability, runbooks. |

Each module ships with **tests, migrations (if DB), and docs**, then I stop for your approval — exactly as you specified.

---

## 9. Database Tables (to be fully specified in Module 1)

Organizations · Users · Roles · Permissions · RolePermissions · Memberships · Stores · Branches · Cameras · CameraStreams · Zones (ROIs) · Employees · Customers · Detections (Timescale) · Events · Alerts · Rules · RuleConditions · Reports · Notifications · NotificationChannels · AuditLogs · Subscriptions · Plans · Invoices · Payments · ApiKeys · Sessions · Settings · ConsentRecords (privacy).

Every table: `id` (UUID), `organization_id` (where tenant-scoped), `created_at/updated_at`, soft-delete where appropriate, and **explicit indexes** on FKs + hot query paths + time-series partitioning for `Detections`/`Events`.

---

## 10. What I need from you to start Module 0

Two quick calls (§3): **Media Gateway = Go or Python?** and **Event store = TimescaleDB or plain Postgres?** — plus confirmation of the build order above.
