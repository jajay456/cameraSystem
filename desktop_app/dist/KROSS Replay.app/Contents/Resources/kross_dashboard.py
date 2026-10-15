#!/usr/bin/env python3
"""
KROSS Dashboard — a native window wrapper around the KROSS Replay web
dashboard, so it opens like a normal Mac app instead of a browser tab.

If the server isn't already running (e.g. via the com.kross.replay launchd
service), this starts it itself — nothing to type in Terminal — and stops
the copy it started when the window is closed.
"""

import os
import subprocess
import time
import urllib.request
from pathlib import Path

import webview

# Hardcoded rather than derived from __file__: once this script is bundled
# into KROSS Replay.app (py2app), __file__ points inside the frozen bundle,
# not the real project checkout — same reason control_app/kross_control.py
# hardcodes this path.
PROJECT_DIR = Path("/Users/natthapong/Documents/camera_system")
PYTHON = str(PROJECT_DIR / ".venv" / "bin" / "python")
DASHBOARD_URL = "http://localhost:8000"

LOADING_HTML = """
<html><body style="font-family:-apple-system,sans-serif;display:flex;
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


def _clean_env() -> dict:
    """Once bundled into KROSS Replay.app, py2app sets PYTHONHOME /
    PYTHONPATH so the frozen app's own interpreter finds its libs — but
    those same vars leak into this subprocess and break the venv python's
    normal site-packages resolution (e.g. `import google.auth` failing
    even though it's installed). Strip them so the venv python starts as
    if launched fresh from a shell.

    Also: apps launched from Finder/LaunchServices (double-click, not a
    Terminal) get a bare PATH that doesn't include Homebrew's bin dir —
    app.main shells out to `mediamtx` and `ffmpeg` by bare name, so
    without this they silently fail to start (no error surfaced, cameras
    just show offline)."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("PYTHON")}
    homebrew_bins = ["/opt/homebrew/bin", "/opt/homebrew/sbin", "/usr/local/bin"]
    path_parts = env.get("PATH", "").split(":")
    env["PATH"] = ":".join(homebrew_bins + [p for p in path_parts if p not in homebrew_bins])
    return env


def _start_server() -> None:
    global _server_proc
    _server_proc = subprocess.Popen(
        [PYTHON, "-m", "app.main"], cwd=PROJECT_DIR, env=_clean_env(),
    )


def _wait_and_load(window) -> None:
    if not _server_up():
        _start_server()
        for _ in range(60):  # up to ~30s
            if _server_up():
                break
            time.sleep(0.5)
    window.load_url(DASHBOARD_URL)


def _on_closed() -> None:
    if _server_proc and _server_proc.poll() is None:
        _server_proc.terminate()
        try:
            _server_proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            _server_proc.kill()


def main():
    window = webview.create_window(
        "KROSS Replay",
        html=LOADING_HTML,
        width=1280,
        height=800,
        min_size=(800, 600),
    )
    window.events.closed += _on_closed
    webview.start(_wait_and_load, window)


if __name__ == "__main__":
    main()
