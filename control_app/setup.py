"""
Build with:
    cd control_app
    python setup.py py2app
Produces dist/KROSS Control.app — a menu bar app to start/stop/check the
KROSS Replay server (which itself runs via the com.kross.replay launchd
service). Double-click the .app, or drag it to /Applications and add it
to Login Items so it's always in the menu bar.
"""

from setuptools import setup

APP = ["kross_control.py"]
OPTIONS = {
    "argv_emulation": False,
    "plist": {
        "LSUIElement": True,  # menu bar only — no Dock icon, no app window
        "CFBundleName": "KROSS Control",
        "CFBundleDisplayName": "KROSS Control",
        "CFBundleIdentifier": "com.kross.control",
        "CFBundleShortVersionString": "1.0.0",
    },
    "packages": ["rumps"],
}

setup(
    name="KROSS Control",
    app=APP,
    options={"py2app": OPTIONS},
    setup_requires=["py2app"],
)
