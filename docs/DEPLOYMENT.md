# VisionOps AI — Production Deployment (single VPS)

A production install on one Ubuntu 24.04 VPS using Docker Compose, Nginx, and
Let's Encrypt. Designed to migrate to Kubernetes later without app changes.

## 1. Server requirements
- **Ubuntu 24.04 LTS**, x86_64.
- **4 vCPU / 8 GB RAM** minimum (more for many cameras / AI). A GPU is recommended
  for the AI engine at scale but not required (CPU inference works at low FPS).
- **50 GB+** disk (Postgres, MinIO objects, model cache).
- Open ports: **80, 443 (TCP)** and **8189 (UDP)** for WebRTC media.
- A **domain name** pointing at the server.

## 2. DNS setup
Create an **A record** for your domain (e.g. `cctv.example.com`) → the server's
public IP. Verify: `dig +short cctv.example.com`.

## 3. Install Docker
```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker "$USER" && newgrp docker
docker compose version   # confirm Compose v2
```

## 4. Get the code + configure
```bash
git clone <your-repo> visionops && cd visionops
cp .env.production.example .env
# Edit .env: set DOMAIN, all CHANGE_ME secrets (openssl rand -hex 32), SMTP, etc.
chmod 600 .env
bash scripts/generate_keys.sh    # RS256 JWT keys → apps/api/keys (gitignored)
```

## 5. SSL certificate (Let's Encrypt)
```bash
DOMAIN=cctv.example.com EMAIL=you@example.com bash scripts/init-letsencrypt.sh
```
This issues a real certificate and reloads Nginx. Certificates auto-renew via the
`certbot` service.

## 6. Start the stack
```bash
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml run --rm migrate   # apply DB migrations
```
Create the MinIO bucket (first run auto-creates it via the API on startup).

## 7. Verify
- `https://cctv.example.com` → the app loads.
- `https://cctv.example.com/api/health` → `{"status":"ok"}`.
- `docker compose -f docker-compose.prod.yml ps` → all services `Up`/healthy.

## 8. Monitoring
- **Logs** (structured JSON): `docker compose -f docker-compose.prod.yml logs -f api`.
- **Health**: `GET /api/health` (liveness), `GET /api/ready` (DB + Redis).
- **Resource use**: `docker stats`.

## 9. Updating
```bash
bash scripts/deploy.sh     # pull, rebuild, migrate, restart, prune
```

## 10. Backups & restore
```bash
bash scripts/backup.sh                     # → backups/<timestamp>/
bash scripts/restore.sh backups/<ts>       # restore Postgres
```
Schedule `scripts/backup.sh` via cron (e.g. daily) and copy `backups/` off-server.

## 11. Troubleshooting
| Symptom | Check |
|---|---|
| 502 from Nginx | `docker compose ... logs web api`; are they healthy? |
| Cert errors | Re-run `init-letsencrypt.sh`; check DNS points here. |
| WebRTC live view black | UDP **8189** open in the firewall; `mediamtx` logs. |
| Camera won't connect | RTSP URL/creds; the camera network is reachable from the VPS. |
| AI events not firing | `ai-engine` logs; ffmpeg present; rules + zones configured. |
| Emails not sent | SMTP_* set; `worker` logs (`email_sent`/`email_logged`). |

## Notes
- Only Nginx (80/443) and MediaMTX media (8189/udp) are exposed; all other
  services are internal to the Docker network.
- `restart: unless-stopped` + `stop_grace_period` give auto-restart + graceful
  shutdown. Postgres, Redis, MinIO, MediaMTX, and model cache use named volumes.
