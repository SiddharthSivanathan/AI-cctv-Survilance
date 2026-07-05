#!/usr/bin/env bash
# Bootstrap Let's Encrypt certificates for the production Nginx.
# Creates a temporary self-signed cert so Nginx can start, then requests the
# real certificate from Let's Encrypt and reloads.
#
#   DOMAIN=cctv.example.com EMAIL=you@example.com bash scripts/init-letsencrypt.sh
set -euo pipefail

: "${DOMAIN:?Set DOMAIN=your.domain}"
: "${EMAIL:?Set EMAIL=you@example.com}"
COMPOSE="docker compose -f docker-compose.prod.yml"
CERT_PATH="/etc/letsencrypt/live/${DOMAIN}"

echo "==> Creating dummy certificate so Nginx can start"
$COMPOSE run --rm --entrypoint "\
  sh -c 'mkdir -p ${CERT_PATH} && \
  openssl req -x509 -nodes -newkey rsa:2048 -days 1 \
    -keyout ${CERT_PATH}/privkey.pem -out ${CERT_PATH}/fullchain.pem \
    -subj /CN=localhost'" certbot

echo "==> Starting Nginx"
$COMPOSE up -d nginx

echo "==> Requesting the real certificate"
$COMPOSE run --rm --entrypoint "\
  certbot certonly --webroot -w /var/www/certbot \
    --email ${EMAIL} -d ${DOMAIN} --agree-tos --no-eff-email --force-renewal" certbot

echo "==> Reloading Nginx"
$COMPOSE exec nginx nginx -s reload

echo "==> Done. HTTPS is live for https://${DOMAIN}"
