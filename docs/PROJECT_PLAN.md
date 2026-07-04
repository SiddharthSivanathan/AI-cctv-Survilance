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

## Phase 3 — Authentication & Multi-Tenant SaaS ⬜
JWT + refresh rotation · Argon2id · MFA · orgs · RLS isolation · RBAC · sessions · audit logs.

## Phase 4 — Organization, Stores & Branches ⬜
Org/user management · invitations · stores · branches · settings · audit.

## Phase 5 — Camera Management & RTSP Integration ⬜
Camera CRUD · encrypted creds · ONVIF discovery · zones/ROIs · health/heartbeats.

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
**Verify & approve Phase 2** (run the verify commands in the README / phase summary), then I present the Phase 3 plan (auth + multi-tenant DB schema + RLS) with the exact file list and **stop again** before writing code — per Rule 3.
