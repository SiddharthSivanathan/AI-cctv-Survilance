# ADR 0005 — Live Streaming (MediaMTX + Go gateway)

- **Status:** Accepted
- **Date:** 2026-07-04
- **Phase:** 6 (Live Streaming Service)

## Context
V1 needs low-latency (<2s) live camera viewing in the browser, multiple
simultaneous streams, auto-reconnect, and status states — without building a
media server. Product direction: **WebRTC only**, MediaMTX as the media plane,
FastAPI as the source of truth for authorization via short-lived tokens.

## Decisions
1. **MediaMTX is the media plane** (RTSP→WebRTC). We do **not** build a custom
   WebRTC server/SFU. MediaMTX is kept internal and is replaceable.
2. **Go gateway = authorizing edge.** It provisions on-demand MediaMTX paths and
   reverse-proxies WHEP **signaling** after verifying a backend-issued token.
   MediaMTX is never exposed; internal URLs never leak (the WHEP `Location` is
   rewritten to route cleanup back through the gateway). The gateway uses the Go
   **standard library only** (hand-rolled HS256 verify) so it builds offline.
3. **FastAPI issues short-lived HMAC playback tokens.** `POST /cameras/{id}/live`
   authorizes the tenant (camera must belong to the org), decrypts the RTSP
   source, asks the gateway to provision, and returns `{ whep_url, token,
   expires_at }`. The gateway verifies the token (shared HMAC secret) and checks
   the `path` claim matches the requested camera. Tokens are ~60s TTL.
4. **On-demand streaming.** MediaMTX only pulls the camera RTSP when a viewer
   connects (`sourceOnDemand`), and stops when idle — cost-efficient.
5. **Media path.** WebRTC media (ICE/RTP) flows **directly** between browser and
   MediaMTX (UDP :8189, exposed + advertised via `webrtcAdditionalHosts`). Only
   signaling passes through the gateway. Production needs the public host/IP and
   likely a TURN server; documented.
6. **Frontend** uses a minimal WHEP client (`connectWhep`) + a `LivePlayer`
   component with idle/connecting/live/reconnecting/error states and automatic
   reconnect with backoff. A live grid supports 1/4/9 layouts.

## Deferrals (per product)
Recording, playback, storage, HLS/DASH/RTMP, PTZ, adaptive bitrate, GPU
transcode, multi-quality — none in V1. The AI frame-ingestion pipe (ffmpeg
sampler → Redis) is **Phase 7**, built with the detector.

## Verification note
This phase requires Go, Docker, MediaMTX, ffmpeg, and a real RTSP camera to
verify end-to-end. Token/routing logic is unit-tested; live playback must be
confirmed on real infrastructure.
