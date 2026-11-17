#!/bin/bash
set -euo pipefail
cd /Users/natthapong/Documents/GitHub/cameraSystem
set -a
source .env
set +a
# Writes go to the real Firestore (service account in .env) by default.
# Set USE_EMULATOR=1 to write to the local emulator instead.
if [ "${USE_EMULATOR:-0}" = "1" ]; then
  export FIRESTORE_EMULATOR_HOST="${FIRESTORE_EMULATOR_HOST:-127.0.0.1:8080}"
  export GCLOUD_PROJECT="${GCLOUD_PROJECT:-kross-highlight-local}"
else
  unset FIRESTORE_EMULATOR_HOST
fi
exec .venv/bin/python -m app.main
