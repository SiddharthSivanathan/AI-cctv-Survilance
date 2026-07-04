# VisionOps AI — Product Requirements Document (PRD)

**Version:** 1.0 · **Status:** Draft for approval · **Owner:** Engineering

---

## 1. Scope
Multi-tenant SaaS for AI-powered video operations intelligence over existing CCTV. This PRD defines *what* v1 does; architecture defines *how* (see [ARCHITECTURE.md](../ARCHITECTURE.md)).

## 2. Personas & Roles (RBAC)
| Role | Description | Key permissions |
|---|---|---|
| **Owner** | Tenant creator / account owner | Everything incl. billing, delete org |
| **Admin** | Org administrator | Users, stores, cameras, rules, settings |
| **Manager** | Store/branch manager | View assigned stores, ack alerts, view reports |
| **Analyst** | Ops/data analyst | Analytics, reports, read-only cameras |
| **Viewer** | Limited viewer | Read-only dashboards & alerts |

Permissions are granular (resource × action) and composed into roles; roles are tenant-scoped.

## 3. Functional Requirements (by phase)

### FR-A Authentication & Tenancy (Phase 3)
- Email/password (Argon2id), email verification, password reset.
- JWT access (15 min) + rotating refresh (httpOnly cookie) with reuse detection.
- TOTP MFA (optional, enforceable per org).
- Multi-tenant orgs with RLS isolation; user belongs to ≥1 org via Membership.
- Session management + revoke; audit log on all auth events.

### FR-B Organizations, Users, Stores, Branches (Phase 4)
- Create/manage organization; invite users by email; assign roles.
- Stores (a physical site) → Branches (sub-areas/departments) hierarchy.
- Org/store/branch settings; audit logging on all mutations.

### FR-C Cameras & RTSP (Phase 5)
- Register cameras: name, location, RTSP URL, credentials (**encrypted at rest**), branch.
- ONVIF discovery on a local network segment (agent/gateway assisted).
- Camera health/status (online/offline/error), last-seen heartbeats.
- Define **Zones** (polygon ROIs) per camera for rules (queue area, restricted zone, counter).

### FR-D Live Streaming (Phase 6)
- Low-latency live view (WebRTC) in a camera grid; HLS fallback.
- Multi-camera grid (1/4/9/16), fullscreen, per-camera status overlay.

### FR-E AI Vision Pipeline (Phase 7)
- Continuous ingest at configurable FPS per camera.
- Detection (YOLOv11) + tracking (ByteTrack) → structured detections in TimescaleDB.
- Conditional enrichment: fire/smoke, PPE (helmet/vest), pose/fall, LPR, OCR, VLM scene caption.
- Detection classes cover the full list in the brief; each camera enables only needed models.

### FR-F Rule Engine (Phase 8)
- No-code builder: `IF <condition(s)> THEN <action(s)>`.
- Condition types: threshold (count in zone), absence (no class in zone for N sec), dwell/loitering, presence, entry/exit, class-detected (fire/smoke/violence).
- Actions: create alert (priority), notify (channel + recipients), capture clip, webhook.
- Rules are tenant/store/camera-scoped; compiled to a safe typed AST (no code exec).

### FR-G Alerts & Notifications (Phase 10)
- Real-time Alert Center (WebSocket) with ack/resolve/assign, priority, filters.
- Channels: Email, SMS, WhatsApp, Slack, MS Teams, Push, Webhook (per-rule routing + quiet hours + dedup).

### FR-H Dashboard & Analytics (Phase 9)
- KPI dashboard: alerts, camera health, footfall, queue trends.
- Heatmaps, customer journey, footfall analytics, behavior trends.
- Global search + command palette; dark/light; skeleton loading.

### FR-I Reports (Phase 10)
- Scheduled daily/weekly/monthly + executive/incident/productivity/inventory/store-health.
- AI-generated narrative (VLM/LLM) with root-cause analysis + recommendations; export PDF.

### FR-J Billing & Subscriptions (Phase 11)
- Plans (tiers by cameras/features), Stripe integration, metered usage (cameras, AI-minutes), invoices, payment history, upgrade/downgrade.

### FR-K Platform (cross-cutting)
- API keys for programmatic access; versioned REST (`/api/v1`) + OpenAPI/Swagger.
- Full audit logs; settings; AI assistant (chat over the tenant's own data/events).

## 4. Non-Functional Requirements
| Category | Target |
|---|---|
| **Availability** | 99.9% control plane; pipeline degrades gracefully (camera-isolated failures) |
| **Latency** | Live view < 2s glass-to-glass (WebRTC); alert < 5s from event; API p95 < 300ms |
| **Scale** | 10k cameras across tenants at GA; horizontal GPU autoscaling |
| **Security** | See [DEVELOPMENT_STANDARDS.md](DEVELOPMENT_STANDARDS.md) §Security; SOC2-ready controls |
| **Privacy** | Events-not-video default; biometrics consent-gated + region-flagged; configurable retention |
| **Observability** | OTel traces per pipeline stage; Prometheus/Grafana/Loki; Sentry |
| **Cost** | Per-camera GPU cost bounded by FPS sampling + conditional enrichment |

## 5. Acceptance criteria (definition of done, per feature)
Error handling · input validation · logging · tests (unit + integration) · OpenAPI docs · DB migration (if schema) · responsive UI · RLS-enforced · audit-logged. Repo builds & deploys after each phase.

## 6. Out of scope for v1
Hardware sales · edge-only offline mode · on-prem air-gapped install · mobile native apps (responsive web first) · legal-grade evidence chain.

## 7. Key risks & mitigations
| Risk | Mitigation |
|---|---|
| GPU cost explosion | FPS sampling, ROI masks, conditional VLM, model-per-usecase, Triton batching |
| Alert fatigue / false positives | Confidence thresholds, temporal debouncing, per-rule tuning, human ack loop |
| Biometric legal exposure (BIPA/GDPR) | Face/LPR opt-in, consent records, region gating, retention limits |
| RTSP/ONVIF camera diversity | Robust gateway, per-vendor quirks handling, health monitoring |
| Multi-tenant data leakage | Postgres RLS + per-request org context + tests that assert isolation |
