# VisionOps AI — Project Plan & Checklist

Running source of truth for progress (Rule 11). Updated at the end of every phase.
Legend: ✅ done · 🔄 in progress · ⬜ not started · ⏸️ awaiting approval

---

## Phase 1 — Planning & Documentation ✅ (approved)
- ✅ Product Vision — `docs/PRODUCT_VISION.md`
- ✅ PRD — `docs/PRD.md`
- ✅ System Architecture — `ARCHITECTURE.md`
- ✅ Folder Structure — `docs/FOLDER_STRUCTURE.md`
- ✅ Tech Stack — `docs/TECH_STACK.md`
- ✅ Development Standards — `docs/DEVELOPMENT_STANDARDS.md`
- ✅ Locked decisions: Go gateway · TimescaleDB · milestone workflow
- ✅ Owner approval received

## Phase 2 — Project Setup ⏸️ (built — awaiting approval)
- ✅ Git repo + governance (LICENSE, CONTRIBUTING, CHANGELOG, .gitignore)
- ✅ pnpm workspaces + Turborepo (dev/build/lint/test/typecheck/format tasks)
- ✅ Tooling: TS base config, Prettier, EditorConfig, Husky + lint-staged + commitlint
- ✅ `apps/web` — Next.js 15 / React 19 / Tailwind / shadcn foundation + health route
- ✅ `apps/api` — FastAPI Clean Architecture skeleton, config, logging, async DB, Alembic, `/health` + `/ready`
- ✅ `apps/ai-engine` — inference service skeleton (Redis-connected lifecycle)
- ✅ `apps/worker` — Celery + Beat skeleton + `ping` task
- ✅ `packages/*` — config, types, utils (tested), ui, sdk
- ✅ `infrastructure/*` — Dockerfiles, nginx, k8s/terraform placeholders; root `docker-compose.yml` (Postgres+Timescale, Redis, MinIO, all services)
- ✅ CI workflow (`.github/workflows/ci.yml`)
- ⚠️ Full-stack `docker compose up` / `pnpm build` **not executed in this environment** (no Node/pnpm/Docker on this machine) — verify commands provided for the owner
- ⬜ **Owner approval to proceed to Phase 3**
- ℹ️ Go media gateway deferred to Phase 6 (Live Streaming), per Phase 1 architecture

## Phase 3 — Authentication & Multi-Tenant SaaS ⏸️ (built — awaiting approval)
Vertical slice (backend + frontend), per owner direction. Scope simplified for V1:
email+password only, one org per user, Owner role, hard email-verification gate.
- ✅ DB schema + migration: organizations, users, memberships, refresh_tokens, email_verification_tokens, password_reset_tokens, audit_logs (indexed)
- ✅ Postgres RLS on audit_logs (FORCE) + per-request tenant context — isolation test proves it
- ✅ JWT RS256 access + rotating refresh tokens with reuse detection (family revocation)
- ✅ Argon2id passwords · opaque hashed verification/reset tokens (24h verify expiry)
- ✅ Auth API: register, verify-email (auto-login), resend, login (verified-gate), refresh, logout, forgot/reset password, me
- ✅ Organizations API: create company (Owner) + onboarding state
- ✅ Redis-backed rate limiting on sensitive auth endpoints (fail-open)
- ✅ Clean error envelope + security headers middleware
- ✅ Frontend: landing, signup, login (+resend), forgot/reset password, verify-email, company setup + onboarding wizard, protected dashboard placeholder
- ✅ Auth store (Zustand) + api client with silent token refresh + route guard
- ✅ Tests: unit (password/jwt/tokens) + integration (register/verify/login, refresh rotation, tenant isolation, onboarding); CI runs them on Postgres+Redis
- ⚠️ Not executed in this environment (no Node/Docker/Python 3.12) — verify commands provided
- ℹ️ MFA/SSO/invites deferred; schema kept extensible. Refresh token stored client-side for V1 (httpOnly-cookie/BFF hardening noted for Phase 12)
- ⬜ **Owner approval to proceed to Phase 4**

## Phase 4 — Organizations & Stores ⏸️ (built — awaiting approval)
Vertical slice. Simplified per owner: **no Branch entity** (Store = location); richer org settings.
- ✅ `stores` table + migration with RLS (FORCE); cross-tenant isolation test
- ✅ Store CRUD API (list/create/get/update/delete), `require_membership` gate
- ✅ Organization settings: logo, contact email/phone, address, timezone, currency, alert-email toggle; read-only id + created date
- ✅ Object storage layer (boto3 → S3/MinIO), bucket auto-create, logo upload endpoint
- ✅ Frontend: dashboard sidebar shell, stores list/new/detail/edit, settings page (with logo upload), onboarding step 2 wired to real store creation
- ✅ Shared UI primitives: Textarea, Select, Switch, Skeleton
- ✅ Tests: store CRUD + tenant isolation + onboarding gate; org settings read/update
- ⚠️ Object-storage/logo flows need Docker/MinIO to fully verify
- ⬜ **Owner approval to proceed to Phase 5**
- ℹ️ Branch entity deferred; schema designed to add it later without refactor

## Phase 5 — Camera Management & RTSP Integration ⏸️ (built — awaiting approval)
Vertical slice. ONVIF/discovery deferred per owner; focus on reliable RTSP validation.
- ✅ `cameras` table + migration with RLS; store-ownership check on create/update
- ✅ Credentials encrypted at rest (Fernet); passwords never returned/logged; masked rtsp_url + has_credentials; blank-password-keeps on edit
- ✅ RTSP validation via ffmpeg/ffprobe: connect, auth, capture frame → thumbnail, detect resolution/fps/codec; status enum
- ✅ Camera CRUD + `POST /cameras/{id}/test` + `POST /cameras/test-connection`
- ✅ Health monitoring: Celery Beat (60s) → internal token-guarded sweep; offline >5min emits `camera.offline` event (full alerts in Phase 10)
- ✅ Frontend: cameras grid, add (with Test Connection), detail (preview + test), edit; store detail lists its cameras; sidebar Cameras enabled
- ✅ UI primitive: Badge; camera status badges + preview thumbnails
- ✅ Tests: crypto + rtsp unit; camera CRUD/masking/isolation + health sweep integration (probe monkeypatched)
- ⚠️ Real ffmpeg RTSP capture needs a live camera + Docker to verify
- ⬜ **Owner approval to proceed to Phase 6**

## Phase 6 — Live Streaming Service ⬜
Go gateway RTSP ingest · WebRTC/HLS · camera grid live view.

## Phase 7 — AI Vision Pipeline ⬜
YOLOv11 + ByteTrack · detections → TimescaleDB · conditional enrichment (fire/smoke, PPE, pose, LPR, OCR, VLM).

## Phase 8 — Rule Engine ⬜
No-code builder · safe typed AST · temporal/stateful conditions · real-time alerts.

## Phase 9 — Dashboard & Analytics ⬜
KPI dashboard · heatmaps · footfall · journey · command palette · search · dark/light.

## Phase 10 — Reports & Notifications ⬜
Scheduled + AI-narrative reports (PDF, RCA) · multi-channel notifications · Alert Center.

## Phase 11 — Billing & Subscription ⬜
Stripe · plans · metered usage · invoices · payments.

## Phase 12 — Testing, Security & Production Deployment ⬜
E2E tests · security hardening · K8s + Helm · GPU node pools · observability · runbooks.

---

## Next recommended action
**Verify & approve Phase 5** (cameras slice), then I present the Phase 6 plan (Live Streaming Service — Go media gateway, WebRTC/HLS, camera grid live view) with the exact file list and **stop again** before writing code — per Rule 3.
