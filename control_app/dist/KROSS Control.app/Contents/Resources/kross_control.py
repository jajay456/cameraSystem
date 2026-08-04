#!/usr/bin/env python3
"""
KROSS Control — a menu bar icon to start/stop/check the KROSS Replay
server without needing Terminal. The server itself keeps running via the
com.kross.replay launchd service (RunAtLoad + KeepAlive); this app is just
a friendly on/off switch and status light for it.
"""

import subprocess
import urllib.request
import webbrowser
from pathlib import Path

import rumps

PROJECT_DIR = Path("/Users/natthapong/Documents/camera_system")
PLIST_PATH = Path.home() / "Library/LaunchAgents/com.kross.replay.plist"
LOG_PATH = PROJECT_DIR / "logs/server.log"
DASHBOARD_URL = "http://localhost:8000"
UID = str(subprocess.run(["id", "-u"], capture_output=True, text=True).stdout.strip())


def server_status() -> dict | None:
    try:
        with urllib.request.urlopen(f"{DASHBOARD_URL}/api/status", timeout=2) as r:
            import json
            return json.load(r)
    except Exception:
        return None


class KrossControlApp(rumps.App):
    def __init__(self):
        super().__init__("KROSS", icon=None, quit_button=None)
        self.status_item = rumps.MenuItem("checking…")
        self.menu = [
            self.status_item,
            None,
            rumps.MenuItem("Open Dashboard", callback=self.open_dashboard),
            rumps.MenuItem("View Logs", callback=self.view_logs),
            None,
            rumps.MenuItem("Start Service", callback=self.start_service),
            rumps.MenuItem("Stop Service", callback=self.stop_service),
            None,
            rumps.MenuItem("Quit KROSS Control", callback=self.quit_app),
        ]
        self.refresh(None)

    @rumps.timer(5)
    def refresh(self, _):
        info = server_status()
        if info:
            self.title = "🟢 KROSS"
            branch = info.get("branchName", "?")
            cams = info.get("cameras", 0)
            self.status_item.title = f"● Running — {branch} ({cams} cams)"
        else:
            self.title = "🔴 KROSS"
            self.status_item.title = "○ Not running"

    def open_dashboard(self, _):
        webbrowser.open(DASHBOARD_URL)

    def view_logs(self, _):
        subprocess.run(["open", "-a", "Console", str(LOG_PATH)])

    def start_service(self, _):
        subprocess.run(["launchctl", "bootstrap", f"gui/{UID}", str(PLIST_PATH)])
        rumps.notification("KROSS Control", "", "Service starting…")
        self.refresh(None)

    def stop_service(self, _):
        subprocess.run(["launchctl", "bootout", f"gui/{UID}", str(PLIST_PATH)])
        rumps.notification("KROSS Control", "", "Service stopped")
        self.refresh(None)

    def quit_app(self, _):
        rumps.quit_application()


if __name__ == "__main__":
    KrossControlApp().run()
