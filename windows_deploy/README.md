# Windows deployment

Everything in this folder is **written but not yet tested on a real Windows
machine** (built from macOS, which can't run or cross-compile Windows
binaries). Please follow these steps on an actual Windows PC and report back
the exact error message if anything doesn't work — happy to fix it fast.

## 1. Install prerequisites
- [Python 3.11](https://www.python.org/downloads/) — check "Add python.exe to PATH" during install
- [ffmpeg](https://www.gyan.dev/ffmpeg/builds/) (get a "full" or "essentials" build, unzip, add its `bin` folder to PATH)
- [MediaMTX](https://github.com/bluenviron/mediamtx/releases) — download the `windows_amd64` zip, unzip, note the path to `mediamtx.exe`
- [NSSM](https://nssm.cc/download) — unzip, note the path to `nssm.exe` (use the `win64` folder)

## 2. Copy the project
Copy the whole `camera_system` folder to the new machine, e.g. `C:\KrossReplay\camera_system`.
Include `.env` and `firebase-service-account.json` as-is (shared credentials
across every branch). Do **not** copy `.venv` — make a fresh one (step 3).

## 3. Set up the app
```powershell
cd C:\KrossReplay\camera_system
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
```

## 4. Edit config.yaml for this branch
- `system.encoder` → set to `libx264` (safe default; works without any
  special GPU driver — see the comment in config.yaml for the qsv option if
  this machine turns out to have a modern Intel iGPU later)
- Clear out any leftover cameras/courts from testing: `cameras: []`, `courts: {}`
  in `config.yaml`, and `paths: {}` in `mediamtx.yml` (keep `api: yes`)
- Make sure `mediamtx.exe` is reachable — either add its folder to PATH, or
  edit `MEDIAMTX_PATH`-launching code in `app/main.py` to use the full path
  if you'd rather not touch PATH (ask if you want this done instead)

## 5. Test it manually first
```powershell
.venv\Scripts\python -m app.main
```
Open `http://localhost:8000`, use **+ Add Camera**, pick this site's club,
add real cameras. Confirm capture → clip → R2 → Firestore works
before moving on to auto-start. Ctrl+C to stop.

## 6. Install as an auto-starting Windows Service
Edit `NSSM_EXE` and `PROJECT_DIR` at the top of `install_service.bat` to
match this machine, then right-click it → **Run as administrator**.

This registers a service named `KrossReplay` that starts at boot (before
any login) and restarts itself automatically if it ever crashes — the
Windows equivalent of the `launchd` service used on the Mac test machine.

To remove it later: edit and run `uninstall_service.bat` as administrator.

## 7. Optional: tray icon control panel
`kross_control_win.py` is the Windows equivalent of the Mac menu-bar app —
a system tray icon showing green (running) / red (not running), with
Start/Stop/Open Dashboard/View Logs.

```powershell
pip install -r requirements.txt
python kross_control_win.py
```

To make it a real double-clickable `.exe` (must be built ON Windows —
PyInstaller doesn't cross-compile):
```powershell
pyinstaller --onefile --windowed --name "KROSS Control" --icon "..\assets\icon\KROSSReplay.ico" kross_control_win.py
```
The `.exe` will be in `dist\KROSS Control.exe`. Add it to the Startup folder
(`Win+R` → `shell:startup`) if you want the tray icon to appear automatically
at login too.

**Note:** Start/Stop in the tray app run `net start`/`net stop`, which
Windows requires admin rights for — if those buttons don't do anything,
try running the tray app itself as Administrator.

## 8. Optional: dashboard app window
`desktop_app/kross_dashboard_win.py` (Windows equivalent of the macOS
`desktop_app/kross_dashboard.py`) opens the camera-grid dashboard in its own
native window instead of a browser tab. It makes sure the `KrossReplay`
service is running (starting it if needed — same admin-rights caveat as
above) and loads the dashboard.

```powershell
pip install -r requirements.txt
pip install -r windows_deploy\requirements.txt
python desktop_app\kross_dashboard_win.py
```

To make it a real double-clickable `.exe` (must be built ON Windows):
```powershell
cd desktop_app
pyinstaller --onefile --windowed --name "KROSS Replay" --icon "..\assets\icon\KROSSReplay.ico" kross_dashboard_win.py
```
The `.exe` will be in `desktop_app\dist\KROSS Replay.exe` — copy it to the
Desktop, or drop a shortcut to it in Startup (`Win+R` → `shell:startup`) to
have it open automatically at login.

## 9. Optional: a real installer (one setup.exe for everything above)
Instead of doing steps 2–8 by hand on every new site's machine,
`windows_deploy\installer\kross_replay.iss` is an
[Inno Setup](https://jrsoftware.org/isinfo.php) script that packages it all
into a single `KROSS Replay Setup.exe`: copies the project source, creates
the venv and installs dependencies, registers the `KrossReplay` Windows
Service, and installs `KROSS Replay.exe` / `KROSS Control.exe` with Start
Menu + Desktop shortcuts. Uninstalling stops and removes the service too.

This is the **lightweight** installer — it still expects Python, ffmpeg,
MediaMTX, and NSSM to already be installed and on PATH (step 1 above); it
doesn't bundle those binaries itself. It also never bundles `.env` or
`firebase-service-account.json` (secrets/site-specific) — it copies
`.env.example` → `.env` and opens both files in Notepad at the end of
install so the real credentials and this branch's `id`/`name` are easy to
fill in immediately.

Build steps (run ON Windows, in order — full detail in the comment header
of `kross_replay.iss`):
```powershell
# 1. Build the two desktop apps first
cd desktop_app
pyinstaller --onefile --windowed --name "KROSS Replay" --icon "..\assets\icon\KROSSReplay.ico" kross_dashboard_win.py
cd ..\windows_deploy
pyinstaller --onefile --windowed --name "KROSS Control" --icon "..\assets\icon\KROSSReplay.ico" kross_control_win.py

# 2. Install Inno Setup: https://jrsoftware.org/isinfo.php

# 3. Compile the installer (or right-click kross_replay.iss -> Compile)
ISCC.exe windows_deploy\installer\kross_replay.iss
```
Output: `windows_deploy\installer\Output\KROSS Replay Setup.exe` — copy
this one file to a new site's machine and run it as Administrator.

For the end-user side of running that installer (what to install first,
what to fill in, troubleshooting) — hand them `INSTALL.th.md` (Thai,
written for non-technical staff at a new site, no build steps).
