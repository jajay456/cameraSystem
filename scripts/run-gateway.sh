#!/bin/bash
set -euo pipefail
cd /Users/natthapong/Documents/GitHub/cameraSystem
set -a
source .env
set +a
export API_KEY="${TEST_API_KEY:?TEST_API_KEY must be set in .env}"
export API_PORT=8001
export UPSTREAM_PORT=8000
exec .venv/bin/python functions/scripts/api-gateway.py
