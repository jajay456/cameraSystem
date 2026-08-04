#!/usr/bin/env python3
"""
KROSS Control (Windows) — a system tray icon to start/stop/check the KROSS
Replay server without needing a terminal. The server itself auto-starts via
a Windows Scheduled Task (see install_task.ps1); this tray app is just a
friendly on/off switch and status light for it.

NOT YET TESTED ON WINDOWS — written from macOS. Please run this and report
back any errors so they can be fixed.

Run directly with:
    pip install -r requirements.txt
    python kross_control_win.py
Or package as a standalone .exe with PyInstaller (must be run ON Windows —
PyInstaller cannot cross-build a Windows .exe from macOS):
    pyinstaller --onefile --windowed --name "KROSS Control" kross_control_win.py
"""

import json
import subprocess
import threading
import time
import urllib.request
import webbrowser
from pathlib import Path

import pystray
from PIL import Image, ImageDraw

SERVICE_NAME = "KrossReplay"
LOG_PATH = Path(__file__).resolve().parent.parent / "logs" / "server.log"
DASHBOARD_URL = "http://localhost:8000"


def server_status() -> dict | None:
    try:
        with urllib.request.urlopen(f"{DASHBOARD_URL}/api/status", timeout=2) as r:
            return json.load(r)
    except Exception:
        return None


def make_icon(color: str) -> Image.Image:
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse((8, 8, 56, 56), fill=color)
    return img


ICON_GREEN = make_icon("#3fb950")
ICON_RED = make_icon("#e5484d")


def open_dashboard(icon, item):
    webbrowser.open(DASHBOARD_URL)


def view_logs(icon, item):
    subprocess.run(["notepad.exe", str(LOG_PATH)])


def start_service(icon, item):
    # controlling a Windows service needs admin rights — run this tray app
    # "as Administrator" if these buttons don't seem to do anything
    subprocess.run(["net", "start", SERVICE_NAME], capture_output=True)


def stop_service(icon, item):
    subprocess.run(["net", "stop", SERVICE_NAME], capture_output=True)


def quit_app(icon, item):
    icon.stop()


def build_menu(status_text: str) -> pystray.Menu:
    return pystray.Menu(
        pystray.MenuItem(status_text, None, enabled=False),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Open Dashboard", open_dashboard),
        pystray.MenuItem("View Logs", view_logs),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Start Service", start_service),
        pystray.MenuItem("Stop Service", stop_service),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Quit KROSS Control", quit_app),
    )


def refresh_loop(icon: pystray.Icon):
    while True:
        info = server_status()
        if info:
            branch = info.get("branchName", "?")
            cams = info.get("cameras", 0)
            icon.icon = ICON_GREEN
            icon.title = f"KROSS — {branch} ({cams} cams)"
            icon.menu = build_menu(f"● Running — {branch} ({cams} cams)")
        else:
            icon.icon = ICON_RED
            icon.title = "KROSS — not running"
            icon.menu = build_menu("○ Not running")
        time.sleep(5)


def main():
    icon = pystray.Icon("kross_control", ICON_RED, "KROSS Control", build_menu("checking…"))
    threading.Thread(target=refresh_loop, args=(icon,), daemon=True).start()
    icon.run()


if __name__ == "__main__":
    main()
