# ADR 0001 — Monorepo, Turborepo, and polyglot service boundaries

- **Status:** Accepted
- **Date:** 2026-07-04
- **Phase:** 2 (Project Setup)

## Context
VisionOps AI spans TypeScript (web), Python (API, AI, workers), and later Go
(media gateway). We need one repository that keeps these isolated yet
orchestratable, with shared types and consistent tooling.

## Decision
1. **Monorepo** managed with **pnpm workspaces** (JS) + **Turborepo** (task
   orchestration/caching across all packages, including Python apps via thin
   `package.json` script wrappers).
2. **Polyglot apps** live under `apps/*`; each is independently runnable and
   has its own dependency manifest (`pyproject.toml` / `package.json`).
3. **Shared TS packages** under `packages/*`: `config` (tsconfig/eslint/tailwind),
   `types` (incl. future OpenAPI-generated DTOs), `utils`, `ui`, `sdk`.
4. **Infrastructure** is separated under `infrastructure/*` (docker, kubernetes,
   nginx, terraform); the root `docker-compose.yml` runs the full local stack.
5. **Clean Architecture** enforced inside the API (api → services → repositories
   → models; pure domain layer).

## Consequences
- One `pnpm install`; `turbo run <task>` fans out across the graph with caching.
- Python apps participate in Turborepo tasks but keep native tooling (ruff,
  mypy, pytest, Alembic).
- Frontend/backend/AI/infra never cross-import — enforced by directory layout.
- The Go media gateway (Phase 6) slots in as `apps/gateway` without disruption.

## Alternatives considered
- **Polyrepo:** rejected — cross-service type sharing and coordinated changes
  become painful at this stage.
- **Nx instead of Turborepo:** heavier; Turborepo is sufficient and simpler.
