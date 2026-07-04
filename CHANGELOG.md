# Changelog

All notable changes to this project are documented here.
Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
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
