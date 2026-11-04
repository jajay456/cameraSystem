#!/bin/bash
set -euo pipefail
cd /Users/natthapong/Documents/GitHub/cameraSystem
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"
set -a
source .env
set +a
export TEST_API_KEY="${TEST_API_KEY:?TEST_API_KEY must be set in .env}"
exec npm run dev:emulator
