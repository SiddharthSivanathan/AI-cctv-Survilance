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

## Endpoints (Phase 2)
- `GET /health` — liveness
- `GET /ready` — readiness (Postgres + Redis)
- `GET /docs` — Swagger UI · `GET /openapi.json`
