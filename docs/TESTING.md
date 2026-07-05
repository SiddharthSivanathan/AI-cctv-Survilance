# Testing

## Running the suites
```bash
# API (needs Postgres + Redis; integration tests skip if the DB is unreachable)
cd apps/api && pip install -e ".[dev]" && alembic upgrade head && pytest -q

# AI engine (pure logic; ML mocked — no torch/ffmpeg needed)
cd apps/ai-engine && pip install -e ".[dev]" && pytest -q

# Worker
cd apps/worker && pip install -e ".[dev]" && pytest -q

# Gateway (Go)
cd apps/gateway && go test ./...

# Frontend
pnpm --filter @visionops/utils test
pnpm --filter @visionops/web build
```
CI runs all of the above (Postgres + Redis services for the API job).

## Coverage matrix (what is / isn't verifiable without live infra)

| Area | Tested here | Needs running stack |
|---|---|---|
| Auth (register/verify/login/refresh rotation/reuse) | ✅ integration | — |
| Tenant isolation (RLS) | ✅ asserted cross-tenant | — |
| Stores / cameras / zones / rules CRUD + isolation | ✅ | — |
| Credential encryption + masking | ✅ unit + integration | — |
| Rule engine (queue/occupancy/loitering/unattended, cooldown) | ✅ pure unit | — |
| Event dedup / open-resolve / alerts | ✅ integration | — |
| Analytics aggregation + metrics | ✅ integration | — |
| Notifications (create, mark read) | ✅ integration | — |
| Reports (generate, CSV) | ✅ integration | PDF render (reportlab) |
| WebSocket auth rejection | ✅ | live delivery |
| RTSP probe / YOLO inference | ⚠️ logic only (mocked) | ffmpeg + camera + (GPU) |
| WebRTC live view | — | MediaMTX + camera + browser |
| SMTP email delivery | ⚠️ enqueue path | real SMTP |
| PDF rendering, Beat schedules | — | running worker/stack |

The items in the right column are inherently integration/infra concerns —
verify them against a real deployment (`docker compose -f docker-compose.prod.yml`).
