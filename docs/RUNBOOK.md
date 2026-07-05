# VisionOps AI — Operations Runbook

Quick reference for running the production stack. All commands assume the repo
root and `docker compose -f docker-compose.prod.yml` (aliased `dc` below).

```bash
alias dc='docker compose -f docker-compose.prod.yml'
```

## Service map
| Service | Role | Exposed |
|---|---|---|
| nginx | TLS reverse proxy | 80, 443 |
| web | Next.js frontend | internal |
| api | FastAPI control plane | internal |
| gateway | WebRTC authz proxy | internal |
| mediamtx | media server | 8189/udp |
| worker | Celery (health, reports, email) | internal |
| ai-engine | sampler + YOLO + rules | internal |
| postgres / redis / minio | data / cache / objects | internal |

## Common tasks
- **Status:** `dc ps`
- **Logs:** `dc logs -f api` (or any service)
- **Restart one service:** `dc restart api`
- **Restart all:** `dc restart`
- **Stop:** `dc down` (keeps volumes) · **Stop + wipe data:** `dc down -v` ⚠️
- **Run migrations:** `dc run --rm migrate`
- **Shell in a container:** `dc exec api sh`
- **DB console:** `dc exec postgres psql -U visionops -d visionops`

## Incidents
| Incident | Action |
|---|---|
| High CPU on ai-engine | Reduce per-camera `sample_fps`; consider a GPU host. |
| Postgres disk filling | Check `camera_events`/`camera_metrics` growth; add a retention job. |
| Certbot renewal failed | `dc run --rm certbot renew --dry-run`; check port 80 reachable. |
| Redis memory | Streams are capped (MAXLEN); check `dc exec redis redis-cli info memory`. |
| Stuck deploy | `dc build --no-cache <svc>` then `dc up -d`. |

## Scaling (single VPS limits)
- The AI engine and worker are stateless — for more cameras, move to a bigger
  box or (V2) split ai-engine onto a GPU node and adopt Kubernetes.
- Detection Redis streams are capped; a slow detector drops frames rather than
  backing up.

## Backups
- `bash scripts/backup.sh` (cron daily recommended) → `backups/<ts>/`.
- Copy backups off-server (e.g. `rclone`/`scp`) — a VPS backup on the same disk
  is not disaster recovery.
