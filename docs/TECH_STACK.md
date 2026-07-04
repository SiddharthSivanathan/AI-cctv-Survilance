# VisionOps AI — Tech Stack (locked)

Decisions confirmed with product owner: **Go media gateway**, **TimescaleDB event store**, milestone-based delivery.

## Frontend (`apps/web`)
- **Next.js 15** (App Router, React Server Components)
- **React 19**, **TypeScript** (strict)
- **Tailwind CSS** + **shadcn/ui** (Radix primitives)
- **Framer Motion** (animation)
- **TanStack Query** (server state) + **Zustand** (client/UI state)
- **react-hook-form + Zod** (forms/validation)
- Types generated from backend **OpenAPI** → `packages/shared-types` (single source of truth)
- Live video: **WebRTC** player, **HLS.js** fallback

## Backend — Control Plane (`apps/api`)
- **Python 3.12**, **FastAPI**
- **SQLAlchemy 2.0** (async) + **Alembic** migrations
- **Pydantic v2** (validation, settings, OpenAPI)
- **Clean Architecture**: api → services → repositories → models; **Dependency Injection**; **Repository Pattern**
- **JWT** (RS256), **Argon2id**, **pyotp** (MFA)
- API versioning (`/api/v1`), Swagger/OpenAPI, rate limiting (slowapi/Redis)

## Media Gateway (`apps/gateway`) — **Go**
- **Go 1.22+**
- RTSP pull + **ONVIF** discovery; H.264/H.265 decode
- FPS sampling; frame publish to pipeline bus
- Live stream origin (WebRTC/HLS) via **MediaMTX** (or mediasoup) integration
- gRPC/Redis Streams to inference plane

## AI Inference (`apps/inference`)
- **Python 3.12**, **PyTorch**
- **YOLOv11** (Ultralytics) → **ONNX Runtime** / **TensorRT**
- **ByteTrack** (tracking)
- **NVIDIA Triton Inference Server** (multi-model GPU sharing/batching) — prod
- **OpenCV** (frame ops, ROI masks)
- **SAM2** (segmentation, where needed), **Whisper** (audio, optional)
- VLM: **Qwen2.5-VL** (self-host) + **Gemini Vision** (managed fallback) via a model router

## Async / Workers (`services/*`)
- **Celery** + **Celery Beat** (rules eval, notifications, report scheduling, billing jobs)
- **Redis** (broker, cache, distributed locks, **Redis Streams** pipeline bus → Kafka/Redpanda at scale)

## Data
- **PostgreSQL 16** + **Row-Level Security** (control plane, tenant isolation)
- **TimescaleDB** (hypertables for detections/events/analytics time-series)
- **Object storage**: S3 / GCS / Azure Blob (clips, thumbnails, report PDFs, model artifacts) behind one storage interface
- **MinIO** for local dev object storage

## Infrastructure
- **Docker** + **Docker Compose** (dev)
- **Kubernetes** (prod) + **Helm**; GPU node pools for inference
- **Nginx** / Ingress; cert-manager (HTTPS)
- Cloud-agnostic; reference deploy on **AWS** (EKS + S3 + RDS/Aurora + ElastiCache), portable to GCP/Azure
- **Terraform** (optional, infra as code)

## Observability & Quality
- **OpenTelemetry** → **Prometheus** + **Grafana** + **Loki**; **Sentry** (errors)
- **structlog** (structured JSON logs)
- Tests: **pytest** (backend), **Vitest/Playwright** (frontend), **go test** (gateway)
- Lint/format: **ruff** + **mypy** (py), **ESLint** + **Prettier** (ts), **golangci-lint** (go)
- **pre-commit** hooks; CI (GitHub Actions): lint → typecheck → test → build → docker

## Payments & Comms
- **Stripe** (billing/subscriptions/metering)
- Notifications: **SMTP/SES** (email), **Twilio** (SMS/WhatsApp), **Slack**, **MS Teams**, web push (VAPID), generic webhooks

## Repo tooling
- Monorepo managed with **pnpm workspaces** (JS) + **uv/poetry** (Python) + Go modules
- Task runner: **Make** / **Taskfile**
