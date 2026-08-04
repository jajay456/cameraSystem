#!/usr/bin/env python3
"""
KROSS Dashboard (Windows) — a native window wrapper around the KROSS Replay
web dashboard, so it opens like a normal app instead of a browser tab.

NOT YET TESTED ON WINDOWS — written from macOS, same as the rest of
windows_deploy/. Please run this and report back any errors.

Unlike the macOS version (desktop_app/kross_dashboard.py), this does NOT
spawn the server itself: on Windows the server runs as the "KrossReplay"
Windows Service (see windows_deploy/install_service.bat), which auto-starts
at boot and restarts itself on crash — there's no need (and no clean way,
without admin rights) for this window to manage that process directly. It
just makes sure the service is running, starting it if needed, then shows
the dashboard. Closing the window does not stop the service.

Run directly with:
    pip install -r requirements.txt
    pip install -r windows_deploy/requirements.txt
    pip install pywebview
    python desktop_app/kross_dashboard_win.py

Or package as a standalone .exe with PyInstaller (must be built ON Windows —
PyInstaller cannot cross-build a Windows .exe from macOS):
    pyinstaller --onefile --windowed --name "KROSS Replay" kross_dashboard_win.py
The .exe will be in dist\\KROSS Replay.exe
"""

import subprocess
import time
import urllib.request

import webview

SERVICE_NAME = "KrossReplay"
DASHBOARD_URL = "http://localhost:8000"

LOADING_HTML = """
<html><body style="font-family:'Segoe UI',sans-serif;display:flex;
align-items:center;justify-content:center;height:100vh;margin:0;
background:#111;color:#eee;">
<p>Starting KROSS Replay server…</p>
</body></html>
"""


def _server_up() -> bool:
    try:
        with urllib.request.urlopen(f"{DASHBOARD_URL}/api/status", timeout=1) as r:
            return r.status == 200
    except Exception:
        return False


def _start_service() -> None:
    # Starting a Windows service needs admin rights. If this silently does
    # nothing (service stays down), either run KROSS Replay.exe "as
    # Administrator" once, or start the service manually first via
    # services.msc or `net start KrossReplay` in an elevated prompt.
    subprocess.run(["net", "start", SERVICE_NAME], capture_output=True)


def _wait_and_load(window) -> None:
    if not _server_up():
        _start_service()
        for _ in range(60):  # up to ~30s
            if _server_up():
                break
            time.sleep(0.5)
    window.load_url(DASHBOARD_URL)


def main():
    window = webview.create_window(
        "KROSS Replay",
        html=LOADING_HTML,
        width=1280,
        height=800,
        min_size=(800, 600),
    )
    webview.start(_wait_and_load, window)


if __name__ == "__main__":
    main()
