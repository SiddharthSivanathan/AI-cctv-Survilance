#!/usr/bin/env bash
# Deploy / update VisionOps AI on the production VPS.
# Pulls latest code (if a git repo), rebuilds, runs migrations, restarts.
#   bash scripts/deploy.sh
set -euo pipefail

cd "$(dirname "$0")/.."
COMPOSE="docker compose -f docker-compose.prod.yml"

if [ -d .git ]; then
  echo "==> Pulling latest code"
  git pull --ff-only
fi

echo "==> Building images"
$COMPOSE build

echo "==> Running database migrations"
$COMPOSE run --rm migrate

echo "==> Restarting services"
$COMPOSE up -d

echo "==> Pruning old images"
docker image prune -f

echo "==> Deploy complete. Status:"
$COMPOSE ps
