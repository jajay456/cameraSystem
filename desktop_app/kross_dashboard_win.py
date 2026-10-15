#!/usr/bin/env python3
"""
KROSS Dashboard (Windows) — a native window wrapper around the KROSS Replay
web dashboard, so it opens like a normal app instead of a browser tab.

If the server is already running (e.g. as the "KrossReplay" Windows Service
from windows_deploy/install_service.bat), this just shows it. Otherwise it
tries to start that service, and if the service isn't installed it starts
the server itself — hidden, no console window — and stops the copy it
started when the window is closed (same as the macOS version,
desktop_app/kross_dashboard.py).

Run directly (no console window) with:
    pip install pywebview
    .venv\\Scripts\\pythonw.exe desktop_app\\kross_dashboard_win.py
A Desktop shortcut pointing at exactly that is the simplest launcher.

Or package as a standalone .exe with PyInstaller:
    pyinstaller --onefile --windowed --name "KROSS Replay" kross_dashboard_win.py
The .exe will be in dist\\KROSS Replay.exe. Note the .exe locates the
project relative to itself (desktop_app\\dist\\ -> project root), so leave it
there and put a shortcut to it on the Desktop rather than moving it.
"""

import ctypes
import os
import subprocess
import sys
import time
import urllib.request
import winreg
from pathlib import Path

import webview

SERVICE_NAME = "KrossReplay"
DASHBOARD_URL = "http://localhost:8000"

if getattr(sys, "frozen", False):
    # PyInstaller .exe in desktop_app\dist\
    PROJECT_DIR = Path(sys.executable).resolve().parent.parent.parent
else:
    PROJECT_DIR = Path(__file__).resolve().parent.parent
PYTHON = str(PROJECT_DIR / ".venv" / "Scripts" / "python.exe")
ICON = str(PROJECT_DIR / "assets" / "icon" / "KROSSReplay.ico")

LOADING_HTML = """
<html><body style="font-family:'Segoe UI',sans-serif;display:flex;
align-items:center;justify-content:center;height:100vh;margin:0;
background:#111;color:#eee;">
<p>Starting KROSS Replay server…</p>
</body></html>
"""

_server_proc = None  # only set if THIS app started the server


def _server_up() -> bool:
    try:
        with urllib.request.urlopen(f"{DASHBOARD_URL}/api/status", timeout=1) as r:
            return r.status == 200
    except Exception:
        return False


def _wait_for_server(seconds: float) -> bool:
    for _ in range(int(seconds * 2)):
        if _server_up():
            return True
        time.sleep(0.5)
    return False


def _registry_path() -> str:
    """PATH as currently saved in the registry (system + user). A shortcut
    launched from Explorer can inherit a stale PATH from before ffmpeg /
    mediamtx were installed — app.main runs both by bare name, and without
    them the cameras just show offline with no error surfaced."""
    parts = []
    for root, key in (
        (winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment"),
        (winreg.HKEY_CURRENT_USER, r"Environment"),
    ):
        try:
            with winreg.OpenKey(root, key) as k:
                parts.append(os.path.expandvars(winreg.QueryValueEx(k, "Path")[0]))
        except OSError:
            pass
    return ";".join(parts)


def _clean_env() -> dict:
    # Drop PYTHONHOME/PYTHONPATH (set by a frozen .exe) so the venv python
    # resolves its own site-packages.
    env = {k: v for k, v in os.environ.items() if not k.startswith("PYTHON")}
    env["PATH"] = _registry_path() + ";" + env.get("PATH", "")
    return env


def _start_service() -> bool:
    # Only works if the service is installed and this has admin rights;
    # otherwise it fails quietly and we fall back to _start_server().
    r = subprocess.run(
        ["net", "start", SERVICE_NAME],
        capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW,
    )
    return r.returncode == 0


def _start_server() -> None:
    global _server_proc
    _server_proc = subprocess.Popen(
        [PYTHON, "-m", "app.main"], cwd=PROJECT_DIR, env=_clean_env(),
        creationflags=subprocess.CREATE_NO_WINDOW,
    )


def _wait_and_load(window) -> None:
    if not _server_up():
        if not (_start_service() and _wait_for_server(30)):
            _start_server()
            _wait_for_server(30)
    window.load_url(DASHBOARD_URL)


def _on_closed() -> None:
    if _server_proc and _server_proc.poll() is None:
        # /T: also stop the ffmpeg recorders and MediaMTX the server spawned.
        subprocess.run(
            ["taskkill", "/PID", str(_server_proc.pid), "/T", "/F"],
            capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW,
        )


def main():
    # Own taskbar identity, so Windows shows the KROSS icon instead of
    # grouping this window under pythonw.exe's Python logo.
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("Kross.Replay.Dashboard")
    window = webview.create_window(
        "KROSS Replay",
        html=LOADING_HTML,
        width=1280,
        height=800,
        min_size=(800, 600),
    )
    window.events.closed += _on_closed
    webview.start(_wait_and_load, window, icon=ICON)


if __name__ == "__main__":
    main()
