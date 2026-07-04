# Changelog

All notable changes to this project are documented here.
Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
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
