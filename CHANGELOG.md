# Changelog

All notable changes to this project are documented here.
Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Phase 7 — AI Vision Pipeline** (stateless detector; backend + overlay):
  - ffmpeg frame sampler (reads MediaMTX internal RTSP at 2 fps, 640×640) → capped Redis frames stream; sampler manager provisions paths and reconciles from `GET /internal/cameras/streams`.
  - YOLOv11s detector (Ultralytics, lazy-loaded, pure parse function) + IOU tracker (ByteTrack-swappable via `supervision`).
  - Detection worker: Redis consumer group → detect → track → publish detection payloads (ephemeral) + `detections:latest` key. Stateless and DB-free.
  - API: internal camera-streams endpoint (decrypted sources) and `GET /cameras/{id}/detections/latest` (tenant-scoped Redis read) for the live overlay.
  - Frontend: live bounding-box overlay + person count on the WebRTC player.
  - MediaMTX internal RTSP enabled; ai-engine image adds ffmpeg + ML deps. Tests (ML-mocked) for parsing/tracking/payloads.
  - No raw-detection persistence; business events/alerts/zones/rules deferred to Phase 8.
- **Phase 6 — Live Streaming Service** (backend + gateway + frontend vertical slice):
  - New Go media gateway (`apps/gateway`, standard library only): provisions on-demand MediaMTX paths, verifies backend-issued HS256 playback tokens, and authorizing-reverse-proxies WHEP signaling (MediaMTX stays internal).
  - MediaMTX added as the WebRTC media plane; docker-compose services (`mediamtx`, `gateway`) + config.
  - API `POST /cameras/{id}/live`: tenant-authorized, decrypts RTSP source, provisions the path, issues a short-lived token + `whep_url`.
  - Frontend: WHEP WebRTC `LivePlayer` (loading/live/reconnecting/error, auto-reconnect), camera detail live view, live grid (1×1/2×2/3×3), Live nav entry.
  - Tests: gateway token/routing (Go) + API stream token issuance & tenant scoping; CI Go job added.
  - WebRTC only (no HLS/DASH). AI frame ingestion deferred to Phase 7.
- **Phase 5 — Camera Management & RTSP Integration** (backend + frontend vertical slice):
  - `cameras` table + migration with Row-Level Security; store-ownership validation on create/update.
  - RTSP credentials encrypted at rest (Fernet); passwords never returned or logged; `rtsp_url` userinfo stripped; `has_credentials` flag; blank-password-keeps-existing on edit.
  - RTSP validation via ffmpeg/ffprobe: connect, authenticate, capture a frame → thumbnail (object storage), detect resolution/fps/codec; typed status result.
  - Camera CRUD, `POST /cameras/{id}/test`, `POST /cameras/test-connection`, `GET /stores/{id}/cameras`.
  - Health monitoring: Celery Beat (60s) triggers an internal token-guarded sweep; cameras offline beyond threshold emit a `camera.offline` event (full alerts arrive in Phase 10).
  - Frontend: cameras grid, add/detail/edit with live "Test Connection", preview thumbnails, status badges; store detail lists its cameras; Cameras enabled in the sidebar.
  - Shared UI primitive: Badge. ffmpeg added to the API image.
- **Phase 4 — Organizations & Stores** (backend + frontend vertical slice):
  - `stores` table + migration with Row-Level Security; store CRUD API gated by an onboarded-membership dependency; cross-tenant isolation test.
  - Organization settings (logo, contact, address, timezone, currency, email-alert toggle) with read-only id/created date; `PATCH /organizations/current`.
  - Object-storage layer (boto3 → S3/MinIO) with bucket auto-creation and a logo upload endpoint.
  - Frontend: dashboard sidebar shell, stores list/create/detail/edit, settings page with logo upload; onboarding "Add first store" wired to the real API.
  - Shared UI primitives: Textarea, Select, Switch, Skeleton.
  - Note: Branch entity intentionally deferred; Store is the single V1 location entity.
- **Phase 3 — Authentication & Multi-Tenant SaaS** (backend + frontend vertical slice):
  - Multi-tenant schema + Alembic migration (organizations, users, memberships, refresh/verification/reset tokens, audit logs) with Postgres Row-Level Security on `audit_logs`.
  - JWT RS256 access tokens + rotating refresh tokens with reuse detection; Argon2id passwords.
  - Auth API: register, email verification (24h, auto-login), resend, login (email-verified gate), refresh, logout, forgot/reset password, `me`; organization creation + onboarding state.
  - Redis-backed rate limiting, consistent error envelope, security-headers middleware.
  - Frontend: landing, signup, login, forgot/reset password, verify-email, company setup + onboarding wizard, protected dashboard; Zustand auth store + auto-refreshing API client + route guard.
  - Shared UI primitives: Input, Label, Card, Alert.
  - Tests: unit (password/JWT/tokens) + integration (register→verify→login, refresh rotation, tenant isolation, onboarding); CI now runs the API suite against Postgres + Redis.

- **Phase 2 — Project Setup:** Turborepo + pnpm monorepo foundation.
  - Root tooling: pnpm workspaces, Turborepo, TypeScript base config, Prettier, EditorConfig.
  - Git hooks: Husky (`pre-commit`, `commit-msg`), lint-staged, Conventional Commits (commitlint).
  - `apps/web` — Next.js 15 / React 19 / Tailwind / shadcn foundation with health route.
  - `apps/api` — FastAPI skeleton (Clean Architecture layers), config, structured logging, async DB session, Alembic init, `/health` + `/api/v1`.
  - `apps/ai-engine` — AI vision service worker skeleton (Redis-connected).
  - `apps/worker` — Celery + Beat skeleton.
  - `packages/*` — `config`, `types`, `utils`, `ui`, `sdk` shared package scaffolds.
  - `infrastructure/` — Docker, Kubernetes, Nginx, Terraform folders; root `docker-compose.yml` (Postgres+TimescaleDB, Redis, MinIO, all services).
  - CI workflow scaffold (`.github/workflows/ci.yml`).
  - Governance: `LICENSE` (MIT), `CONTRIBUTING.md`, `CHANGELOG.md`.

### Documentation
- **Phase 1:** Product Vision, PRD, System Architecture, Folder Structure, Tech Stack, Development Standards, Project Plan.

[Unreleased]: https://example.com/visionops-ai/tree/main
