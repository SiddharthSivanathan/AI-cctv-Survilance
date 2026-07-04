# VisionOps AI

> Turn existing CCTV into an always-on AI operations analyst. Multi-tenant SaaS for AI-powered video intelligence.

**Status:** Phase 2 (Project Setup) complete — awaiting approval. Enterprise monorepo foundation; no business logic yet.

## Monorepo layout
```
apps/
  web/         Next.js 15 dashboard (React 19, Tailwind, shadcn)
  api/         FastAPI control plane (Clean Architecture, async SQLAlchemy)
  ai-engine/   Computer-vision inference service (YOLOv11/ByteTrack — Phase 7)
  worker/      Celery background jobs (rules, notifications, reports)
  mobile/      Reserved (future React Native)
packages/
  config/      Shared tsconfig / eslint / tailwind preset
  types/       Shared TS types (+ future OpenAPI-generated DTOs)
  utils/       Framework-agnostic helpers
  ui/          Shared React component library (shadcn based)
  sdk/         Internal typed API client
infrastructure/
  docker/      Dockerfiles + Postgres init
  kubernetes/  Manifests/Helm (Phase 12)
  nginx/       Reverse-proxy template
  terraform/   Cloud IaC (Phase 12)
```

## Prerequisites
Node ≥ 20 + pnpm ≥ 9 (`corepack enable`) · Python ≥ 3.12 · Docker + Docker Compose.

## Quick start
```bash
cp .env.example .env
bash scripts/bootstrap.sh          # install JS + Python deps
docker compose up --build          # full stack (web:3000, api:8000, +infra)
```

### Verify the foundation
```bash
# Backend (per app: api, ai-engine, worker)
cd apps/api && pip install -e ".[dev]" && pytest -q && ruff check app tests

# Frontend + shared packages
pnpm install
pnpm --filter @visionops/utils test
pnpm --filter @visionops/web build

# Health checks (with stack running)
curl localhost:8000/health     # {"status":"ok",...}
curl localhost:8000/ready      # DB + Redis connectivity
curl localhost:3000/health     # web liveness
```

## Turborepo tasks
`pnpm dev` · `pnpm build` · `pnpm lint` · `pnpm test` · `pnpm typecheck` · `pnpm format`

## Documentation
| Doc | Purpose |
|---|---|
| [Product Vision](docs/PRODUCT_VISION.md) | Why this exists, who it's for |
| [PRD](docs/PRD.md) | Features, NFRs, risks |
| [Architecture](ARCHITECTURE.md) | Three-plane system design |
| [Tech Stack](docs/TECH_STACK.md) | Locked technology choices |
| [Folder Structure](docs/FOLDER_STRUCTURE.md) | Monorepo layout & layering rules |
| [Development Standards](docs/DEVELOPMENT_STANDARDS.md) | Engineering rules + Definition of Done |
| [Project Plan](docs/PROJECT_PLAN.md) | Running progress checklist |
| [ADRs](docs/adr/) | Architecture Decision Records |

## Key decisions (locked)
Media gateway **Go** (Phase 6) · Event store **TimescaleDB** · Delivery **milestone-based, stop-and-approve per phase**.

## License
[MIT](LICENSE)
