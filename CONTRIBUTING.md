# Contributing to VisionOps AI

Thank you for contributing. This repository follows strict enterprise engineering standards — see [docs/DEVELOPMENT_STANDARDS.md](docs/DEVELOPMENT_STANDARDS.md) for the binding rules. This file is the quick-start.

## Prerequisites
- **Node.js** ≥ 20.11 and **pnpm** ≥ 9 (`corepack enable`)
- **Python** ≥ 3.12 with **uv** or **pip**
- **Docker** + **Docker Compose**

## Setup
```bash
pnpm install            # installs JS deps + Husky hooks
cp .env.example .env    # configure environment
docker compose up -d    # start infra + services
```

## Monorepo tasks (Turborepo)
```bash
pnpm dev         # run all apps in dev
pnpm build       # build everything
pnpm lint        # lint all packages
pnpm test        # run all tests
pnpm typecheck   # type-check all TS packages
pnpm format      # Prettier write
```
Scope to one app: `pnpm --filter @visionops/web dev`.

## Branching
- `main` — always deployable. No direct commits.
- Feature branches: `feat/<scope>-<short-desc>`, `fix/<scope>-<short-desc>`.

## Commit messages — Conventional Commits (enforced by commitlint)
```
<type>(<scope>): <subject>

feat(api): add refresh token rotation
fix(web): correct alert badge count
docs(repo): update setup guide
```
**Types:** feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert.
**Scopes:** web, api, ai-engine, worker, ui, config, types, utils, sdk, infra, docs, deps, release, repo.

## Coding standards (summary)
- Clean Architecture + SOLID; Repository Pattern; Dependency Injection.
- **Python:** ruff + mypy (strict), type hints, docstrings.
- **TypeScript:** strict mode, ESLint + Prettier, no unjustified `any`.
- Every feature: error handling · validation · logging · tests · docs · migrations (if schema).
- **No placeholder/fake logic.** No secrets committed. Never modify unrelated files.

## Pull requests
1. `pnpm lint && pnpm test && pnpm typecheck` all green.
2. Update docs + `CHANGELOG.md` (`[Unreleased]`).
3. Reference the phase/module. PRs reviewed against Development Standards.

## Definition of Done
See the checklist in [docs/DEVELOPMENT_STANDARDS.md](docs/DEVELOPMENT_STANDARDS.md#definition-of-done-per-module).
