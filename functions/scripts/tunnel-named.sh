#!/usr/bin/env bash
set -euo pipefail
: "${CLOUDFLARE_TUNNEL_NAME:?Set CLOUDFLARE_TUNNEL_NAME}"
: "${CLOUDFLARE_HOSTNAME:?Set CLOUDFLARE_HOSTNAME}"
PORT="${API_PORT:-5001}"
echo "Exposing functions API only on localhost:${PORT} at https://${CLOUDFLARE_HOSTNAME}."
echo "Partner header: x-api-key: ${API_KEY:?Set API_KEY to the test API key}"
exec cloudflared tunnel --name "${CLOUDFLARE_TUNNEL_NAME}" \
  --hostname "${CLOUDFLARE_HOSTNAME}" --url "http://127.0.0.1:${PORT}"
