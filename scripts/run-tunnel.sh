#!/bin/bash
set -euo pipefail
cd /Users/natthapong/Documents/GitHub/cameraSystem
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"
set -a
source .env
set +a
: "${CLOUDFLARE_TUNNEL_NAME:?CLOUDFLARE_TUNNEL_NAME must be set in .env}"
exec cloudflared tunnel run "$CLOUDFLARE_TUNNEL_NAME"
