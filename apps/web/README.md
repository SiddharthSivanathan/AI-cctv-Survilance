# @visionops/web

VisionOps AI dashboard — Next.js 15 (App Router), React 19, Tailwind, shadcn/ui.

## Responsibility
The web frontend. Talks **only** to the versioned REST API (`@visionops/sdk`); never to the database or AI services directly.

## Develop
```bash
pnpm --filter @visionops/web dev     # http://localhost:3000
```

## Structure
```
src/
├── app/                 # App Router routes
│   ├── layout.tsx       # root layout + providers
│   ├── page.tsx         # landing
│   ├── providers.tsx    # React Query + theme
│   └── health/route.ts  # liveness probe
└── lib/
    ├── api.ts           # shared API client
    └── env.ts           # public runtime config
```
Feature modules, auth, and the dashboard shell land in Phase 3+.
