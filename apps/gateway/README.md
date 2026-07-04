# @visionops/gateway

VisionOps AI media edge — Go. Authorizes browser WebRTC (WHEP) playback with
backend-issued short-lived tokens and reverse-proxies to an internal MediaMTX
media server. **MediaMTX is never exposed directly.**

## Responsibility
- Provision on-demand MediaMTX paths (RTSP source) when the API requests a live
  stream (`POST /internal/provision`, internal-token guarded).
- Authorize and proxy WHEP signaling (`POST /whep/{camera_id}`): verify the
  HMAC playback token issued by FastAPI, then forward the SDP offer/answer to
  MediaMTX. Rewrites the WHEP resource `Location` so cleanup routes back through
  the gateway (internal URLs never leak).

WebRTC **media** (ICE/RTP) flows directly between the browser and MediaMTX's
UDP port — only signaling passes through the gateway.

## Structure
```
cmd/gateway/main.go          entrypoint
internal/config              env configuration
internal/token               HS256 playback-token verification (stdlib only)
internal/mediamtx            MediaMTX control API client (provision paths)
internal/server              HTTP handlers (health, provision, WHEP proxy)
```

## Develop
```bash
go run ./cmd/gateway     # :8080
go test ./...
gofmt -l . && go vet ./...
```

No external Go dependencies — builds offline.
