# VisionOps AI — Development Standards

These are binding rules for every phase. A module is not "done" until it satisfies all of §Definition of Done.

## Architecture
- **Clean Architecture** + **SOLID**. Dependencies point inward; domain has no framework imports.
- **Repository Pattern** for all data access; **Dependency Injection** for services/clients.
- Strict **separation of concerns**: frontend / backend / AI / gateway / data / infra are isolated (see FOLDER_STRUCTURE §Layering rules).
- API **versioned** (`/api/v1`); breaking changes → new version, never mutate v1.
- No cross-tenant logic without an explicit `organization_id` scope + RLS.

## Code quality
- **Python**: ruff (lint+format), mypy (strict typing), Google-style docstrings on public APIs.
- **TypeScript**: strict mode, ESLint + Prettier, no `any` without justification.
- **Go**: gofmt, golangci-lint, errors wrapped with context.
- Functions small, single-responsibility; names descriptive; no dead/commented-out code.
- **No placeholders, fake APIs, or mock logic** in committed code unless explicitly instructed.

## Every feature must include
1. **Error handling** — typed exceptions, no bare `except`, graceful degradation.
2. **Validation** — Pydantic/Zod at boundaries; never trust client input.
3. **Logging** — structured (structlog/JSON), correlation IDs, no secrets/PII in logs.
4. **Tests** — unit for logic, integration for API/DB; multi-tenant isolation asserted.
5. **Documentation** — OpenAPI for APIs, docstrings, README/ADR updates.
6. **Migrations** — every schema change ships an Alembic migration (up + down).
7. **Responsive UI** — mobile → desktop; a11y (keyboard, ARIA).

## Security (SOC2-ready baseline)
- JWT RS256; access 15 min; refresh rotation + reuse detection; Argon2id passwords.
- **RBAC** enforced server-side on every endpoint (never trust the client).
- **Postgres RLS** for tenant isolation + per-request org context (defense in depth).
- Secrets in vault/KMS; **camera RTSP creds encrypted at rest**, never returned by API.
- Parameterized queries only (no string-built SQL). Input validation everywhere.
- CORS allowlist, CSRF for cookie flows, security headers (CSP/HSTS/X-Frame-Options), rate limiting.
- **Audit log** every mutating action (actor, action, resource, ip, timestamp).
- Dependency scanning + secret scanning in CI.
- Privacy: events-not-video default; face/LPR consent-gated + region-flagged; data retention config.

## Testing
- Coverage target ≥ 80% on services/domain.
- Test pyramid: many unit, fewer integration, few e2e (Playwright).
- Every bug fix ships a regression test.
- CI must be green (lint → typecheck → test → build) before merge.

## Git & delivery
- Modular, isolated commits; conventional commit messages.
- Feature branches; PRs reviewed against this doc.
- **Never modify unrelated files. Never refactor working modules unless requested.**
- **Every completed milestone leaves the repo in a buildable, deployable state.**

## Definition of Done (per module)
- [ ] Builds successfully (all apps)
- [ ] All tests pass; coverage target met
- [ ] Lint + type checks clean
- [ ] Migrations included & reversible (if schema changed)
- [ ] OpenAPI / docs updated
- [ ] Error handling, validation, logging present
- [ ] Security & RBAC + RLS verified
- [ ] Responsive & accessible (if UI)
- [ ] PROJECT_PLAN.md checklist updated
- [ ] Nothing unrelated changed
