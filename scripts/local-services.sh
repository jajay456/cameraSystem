#!/bin/bash
set -euo pipefail
ROOT="/Users/natthapong/Documents/GitHub/cameraSystem"
PLIST_DIR="$HOME/Library/LaunchAgents"
UID_VALUE="$(id -u)"
case "${1:-status}" in
  start) exec "$ROOT/scripts/install-local-services.sh" ;;
  stop)
    for label in com.kross.tunnel com.kross.gateway com.kross.camera com.kross.emulator; do
      launchctl bootout "gui/$UID_VALUE/$label" 2>/dev/null || true
    done
    ;;
  restart)
    "$ROOT/scripts/local-services.sh" stop
    exec "$ROOT/scripts/local-services.sh" start
    ;;
  status)
    launchctl print "gui/$UID_VALUE/com.kross.emulator" >/dev/null 2>&1 && echo "emulator: running" || echo "emulator: stopped"
    launchctl print "gui/$UID_VALUE/com.kross.camera" >/dev/null 2>&1 && echo "camera: running" || echo "camera: stopped"
    launchctl print "gui/$UID_VALUE/com.kross.gateway" >/dev/null 2>&1 && echo "gateway: running" || echo "gateway: stopped"
    launchctl print "gui/$UID_VALUE/com.kross.tunnel" >/dev/null 2>&1 && echo "tunnel: running" || echo "tunnel: stopped"
    ;;
  logs) exec tail -f "$ROOT/logs/com.kross.camera.log" "$ROOT/logs/com.kross.gateway.log" "$ROOT/logs/com.kross.tunnel.log" ;;
  *) echo "Usage: $0 {start|stop|restart|status|logs}" >&2; exit 2 ;;
esac
