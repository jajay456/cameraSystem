# Multi-branch model (Option A)

## Principle
One self-contained server per site. Video never leaves a site's LAN. Every
site uploads its clips to ONE shared Cloudinary + Firebase account, tagged
with a `branch` so they stay cleanly separated.

## Per site you need
- 1 mini-PC running this program (every branch, **including onnut, runs
  Windows** — see `windows_deploy/README.md` for the actual production setup
  steps, auto-start, and tray control app. The macOS `launchd`
  service + `control_app/` on the current dev Mac were only for local
  development/testing, not the real onnut deployment.)
- that site's cameras on the local network
- internet (only used when a button is pressed, to upload a clip)

## To add a branch
1. Copy this whole project folder to the new site's mini-PC — including
   `.env` and `firebase-service-account.json` as-is (same Cloudinary +
   Firebase account is shared by every branch, on purpose).
2. On the new machine, before running it for the first time, clear out this
   branch's cameras so they don't come along: either delete each camera from
   the web UI (✕ on its tile) on the OLD machine before copying, or on the
   NEW machine set `cameras: []` and `courts: {}` in `config.yaml` and
   `paths: {}` in `mediamtx.yml`.
3. Set `system.encoder` to `libx264` unless you've confirmed the machine has
   a modern Intel iGPU with Quick Sync (then `qsv` is faster).
4. `pip install -r requirements.txt` (make a fresh venv — don't copy `.venv`
   across machines), then `python -m app.main`.
5. Open the web page → **+ Add Camera** → pick this site's **club** from the
   dropdown (onnut / sky / indoor / asoke) → add its real cameras with their
   real RTSP URLs. Picking the club there sets `branch.id` / `branch.name`
   in `config.yaml` automatically — no manual YAML editing needed.
6. Follow `windows_deploy/README.md` steps 6–7 to make it auto-start as a
   Windows Service and (optionally) install the tray control icon.

## What stays shared
- One Cloudinary account (clips go into per-branch folders, added in Step 5)
- One Firebase project (every clip document carries branch = "thl" / "r9" / …)
- An optional central web page can later read Firestore and show/filter all
  branches at once.

## What stays independent
- Recording, buffering, and clip-cutting are 100% local to each site.
- One site's internet outage or power cut does not affect any other site.
- The per-court cooldown is per-site (each server tracks its own).

## Resilience
Because each site is standalone, "the system is down" can only ever mean one
site, never all of them. This is the main reason Option A is preferred over a
single central server for camera systems.