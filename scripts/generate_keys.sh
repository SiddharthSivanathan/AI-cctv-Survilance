#!/usr/bin/env bash
# Generate an RSA keypair for RS256 JWT signing.
# Keys are written to apps/api/keys/ (gitignored). Do NOT commit them.
set -euo pipefail

cd "$(dirname "$0")/.."
KEY_DIR="apps/api/keys"
mkdir -p "$KEY_DIR"

if [ -f "$KEY_DIR/jwt_private.pem" ]; then
  echo "Keys already exist at $KEY_DIR — refusing to overwrite."
  exit 0
fi

echo "==> Generating RSA private key"
openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:2048 -out "$KEY_DIR/jwt_private.pem"

echo "==> Extracting public key"
openssl rsa -pubout -in "$KEY_DIR/jwt_private.pem" -out "$KEY_DIR/jwt_public.pem"

chmod 600 "$KEY_DIR/jwt_private.pem"
echo "==> Done. Keys written to $KEY_DIR (gitignored)."
