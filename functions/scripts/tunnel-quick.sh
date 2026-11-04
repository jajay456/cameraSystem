#!/usr/bin/env bash
set -euo pipefail
: "${API_KEY:?Set API_KEY to the test API key}"
PORT="${API_PORT:-8001}"
echo "Exposing functions API only on localhost:${PORT} (not frontend or emulator UI)."
echo "Partner header: x-api-key: ${API_KEY}"
exec cloudflared tunnel --url "http://127.0.0.1:${PORT}"
