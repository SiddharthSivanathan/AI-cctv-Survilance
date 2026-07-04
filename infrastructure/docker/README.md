# Docker images

Per-service Dockerfiles (build context = repository root).

| File | Service | Base |
|---|---|---|
| `Dockerfile.api` | FastAPI control plane | `python:3.12-slim` |
| `Dockerfile.web` | Next.js frontend | `node:20-slim` (pnpm) |
| `Dockerfile.worker` | Celery workers | `python:3.12-slim` |
| `Dockerfile.ai-engine` | AI inference (CPU skeleton) | `python:3.12-slim` |
| `postgres/init.sql` | Postgres init | enables TimescaleDB + extensions |

The GPU variant of `ai-engine` (CUDA/TensorRT) is added in Phase 7.
Orchestrated by the root [`docker-compose.yml`](../../docker-compose.yml).
