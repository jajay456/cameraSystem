#!/bin/bash
set -euo pipefail

ROOT="/Users/natthapong/Documents/GitHub/cameraSystem"
PLIST_DIR="$HOME/Library/LaunchAgents"
UID_VALUE="$(id -u)"
mkdir -p "$PLIST_DIR" "$ROOT/logs"

for label in com.kross.emulator com.kross.camera com.kross.gateway com.kross.tunnel; do
  launchctl bootout "gui/$UID_VALUE/$label" 2>/dev/null || true
done

write_plist() {
  local label="$1"
  local script="$2"
  cat > "$PLIST_DIR/$label.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>$label</string>
  <key>ProgramArguments</key><array><string>$ROOT/$script</string></array>
  <key>WorkingDirectory</key><string>$ROOT</string>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>ThrottleInterval</key><integer>10</integer>
  <key>StandardOutPath</key><string>$ROOT/logs/$label.log</string>
  <key>StandardErrorPath</key><string>$ROOT/logs/$label.log</string>
</dict></plist>
PLIST
  launchctl bootstrap "gui/$UID_VALUE" "$PLIST_DIR/$label.plist"
}

for label_and_script in \
  "com.kross.emulator scripts/run-emulator.sh" \
  "com.kross.camera scripts/run-camera.sh" \
  "com.kross.gateway scripts/run-gateway.sh" \
  "com.kross.tunnel scripts/run-tunnel.sh"; do
  read -r label script <<< "$label_and_script"
  write_plist "$label" "$script"
done

echo "Installed local services. Check: $ROOT/scripts/local-services.sh status"
