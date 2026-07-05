# Security Policy

## Reporting a vulnerability
Email **security@visionops.ai** with details and reproduction steps. Please do
not open public issues for security reports. We aim to acknowledge within 3
business days.

## Security posture (V1)

### Tenant isolation
- **PostgreSQL Row-Level Security** (`FORCE ROW LEVEL SECURITY`) on every
  tenant-scoped table (stores, cameras, zones, rules, camera_events, alerts,
  camera_metrics, notifications, reports, audit_logs). The per-request
  `app.current_org` context is derived from the validated JWT — a code bug
  cannot leak data across organizations. Cross-tenant isolation is regression-tested.

### Authentication & authorization
- **Argon2id** password hashing.
- **RS256 JWT** access tokens (15 min) + **rotating refresh tokens** with reuse
  detection (family revocation). Refresh-token hashes only are stored.
- Email verification (24h) gates login. RBAC seam (`require_role`) in place.
- WebSocket authenticated by JWT; subscribes only to the caller's org channel.

### Secrets & data protection
- **Camera RTSP passwords encrypted at rest** (Fernet); decrypted only in-process
  to connect; never returned by the API or written to logs.
- Secrets are environment-provided; `.env` is gitignored (`chmod 600` in prod).
- JWT signing keys are files mounted read-only, never committed.

### Transport & headers
- **HTTPS everywhere** (Let's Encrypt) with HSTS in production.
- Security headers (`X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`,
  `Referrer-Policy`, CSP-friendly) at both the API and Nginx.
- CORS restricted to the configured origin.

### Abuse prevention
- **Redis-backed rate limiting** on sensitive auth endpoints (login, register,
  password reset).
- Internal service endpoints require a shared internal token.

### Input handling
- Pydantic validation at every API boundary; parameterized queries only
  (SQLAlchemy) — no string-built SQL. No user-supplied code execution (the rule
  engine evaluates a fixed set of typed rule types).

### Auditing
- Mutating and security-relevant actions are recorded in `audit_logs`
  (actor, action, resource, ip, user-agent).

## Deferred to V2
Per-user notification routing, SSO/SAML, MFA, secrets-manager integration
(currently env-based), and a formal WAF. The architecture accommodates these
without major refactoring.
