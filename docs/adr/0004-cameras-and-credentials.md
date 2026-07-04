# ADR 0004 — Cameras & Credential Handling (V1)

- **Status:** Accepted
- **Date:** 2026-07-04
- **Phase:** 5 (Camera Management & RTSP Integration)

## Context
Cameras carry sensitive RTSP credentials and require connection validation.
Product direction: real "Test Connection" (connect, authenticate, capture a
frame, detect resolution/fps/codec), never expose passwords, and a 60-second
health monitor that flags cameras offline for >5 minutes.

## Decisions
1. **Cameras belong to Stores** and are RLS-protected (`ENABLE`+`FORCE`). The
   service also verifies the target store belongs to the caller's org, closing
   the gap where an FK check bypasses RLS.
2. **Credentials encrypted at rest** via Fernet (`app/core/crypto.py`). The RTSP
   password is stored as ciphertext (`password_encrypted`) and decrypted only
   in-process to open a connection. **Responses never include the password**;
   the `rtsp_url` is stored with userinfo stripped and returned alongside
   `username` + `has_credentials`. On edit, a blank password keeps the stored
   one. Passwords never appear in logs, errors, or audit metadata.
3. **RTSP validation via ffmpeg/ffprobe** (`app/core/rtsp.py`): validate URL →
   connect → authenticate → capture one frame → thumbnail to object storage →
   detect resolution/fps/codec. Result maps to a status enum
   (connected/auth_failed/unreachable/invalid_url/timeout/error). ffmpeg is
   added to the API image. *This intentionally puts light, bounded video work
   in the control plane; continuous decoding/streaming remains the gateway's
   job (Phase 6).*
4. **Health monitoring** = Celery Beat (worker) every 60s → calls an
   **internal, token-guarded** API endpoint (`/internal/cameras/health-sweep`).
   The sweep iterates orgs (setting RLS context per org), re-probes enabled
   cameras, updates status/last_seen, and — when offline beyond the threshold —
   records a `camera.offline` event. Keeping all DB/credential logic in the API
   avoids duplicating models into the worker.
5. **Offline "alerts" are events for now.** The full Alert entity + email/SMS
   delivery lands in Phase 10; Phase 5 records the offline condition on the
   audit/event trail so nothing is lost.

## Trade-offs / deferrals
- ONVIF discovery, network scanning, grouping, multi-stream, recording,
  playback, PTZ, motion detection, edge AI — explicitly out of V1; the schema
  and services leave room for them.
- The health sweep probes synchronously per camera; fine for V1 volumes. At
  scale this moves to the gateway/inference plane.
- ffmpeg RTSP capture cannot be verified without a live camera; built
  correct-by-construction and confirmed against real hardware.
