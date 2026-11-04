#!/bin/bash
set -euo pipefail
cd /Users/natthapong/Documents/GitHub/cameraSystem
set -a
source .env
set +a
export FIRESTORE_EMULATOR_HOST="${FIRESTORE_EMULATOR_HOST:-127.0.0.1:8080}"
export GCLOUD_PROJECT="${GCLOUD_PROJECT:-kross-highlight-local}"
exec .venv/bin/python -m app.main
