#!/usr/bin/env bash
# Back up the VisionOps AI database + object storage to ./backups/<timestamp>.
#   bash scripts/backup.sh
set -euo pipefail

cd "$(dirname "$0")/.."
COMPOSE="docker compose -f docker-compose.prod.yml"
TS="$(date +%Y%m%d-%H%M%S)"
DEST="backups/${TS}"
mkdir -p "${DEST}"

# Load DB credentials from .env
set -a; . ./.env; set +a

echo "==> Dumping PostgreSQL"
$COMPOSE exec -T postgres pg_dump -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" \
  | gzip > "${DEST}/postgres.sql.gz"

echo "==> Archiving object storage (MinIO)"
$COMPOSE exec -T minio sh -c 'tar -czf - -C /data .' > "${DEST}/minio.tar.gz" || \
  echo "   (skipped MinIO archive — check volume)"

echo "==> Backup complete: ${DEST}"
ls -lh "${DEST}"
