# ADR 0003 — Stores & Organization Settings (V1)

- **Status:** Accepted
- **Date:** 2026-07-04
- **Phase:** 4 (Organizations & Stores)

## Context
V1 needs the first real tenant business entity and an organization settings
surface. Product direction simplified the model: **no Branch entity** — each
physical location is simply a Store owned by the Organization.

## Decisions
1. **Store is the single location entity.** `Organization ──< Store`. A Store owns
   (in later phases) cameras, AI events, alerts, reports. No `branch_id` on
   Store, so a `branches` table can be introduced later without altering
   existing rows.
2. **Stores are RLS-protected** (`ENABLE` + `FORCE`), policy keyed on
   `app.current_org` for both `USING` and `WITH CHECK`. Because the request sets
   the tenant context and inserts use the caller's org, `INSERT…RETURNING`
   passes. Repositories also filter by `organization_id` (defense-in-depth). A
   cross-tenant integration test proves Org B cannot read/modify Org A's stores.
3. **`require_membership` dependency** guarantees an onboarded user (has a
   membership) and yields the org context. Unauthenticated → 401; authenticated
   but not onboarded → 409 `onboarding_required`.
4. **Organization settings** extend the `organizations` table with logo_url,
   contact_email/phone, address, timezone, currency, alert_email_enabled.
   Read-only id + created_at are surfaced. The settings UI is structured so more
   sections can be added without restructuring.
5. **Object storage layer built now** (`app/core/storage.py`, boto3 → S3/MinIO).
   Bucket auto-created on startup (non-fatal if unreachable) with a public-read
   policy on `public/*`. Logo upload (`POST /organizations/current/logo`,
   multipart, ≤2 MB, image types only) uses it. This is reusable infra for
   camera snapshots, clips, and report PDFs in later phases.

## Consequences
- One clean location model; branches remain a future, non-breaking addition.
- The storage layer is available platform-wide from here on.
- Logo/object-storage flows require MinIO/S3 to fully verify (env-dependent).
