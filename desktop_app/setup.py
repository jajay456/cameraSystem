"""
Build with:
    cd desktop_app
    python setup.py py2app
Produces dist/KROSS Replay.app — a native window showing the KROSS Replay
web dashboard (server must already be running, e.g. via the
com.kross.replay launchd service). Double-click the .app, or drag it to
/Applications.
"""

from setuptools import setup

APP = ["kross_dashboard.py"]
OPTIONS = {
    "argv_emulation": False,
    "iconfile": "../assets/icon/KROSSReplay.icns",
    "plist": {
        "CFBundleName": "KROSS Replay",
        "CFBundleDisplayName": "KROSS Replay",
        "CFBundleIdentifier": "com.kross.dashboard",
        "CFBundleShortVersionString": "1.0.0",
    },
    "packages": ["webview"],
    # pywebview supports many platforms/backends (Qt, GTK, Win32, CEF...);
    # py2app's dependency scan tries to follow all of them (even optional
    # PyInstaller hook files with invalid module names) unless excluded.
    # On macOS only the Cocoa/WebKit backend is actually used.
    "excludes": [
        "PyInstaller",
        "PyQt5", "PyQt6", "PySide2", "PySide6",
        "gi", "qtpy",
    ],
}

setup(
    name="KROSS Replay",
    app=APP,
    options={"py2app": OPTIONS},
    setup_requires=["py2app"],
)
