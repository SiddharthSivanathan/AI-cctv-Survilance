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
├── app/
│   ├── (auth)/          # login, signup, forgot/reset password, verify-email
│   ├── onboarding/      # company setup + onboarding wizard
│   ├── dashboard/       # protected dashboard (placeholder — Phase 9)
│   ├── layout.tsx       # root layout + providers
│   ├── page.tsx         # landing
│   └── providers.tsx    # React Query + theme
├── components/          # auth-guard, shared components
├── features/auth/       # api, hooks, types, use-auth
├── stores/              # Zustand (auth-store)
└── lib/                 # api-client (auto-refresh), env
```

## Auth flow (Phase 3)
Signup → email verification (24h) → auto-login on verify → company setup →
onboarding wizard → dashboard. Login is blocked until the email is verified
(with a resend action). Access token in memory/localStorage; the API client
silently refreshes on 401.
