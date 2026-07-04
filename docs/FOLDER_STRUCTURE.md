# VisionOps AI — Folder Structure

Monorepo. Strict separation of concerns: frontend / backend / AI / gateway / data / infra never bleed into each other. This is the **target** layout; directories are created per-phase, not all at once.

```
visionops-ai/
├── apps/
│   ├── web/                          # Next.js 15 frontend
│   │   ├── src/
│   │   │   ├── app/                  # App Router (route groups: (auth), (dashboard))
│   │   │   ├── components/           # ui/ (shadcn), shared, feature components
│   │   │   ├── features/             # feature modules (alerts, cameras, reports…)
│   │   │   ├── lib/                  # api client, query hooks, utils
│   │   │   ├── stores/               # Zustand stores
│   │   │   ├── hooks/                # React hooks
│   │   │   └── types/                # generated from OpenAPI
│   │   ├── public/
│   │   └── package.json
│   │
│   ├── api/                          # FastAPI control plane (Clean Architecture)
│   │   ├── app/
│   │   │   ├── api/v1/               # routers (thin controllers)
│   │   │   ├── core/                 # config, security, logging, deps (DI)
│   │   │   ├── domain/               # entities, value objects, domain services
│   │   │   ├── schemas/              # Pydantic request/response models
│   │   │   ├── services/             # use-cases / business logic
│   │   │   ├── repositories/         # data access (Repository Pattern)
│   │   │   ├── models/               # SQLAlchemy ORM models
│   │   │   ├── db/                   # session, RLS context, base
│   │   │   └── main.py
│   │   ├── tests/                    # unit + integration
│   │   └── pyproject.toml
│   │
│   ├── gateway/                      # Go media gateway
│   │   ├── cmd/gateway/main.go
│   │   ├── internal/
│   │   │   ├── rtsp/                 # RTSP pull + decode
│   │   │   ├── onvif/                # ONVIF discovery
│   │   │   ├── sampler/              # FPS sampling
│   │   │   ├── publisher/            # frame → pipeline bus
│   │   │   └── stream/               # WebRTC/HLS origin
│   │   ├── pkg/
│   │   └── go.mod
│   │
│   └── inference/                    # AI workers
│       ├── src/
│       │   ├── detectors/            # YOLOv11, fire/smoke, PPE…
│       │   ├── tracking/             # ByteTrack
│       │   ├── enrichment/           # LPR, OCR, pose, VLM router
│       │   ├── pipeline/             # frame consumer → detection emitter
│       │   └── models/               # model loading (ONNX/TRT/Triton clients)
│       ├── tests/
│       └── pyproject.toml
│
├── services/
│   ├── rules-engine/                 # Celery: rule AST eval, stateful temporal rules
│   ├── notifications/                # Celery: multi-channel fanout
│   └── reporting/                    # Celery Beat: report generation
│
├── packages/
│   ├── shared-types/                 # OpenAPI-generated TS types
│   └── ui/                           # shared component library (optional)
│
├── db/
│   ├── migrations/                   # Alembic
│   └── seeds/                        # seed data
│
├── infra/
│   ├── docker/                       # Dockerfiles per service
│   │   └── docker-compose.yml        # dev: postgres+timescale, redis, minio, api, web…
│   ├── k8s/                          # Helm charts / manifests (prod)
│   └── terraform/                    # cloud infra (optional)
│
├── docs/
│   ├── PRODUCT_VISION.md
│   ├── PRD.md
│   ├── TECH_STACK.md
│   ├── FOLDER_STRUCTURE.md
│   ├── DEVELOPMENT_STANDARDS.md
│   ├── PROJECT_PLAN.md               # running checklist (Rule 11)
│   └── adr/                          # Architecture Decision Records
│
├── .github/workflows/               # CI: lint, typecheck, test, build
├── ARCHITECTURE.md
├── Makefile / Taskfile.yml
├── pnpm-workspace.yaml
└── README.md
```

## Layering rules (enforced in review)
- **Frontend** talks only to the versioned REST API — never to the DB or inference directly.
- **API routers** are thin — no business logic; they call **services**, which call **repositories**.
- **Repositories** are the only layer that touches the ORM/DB.
- **Inference/gateway** never touch the control DB directly — they publish to the bus / write events via a narrow interface.
- **Domain layer** has no framework imports (pure Python) — Clean Architecture dependency rule.
