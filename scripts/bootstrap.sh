#!/usr/bin/env bash
# Bootstrap the VisionOps AI dev environment.
set -euo pipefail

cd "$(dirname "$0")/.."

echo "==> Checking prerequisites"
command -v pnpm >/dev/null 2>&1 || { echo "pnpm not found. Run: corepack enable"; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "python3 not found"; exit 1; }

echo "==> Creating .env from example (if missing)"
[ -f .env ] || cp .env.example .env

echo "==> Installing JS workspace dependencies"
pnpm install

echo "==> Installing Python app dependencies (editable)"
for app in api ai-engine worker; do
  echo "    - apps/$app"
  ( cd "apps/$app" && python3 -m pip install -e ".[dev]" >/dev/null )
done

echo "==> Done. Next:"
echo "    docker compose up --build     # full stack"
echo "    pnpm dev                       # JS apps in dev"
