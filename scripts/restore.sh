#!/usr/bin/env bash
# Restore the VisionOps AI database from a backup directory.
#   bash scripts/restore.sh backups/20260705-120000
set -euo pipefail

cd "$(dirname "$0")/.."
SRC="${1:?Usage: restore.sh <backup-dir>}"
COMPOSE="docker compose -f docker-compose.prod.yml"
set -a; . ./.env; set +a

if [ ! -f "${SRC}/postgres.sql.gz" ]; then
  echo "No postgres.sql.gz in ${SRC}"; exit 1
fi

echo "!! This will OVERWRITE the current database. Ctrl-C to abort."
sleep 5

echo "==> Restoring PostgreSQL"
gunzip -c "${SRC}/postgres.sql.gz" | \
  $COMPOSE exec -T postgres psql -U "${POSTGRES_USER}" -d "${POSTGRES_DB}"

echo "==> Restore complete. Run migrations if needed:"
echo "    $COMPOSE run --rm migrate"
