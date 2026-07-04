# @visionops/api

VisionOps AI control plane — FastAPI, async SQLAlchemy 2.0, Clean Architecture.

## Responsibility
The tenant-facing REST API: auth, orgs, stores, cameras, rules, billing. Owns the
control-plane database. Publishes/consumes the event bus but never runs inference.

## Layers (Clean Architecture)
```
app/
├── api/v1/        # routers (thin controllers)
├── schemas/       # Pydantic request/response DTOs
├── services/      # use-cases / business logic        (Phase 3+)
├── repositories/  # data access (Repository Pattern)  (Phase 3+)
├── models/        # SQLAlchemy ORM models             (Phase 3+)
├── domain/        # pure domain entities              (Phase 3+)
├── db/            # engine, session, base
└── core/          # config, logging, security, DI
```

## Develop
```bash
pip install -e ".[dev]"
uvicorn app.main:app --reload      # http://localhost:8000/docs
pytest -q                          # tests
ruff check app tests && mypy app   # lint + types
```

## Endpoints
Health: `GET /health` (liveness) · `GET /ready` (Postgres + Redis) · `GET /docs`.

Auth (`/api/v1/auth`, Phase 3):
`POST /register` · `POST /verify-email` · `POST /resend-verification` · `POST /login` ·
`POST /refresh` · `POST /logout` · `POST /forgot-password` · `POST /reset-password` · `GET /me`.

Organizations (`/api/v1/organizations`): `POST /` (create company / onboarding) · `GET /current`.

## Auth model (V1)
Email + password (Argon2id). RS256 JWT access + rotating refresh tokens (reuse
detection). Hard email-verification gate (24h link). One organization per user
(Owner). Tenant isolation via Postgres RLS + per-request `app.current_org`.
See [ADR 0002](../../docs/adr/0002-auth-and-multitenancy.md).

## Local keys
`bash scripts/generate_keys.sh` writes an RS256 keypair to `apps/api/keys/`
(gitignored). In dev, an ephemeral keypair is generated automatically if none
is configured.
