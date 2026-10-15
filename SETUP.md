# KROSS Replay — Setup Guide (from a brand-new machine)

This walks through everything needed to get KROSS Replay running on a
machine that has nothing installed yet — for both **macOS** and **Windows**.
Pick the section for your OS.

Covers: installing prerequisites → getting the project → configuring it →
running it manually to verify → making it auto-start → (optional) a
double-clickable desktop app / tray icon.

*(ฉบับภาษาไทย: [SETUP.th.md](SETUP.th.md))*

---

## macOS

### 1. Install prerequisites
Open Terminal.

Install [Homebrew](https://brew.sh) if you don't have it:
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Then install the tools this project needs:
```bash
brew install python@3.11 ffmpeg mediamtx
```

### 2. Get the project
If you're setting up a **new site/branch**, copy the whole `camera_system`
folder from an existing machine (via AirDrop, USB, etc.), **including**
`.env` and `firebase-service-account.json` — these credentials are shared
across every branch on purpose (see `MULTI_BRANCH.md`). Do **not** copy the
`.venv` folder; you'll create a fresh one below.

If you're starting completely fresh (no existing site to copy from), place
the project folder at e.g. `~/Documents/camera_system` and you'll fill in
`.env` yourself in step 4.

### 3. Set up the Python environment
```bash
cd ~/Documents/camera_system
python3.11 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

### 4. Configure credentials and this branch's identity
```bash
cp .env.example .env
```
Edit `.env` and fill in:
- `R2_ACCOUNT_ID` / `R2_ACCESS_KEY_ID` / `R2_SECRET_ACCESS_KEY` /
  `R2_BUCKET` / `R2_PUBLIC_URL` — Cloudflare R2 (clip video hosting). See
  "Cloudflare R2 setup" below for where each value comes from.
- `FIREBASE_SERVICE_ACCOUNT_PATH` — leave as `./firebase-service-account.json`
  and place that file (downloaded from Firebase Console → Project Settings →
  Service Accounts → Generate new private key) in the project root

If this machine is a **new branch/site** rather than a copy of an existing
one, also edit `config.yaml`:
- `branch.id` / `branch.name` — a short unique code and display name for
  this site
- `cameras: []` and `courts: {}` — clear these out; you'll add real cameras
  later through the web UI's **+ Add Camera** button

### 5. Run it manually to verify
```bash
.venv/bin/python -m app.main
```
You should see it print `http://localhost:8000`. Open that in a browser —
you should see the camera grid (Court tiles, CAPTURE buttons). Press
`Ctrl+C` to stop once confirmed.

### 6. Make it auto-start (launchd service)
`com.kross.replay.plist` is already set up to run the server via `launchd`
(starts at login, restarts itself if it crashes). If this is a fresh copy
on a new machine, check the paths inside it match this machine's actual
project location, then:
```bash
cp com.kross.replay.plist ~/Library/LaunchAgents/
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.kross.replay.plist
```
Check it's running: `launchctl list | grep kross`. Logs go to `logs/server.log`.

### 7. Optional: menu bar control icon
`control_app/kross_control.py` is a menu bar icon (green/red status) with
Start/Stop/Open Dashboard/View Logs, controlling the launchd service above.
```bash
.venv/bin/pip install rumps py2app pyobjc
cd control_app
../.venv/bin/python setup.py py2app
```
Produces `control_app/dist/KROSS Control.app` — drag it to `/Applications`
and add it to Login Items (System Settings → General → Login Items) so it's
always in the menu bar.

### 8. Optional: dashboard app window + Desktop icon
`desktop_app/kross_dashboard.py` opens the camera-grid dashboard in its own
native window instead of a browser tab, and starts the server itself if it
isn't already running.
```bash
.venv/bin/pip install pywebview
cd desktop_app
../.venv/bin/python setup.py py2app
```
Produces `desktop_app/dist/KROSS Replay.app`. Copy it to the Desktop for a
double-clickable icon:
```bash
cp -R "dist/KROSS Replay.app" ~/Desktop/
```
Re-run this build step (and re-copy) any time `kross_dashboard.py` changes.

---

## Windows

Everything below assumes an empty Windows machine. **This section hasn't
been run on a real Windows PC yet** (written from macOS, which can't test
or cross-build Windows binaries) — if any step errors, note the exact
message so it can be fixed.

### 1. Install prerequisites
- [Python 3.11](https://www.python.org/downloads/) — check **"Add
  python.exe to PATH"** during install
- [ffmpeg](https://www.gyan.dev/ffmpeg/builds/) — download a "full" or
  "essentials" build, unzip it somewhere permanent (e.g. `C:\ffmpeg`), and
  add its `bin` folder to your PATH (Settings → search "environment
  variables" → Edit the `Path` variable → New → paste the `bin` folder path)
- [MediaMTX](https://github.com/bluenviron/mediamtx/releases) — download
  the `windows_amd64` zip, unzip it, note the folder (contains
  `mediamtx.exe`) — add it to PATH the same way as ffmpeg
- [NSSM](https://nssm.cc/download) — unzip, note the path to `nssm.exe`
  (use the `win64` folder) — only needed for step 6 (auto-start)

### 2. Get the project
Copy the whole `camera_system` folder to this machine, e.g.
`C:\KrossReplay\camera_system`. If this is a new branch/site copied from an
existing one, include `.env` and `firebase-service-account.json` as-is
(shared credentials across every branch — see `MULTI_BRANCH.md`). Do **not**
copy the `.venv` folder.

### 3. Set up the Python environment
Open PowerShell:
```powershell
cd C:\KrossReplay\camera_system
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
```

### 4. Configure credentials and this branch's identity
```powershell
copy .env.example .env
```
Fill in `.env` the same way as the macOS section above (R2 keys,
Firebase service account path). Place `firebase-service-account.json` in
the project root if it isn't there already.

If this is a **new branch/site**, also edit `config.yaml`:
- `branch.id` / `branch.name` — unique code and display name for this site
- `system.encoder` → set to `libx264` (safe default without a special GPU
  driver — see the comment in `config.yaml` for the `qsv` option if this
  machine has a modern Intel iGPU)
- Clear out test data: `cameras: []`, `courts: {}` in `config.yaml`, and
  `paths: {}` in `mediamtx.yml` (keep `api: yes`)

### 5. Run it manually to verify
```powershell
.venv\Scripts\python -m app.main
```
Open `http://localhost:8000` in a browser — you should see the camera grid.
Use **+ Add Camera** to add this site's real cameras. Confirm capture →
clip → R2 → Firestore works before moving on. `Ctrl+C` to stop.

### 6. Make it auto-start (Windows Service via NSSM)
Edit `NSSM_EXE` and `PROJECT_DIR` at the top of
`windows_deploy\install_service.bat` to match this machine, then
right-click it → **Run as administrator**.

This registers a service named `KrossReplay` that starts at boot (even
before login) and restarts itself if it crashes. Check status:
`sc query KrossReplay`. Logs go to `logs\server.log`. To remove it later,
edit and run `windows_deploy\uninstall_service.bat` as administrator.

### 7. Optional: tray icon control panel
`windows_deploy\kross_control_win.py` is a system tray icon (green/red
status) with Start/Stop/Open Dashboard/View Logs, controlling the service
above.
```powershell
pip install -r windows_deploy\requirements.txt
python windows_deploy\kross_control_win.py
```
To make it a double-clickable `.exe`:
```powershell
cd windows_deploy
pyinstaller --onefile --windowed --name "KROSS Control" kross_control_win.py
```
The `.exe` lands in `windows_deploy\dist\KROSS Control.exe`. Drop a shortcut
to it in the Startup folder (`Win+R` → `shell:startup`) to have the tray
icon appear automatically at login.

**Note:** Start/Stop in the tray app need admin rights (they call `net
start`/`net stop`) — if those buttons don't do anything, run the tray app
itself as Administrator.

### 8. Optional: dashboard app window + Desktop icon
`desktop_app\kross_dashboard_win.py` opens the camera-grid dashboard in its
own native window. Unlike the tray app, it doesn't manage the service
directly beyond starting it if it's stopped (`net start KrossReplay`);
closing the window doesn't stop the service.
```powershell
pip install -r requirements.txt
pip install -r windows_deploy\requirements.txt
cd desktop_app
pyinstaller --onefile --windowed --name "KROSS Replay" kross_dashboard_win.py
```
The `.exe` lands in `desktop_app\dist\KROSS Replay.exe` — copy it to the
Desktop for a double-clickable icon, or drop a shortcut to it in the
Startup folder for it to open automatically at login.

### 9. Optional: skip steps 3–8 with a real installer
`windows_deploy\installer\kross_replay.iss` builds all of the above (venv,
dependencies, the `KrossReplay` service, both desktop apps + shortcuts)
into one `KROSS Replay Setup.exe`. Still expects Python/ffmpeg/MediaMTX/NSSM
from step 1 to already be installed. See `windows_deploy/README.md` step 9
for the build steps and what it does/doesn't bundle.

---

## Common next steps (both platforms)
- **Add cameras**: open the dashboard → **+ Add Camera** → pick an existing
  court or create a new one → RTSP URL (IP camera) or pick a Mac/Windows
  built-in camera device.
- **Multi-branch**: see `MULTI_BRANCH.md` for how one R2 bucket + Firebase
  project serves multiple independent sites.
- **Cloudflare R2 setup** (one-time, shared by every branch):
  1. dash.cloudflare.com → R2 Object Storage → Create bucket `kross-clips`
     (location: Asia-Pacific).
  2. Bucket → Settings → Public Development URL → Enable (testing), or
     Custom Domains → Add (production). That URL is `R2_PUBLIC_URL`.
  3. Bucket → Settings → Object Lifecycle Rules → Add: delete objects
     7 days after creation, all objects.
  4. R2 Object Storage → API → Manage API tokens → Create Account API token:
     Object Read & Write, only bucket `kross-clips`. Copy the Access Key ID /
     Secret Access Key into `.env` (the secret is shown once). The account ID
     is the subdomain of the bucket's S3 API URL.
- **Clip size**: `system.output_height` (default 1080) and
  `system.video_bitrate` (default 6M) in `config.yaml` control the recorded
  quality — 1080p clips are ~10–30 MB vs ~120 MB at 4K.
- **Troubleshooting**: check `logs/server.log` first. If the dashboard shows
  "server unreachable", confirm the server process (manual run, launchd
  service, or Windows service) is actually up and nothing else is using
  port 8000.
