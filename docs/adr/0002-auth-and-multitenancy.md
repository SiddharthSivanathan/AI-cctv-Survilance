# ADR 0002 — Authentication & Multi-Tenancy (V1)

- **Status:** Accepted
- **Date:** 2026-07-04
- **Phase:** 3 (Authentication & Multi-Tenant SaaS)

## Context
V1 needs secure authentication and tenant isolation that is simple to use now
but does not require a rewrite when richer features (invites, multi-org, MFA,
SSO, RBAC) arrive. Product direction: email+password only, one organization per
user, a single Owner role, and a hard email-verification gate.

## Decisions
1. **Identity via `users` + `memberships` (not `organization_id` on `users`).**
   A `membership` join table links a user to an org with a role. V1 enforces one
   org per user with a unique constraint on `user_id`; dropping it later enables
   many orgs per user and invitations with **no schema refactor**.
2. **Tenant isolation with Postgres RLS.** `audit_logs` is the first tenant-scoped
   table: `ENABLE` + `FORCE ROW LEVEL SECURITY` with a policy keyed on
   `current_setting('app.current_org')`, set per request (`SET LOCAL`) from the
   token. Isolation is enforced at the database, not by application queries. An
   integration test asserts cross-tenant reads return nothing. Stores/cameras/
   events (Phase 4+) follow this exact pattern.
   - Audit **inserts** use a client-side `created_at` to avoid `INSERT ... RETURNING`,
     which under `FORCE RLS` would re-check the SELECT policy and reject
     pre-onboarding (org NULL) rows.
3. **RS256 JWT access tokens.** Asymmetric so the AI engine / gateway can verify
   with the public key without the signing secret. Dev/test auto-generate an
   ephemeral keypair; production requires configured keys.
4. **Rotating refresh tokens with reuse detection.** Only token hashes are
   stored, grouped by `family_id`. Presenting a rotated token revokes the whole
   family (theft response).
5. **Argon2id** password hashing. Opaque, hashed, single-use email-verification
   (24h) and password-reset tokens.
6. **Clean Architecture + DI.** Routers → services → repositories → models; the
   domain/role enum and `require_role` dependency are the seam for future RBAC.
7. **Email via a port.** `EmailSender` interface with a `ConsoleEmailSender` dev
   adapter; SMTP/SES implementation swaps in at Phase 10 with no call-site change.

## Trade-offs / follow-ups
- **Refresh token stored client-side** (Zustand/localStorage) for V1 velocity.
  Hardening to an httpOnly-cookie/BFF model is tracked for Phase 12.
- **One Owner role only** now; permission catalog intentionally omitted (kept
  extensible via the `role` column + rank map).
