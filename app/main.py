#!/usr/bin/env python3
"""
Padel replay system — web server.

This is the single program you run. It:
  1. loads config.yaml
  2. serves the camera-grid web page at  http://<this-machine>:8000/
  3. serves the mobile button page at    http://<this-machine>:8000/m
  4. exposes a small JSON API the pages call
  5. manages the MediaMTX process, and any camera sources that need a local
     process to feed it (publishing a Mac's built-in camera, or continuously
     recording every enabled camera into a rolling buffer for clip-cutting)
  6. on a button trigger: cuts the last clip_seconds from that camera's
     buffer, uploads it to Cloudinary, and writes a Firestore doc with the
     result (see .env.example for the credentials this needs)

Run:
    pip install -r requirements.txt
    cp .env.example .env   # fill in Cloudinary + Firebase credentials
    python -m app.main
Then open http://localhost:8000  (or the machine's LAN IP from your phone).
"""

import json
import logging
import os
import re
import secrets
import socket
import subprocess
import threading
import time
import urllib.request
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path

import cloudinary
import cloudinary.uploader
import firebase_admin
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from firebase_admin import credentials, firestore
from pydantic import BaseModel
from ruamel.yaml import YAML
from tenacity import retry, stop_after_attempt, wait_fixed

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("server")

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "web"
CONFIG_PATH = ROOT / "config.yaml"
MEDIAMTX_PATH = ROOT / "mediamtx.yml"
MEDIAMTX_RTSP_PORT = 8554
MEDIAMTX_API = "http://localhost:9997"

load_dotenv(ROOT / ".env")

# round-trip YAML: edits made through the API keep the comments/formatting
# already in config.yaml and mediamtx.yml instead of clobbering them.
_yaml = YAML()
_yaml.preserve_quotes = True
_yaml.indent(mapping=2, sequence=4, offset=2)


def load_yaml(path: Path):
    with open(path) as f:
        return _yaml.load(f)


def save_yaml(path: Path, data) -> None:
    with open(path, "w") as f:
        _yaml.dump(data, f)


CFG = load_yaml(CONFIG_PATH)

# ----------------------------------------------------------------- Cloudinary / Firestore
# Both are optional at startup: if not configured (.env missing), clips are
# still cut to clips/ but the upload/metadata-write step is skipped with a
# warning, instead of crashing the whole server.
CLOUDINARY_CONFIGURED = bool(os.environ.get("CLOUDINARY_CLOUD_NAME"))
if CLOUDINARY_CONFIGURED:
    cloudinary.config(
        cloud_name=os.environ["CLOUDINARY_CLOUD_NAME"],
        api_key=os.environ["CLOUDINARY_API_KEY"],
        api_secret=os.environ["CLOUDINARY_API_SECRET"],
        secure=True,
    )
else:
    log.warning("Cloudinary not configured (.env missing) — clips will be cut but not uploaded")

FIRESTORE_COLLECTION = os.environ.get("FIRESTORE_COLLECTION", "kross_highlight")
_firestore_db = None
_service_account_path = os.environ.get("FIREBASE_SERVICE_ACCOUNT_PATH")
if _service_account_path and Path(_service_account_path).exists():
    firebase_admin.initialize_app(credentials.Certificate(_service_account_path))
    _firestore_db = firestore.client()
else:
    log.warning("Firebase not configured (FIREBASE_SERVICE_ACCOUNT_PATH missing) — clip metadata will not be saved")

# ----------------------------------------------------------------- app
app_lock = threading.Lock()  # guards CFG + the two yaml files during edits


def slugify(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "_", text.strip().lower()).strip("_")
    return s or "cam"


def unique_id(base: str, existing: set) -> str:
    if base not in existing:
        return base
    i = 2
    while f"{base}{i}" in existing:
        i += 1
    return f"{base}{i}"


# ----------------------------------------------------------------- MediaMTX process
_mediamtx_proc: subprocess.Popen | None = None


def start_mediamtx() -> None:
    """(Re)launch MediaMTX against mediamtx.yml. Safe to call repeatedly."""
    global _mediamtx_proc
    stop_mediamtx()
    try:
        _mediamtx_proc = subprocess.Popen(
            ["mediamtx", str(MEDIAMTX_PATH)],
            cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        log.info("MediaMTX started (pid %d)", _mediamtx_proc.pid)
    except FileNotFoundError:
        log.error("mediamtx binary not found on PATH — camera streams will not work")


def stop_mediamtx() -> None:
    global _mediamtx_proc
    if _mediamtx_proc and _mediamtx_proc.poll() is None:
        _mediamtx_proc.terminate()
        try:
            _mediamtx_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            _mediamtx_proc.kill()
    _mediamtx_proc = None


def restart_mediamtx() -> None:
    """Call after mediamtx.yml changes so MediaMTX picks up new paths."""
    start_mediamtx()
    time.sleep(1)  # give it a moment to bind before anything tries to publish


def live_camera_ids() -> set:
    """Ask MediaMTX's API which paths currently have a publisher connected,
    for the live/offline badge. Empty set if the API isn't reachable yet."""
    try:
        with urllib.request.urlopen(f"{MEDIAMTX_API}/v3/paths/list", timeout=2) as r:
            data = json.load(r)
        return {item["name"] for item in data.get("items", []) if item.get("ready")}
    except Exception:
        return set()


# ----------------------------------------------------------------- Mac camera (ffmpeg) processes
# A Mac's built-in camera has no RTSP output of its own, so we run ffmpeg
# (avfoundation input) to publish it into MediaMTX at rtsp://localhost:8554/<id>,
# same as any other camera source from the app's point of view.
_mac_stop_events: dict[str, threading.Event] = {}


def _mac_ffmpeg_supervisor(cam_id: str, device_index: int, stop_event: threading.Event) -> None:
    url = f"rtsp://localhost:{MEDIAMTX_RTSP_PORT}/{cam_id}"
    cmd = [
        "ffmpeg", "-nostdin", "-loglevel", "warning",
        "-f", "avfoundation", "-framerate", "30", "-video_size", "1280x720",
        "-i", f"{device_index}:none",
        "-vcodec", "libx264", "-preset", "ultrafast", "-tune", "zerolatency",
        "-pix_fmt", "yuv420p",
        "-f", "rtsp", "-rtsp_transport", "tcp", url,
    ]
    while not stop_event.is_set():
        proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        log.info("mac-camera ffmpeg started for %s (pid %d, device %d)", cam_id, proc.pid, device_index)
        while proc.poll() is None:
            if stop_event.wait(1):
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                return
        if not stop_event.is_set():
            log.warning("mac-camera ffmpeg for %s exited unexpectedly, restarting in 2s", cam_id)
            stop_event.wait(2)


def start_mac_camera(cam_id: str, device_index: int) -> None:
    stop_mac_camera(cam_id)
    ev = threading.Event()
    _mac_stop_events[cam_id] = ev
    threading.Thread(target=_mac_ffmpeg_supervisor, args=(cam_id, device_index, ev), daemon=True).start()


def stop_mac_camera(cam_id: str) -> None:
    ev = _mac_stop_events.pop(cam_id, None)
    if ev:
        ev.set()


# ----------------------------------------------------------------- rolling buffer recorder
# Every enabled camera gets a continuous ffmpeg process writing rolling
# segment_seconds-long .mp4 files into buffer/<cam_id>/, wrapping after
# segment_wrap files (segment_wrap x segment_seconds = the buffer window).
# A trigger later concatenates the newest ones into a clip.
ENCODER_MAP = {"videotoolbox": "h264_videotoolbox", "qsv": "h264_qsv", "libx264": "libx264"}
_buffer_stop_events: dict[str, threading.Event] = {}


def _buffer_dir_for(cam_id: str) -> Path:
    d = Path(CFG["system"]["buffer_dir"]) / cam_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def _buffer_supervisor(cam_id: str, stop_event: threading.Event) -> None:
    src = f"rtsp://localhost:{MEDIAMTX_RTSP_PORT}/{cam_id}"
    seg_dir = _buffer_dir_for(cam_id)
    encoder = ENCODER_MAP.get(CFG["system"].get("encoder"), "libx264")
    seg_seconds = CFG["system"]["segment_seconds"]
    seg_wrap = CFG["system"]["segment_wrap"]
    cmd = [
        "ffmpeg", "-nostdin", "-loglevel", "warning", "-rtsp_transport", "tcp",
        "-i", src,
        "-an", "-c:v", encoder, "-pix_fmt", "yuv420p",
        "-force_key_frames", f"expr:gte(t,n_forced*{seg_seconds})",
        "-f", "segment", "-segment_time", str(seg_seconds),
        "-segment_wrap", str(seg_wrap), "-reset_timestamps", "1",
        str(seg_dir / "seg%03d.mp4"),
    ]
    while not stop_event.is_set():
        proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        log.info("buffer recorder started for %s (pid %d)", cam_id, proc.pid)
        while proc.poll() is None:
            if stop_event.wait(1):
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                return
        if not stop_event.is_set():
            log.warning("buffer recorder for %s exited unexpectedly, restarting in 3s", cam_id)
            stop_event.wait(3)


def start_buffer_recorder(cam_id: str) -> None:
    stop_buffer_recorder(cam_id)
    ev = threading.Event()
    _buffer_stop_events[cam_id] = ev
    threading.Thread(target=_buffer_supervisor, args=(cam_id, ev), daemon=True).start()


def stop_buffer_recorder(cam_id: str) -> None:
    ev = _buffer_stop_events.pop(cam_id, None)
    if ev:
        ev.set()


def cut_clip(cam_id: str, claim: str) -> Path | None:
    """Concatenate the most recent finished segments into clips/<claim>.mp4.
    Returns None if there isn't enough buffered footage yet (camera just
    started) or the segment directory doesn't exist."""
    seg_dir = Path(CFG["system"]["buffer_dir"]) / cam_id
    segs = sorted(seg_dir.glob("seg*.mp4"), key=lambda p: p.stat().st_mtime)
    if len(segs) < 2:
        return None
    segs = segs[:-1]  # the newest file is still being written — exclude it

    seg_seconds = CFG["system"]["segment_seconds"]
    needed = -(-CFG["system"]["clip_seconds"] // seg_seconds)  # ceil
    if len(segs) < needed:
        return None  # camera hasn't buffered a full clip_seconds yet
    segs = segs[-needed:]

    clips_dir = Path(CFG["system"]["clips_dir"])
    clips_dir.mkdir(parents=True, exist_ok=True)
    out_path = clips_dir / f"{claim}.mp4"
    list_path = clips_dir / f"{claim}.txt"
    list_path.write_text("".join(f"file '{s.resolve()}'\n" for s in segs))
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-nostdin", "-loglevel", "warning",
             "-f", "concat", "-safe", "0", "-i", str(list_path),
             "-c", "copy", str(out_path)],
            check=True, timeout=30,
        )
    finally:
        list_path.unlink(missing_ok=True)
    return out_path if out_path.exists() else None


@retry(stop=stop_after_attempt(3), wait=wait_fixed(2), reraise=True)
def _upload_to_cloudinary(clip_path: Path, claim: str, club_id: str) -> tuple:
    result = cloudinary.uploader.upload_large(
        str(clip_path), resource_type="video",
        folder=f"kross/{club_id}", public_id=claim,
    )
    return result["secure_url"], result["public_id"]


def process_clip(cam_id: str, court_id: str, claim: str) -> None:
    """Runs in a background thread after a trigger: cut the clip, upload it,
    write the Firestore doc. Any failure here is logged, not raised — the
    button's HTTP response already went back with the claim code."""
    try:
        clip_path = cut_clip(cam_id, claim)
        if not clip_path:
            log.warning("claim %s: not enough buffered footage yet for camera %s", claim, cam_id)
            return

        club_id = CFG.get("branch", {}).get("id", "site")
        video_url = None
        public_id = None
        if CLOUDINARY_CONFIGURED:
            video_url, public_id = _upload_to_cloudinary(clip_path, claim, club_id)
            # uploaded — the mini-PC doesn't need to keep a local copy anymore
            clip_path.unlink(missing_ok=True)
        else:
            log.warning("claim %s: Cloudinary not configured, skipping upload", claim)

        if _firestore_db is not None:
            now = datetime.now()
            doc = {
                "club": club_id,
                "court": court_id,
                "cameraId": cam_id,
                "claimCode": claim,
                "durationSeconds": CFG["system"]["clip_seconds"],
                "date": now.strftime("%Y-%m-%d"),
                "time": now.strftime("%H:%M"),
                "createdAt": firestore.SERVER_TIMESTAMP,
                "videoUrl": video_url,
            }
            if public_id:
                doc["cloudinaryPublicId"] = public_id
            _firestore_db.collection(FIRESTORE_COLLECTION).add(doc)
        else:
            log.warning("claim %s: Firestore not configured, skipping metadata write", claim)

        log.info("claim %s: clip processed (videoUrl=%s)", claim, video_url)
    except Exception:
        log.exception("claim %s: failed to process clip", claim)


# ----------------------------------------------------------------- retention cleanup
# Highlight clips older than CLIP_RETENTION_DAYS get their Cloudinary asset
# and Firestore doc deleted, so old footage doesn't sit around forever.
CLIP_RETENTION_DAYS = int(os.environ.get("CLIP_RETENTION_DAYS", "7"))


def _cleanup_old_clips_once() -> None:
    if _firestore_db is None:
        return
    cutoff = datetime.now(timezone.utc) - timedelta(days=CLIP_RETENTION_DAYS)
    expired = _firestore_db.collection(FIRESTORE_COLLECTION).where(
        filter=firestore.FieldFilter("createdAt", "<", cutoff)
    ).stream()
    removed = 0
    for doc in expired:
        data = doc.to_dict()
        public_id = data.get("cloudinaryPublicId")
        if public_id and CLOUDINARY_CONFIGURED:
            try:
                cloudinary.uploader.destroy(public_id, resource_type="video")
            except Exception:
                log.exception("cleanup: failed to delete Cloudinary asset %s", public_id)
        doc.reference.delete()
        removed += 1
        log.info("cleanup: removed expired clip claim=%s (older than %d days)",
                  data.get("claimCode"), CLIP_RETENTION_DAYS)
    if removed:
        log.info("cleanup: removed %d expired clip(s)", removed)


def _cleanup_loop(stop_event: threading.Event) -> None:
    while not stop_event.is_set():
        try:
            _cleanup_old_clips_once()
        except Exception:
            log.exception("cleanup: run failed")
        stop_event.wait(6 * 3600)  # re-check every 6 hours


_cleanup_stop_event = threading.Event()


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_mediamtx()
    time.sleep(1)
    for c in CFG.get("cameras", []):
        if c.get("enabled") and c.get("source_type") == "mac" and "mac_device_index" in c:
            start_mac_camera(c["id"], c["mac_device_index"])
        if c.get("enabled"):
            start_buffer_recorder(c["id"])
    threading.Thread(target=_cleanup_loop, args=(_cleanup_stop_event,), daemon=True).start()
    yield
    _cleanup_stop_event.set()
    for cam_id in list(_mac_stop_events):
        stop_mac_camera(cam_id)
    for cam_id in list(_buffer_stop_events):
        stop_buffer_recorder(cam_id)
    stop_mediamtx()


app = FastAPI(title="KROSS Replay", lifespan=lifespan)
app.mount("/assets", StaticFiles(directory=ROOT / "assets"), name="assets")

# in-memory record of the last trigger per court, for the cooldown check
_last_trigger: dict[str, float] = {}


class TriggerReq(BaseModel):
    court: str
    token: str | None = None   # phone/on-screen buttons omit it; ESP32 sends it


class AddCameraReq(BaseModel):
    name: str
    court_id: str | None = None     # pick an existing court...
    court_name: str | None = None   # ...or create one with this display name
    camera_type: str                # "rtsp" | "mac"
    rtsp_url: str | None = None         # required for camera_type == "rtsp"
    mac_device_index: int | None = None  # required for camera_type == "mac"


# ---- pages ----------------------------------------------------------------
@app.get("/")
def index():
    """The main camera grid (desktop / big screen)."""
    return FileResponse(WEB / "index.html")


@app.get("/m")
def mobile():
    """The phone button page. (Filled in at Step 6; placeholder for now.)"""
    p = WEB / "mobile.html"
    if p.exists():
        return FileResponse(p)
    return JSONResponse({"note": "mobile page arrives in Step 6"})


# ---- API the pages call ---------------------------------------------------
@app.get("/api/cameras")
def api_cameras():
    """List cameras so the page can draw one tile per camera."""
    live = live_camera_ids()
    cams = [
        {
            "id": c["id"],
            "name": c.get("name", c["id"]),
            "court": c.get("court"),
            "enabled": c.get("enabled", False),
            "live": c["id"] in live,
        }
        for c in CFG.get("cameras", [])
    ]
    return {"cameras": cams, "clip_seconds": CFG["system"]["clip_seconds"]}


@app.get("/api/courts")
def api_courts():
    """List courts so the Add Camera form can offer them in a dropdown."""
    return {
        "courts": [
            {"id": cid, "name": c.get("display_name", cid)}
            for cid, c in CFG.get("courts", {}).items()
        ]
    }


@app.get("/api/mac-devices")
def api_mac_devices():
    """List cameras avfoundation (ffmpeg) can see on this Mac."""
    try:
        r = subprocess.run(
            ["ffmpeg", "-f", "avfoundation", "-list_devices", "true", "-i", ""],
            capture_output=True, text=True, timeout=10,
        )
    except FileNotFoundError:
        raise HTTPException(500, "ffmpeg not found on this machine")

    devices = []
    in_video_section = False
    for line in r.stderr.splitlines():
        if "AVFoundation video devices" in line:
            in_video_section = True
            continue
        if "AVFoundation audio devices" in line:
            in_video_section = False
            continue
        if in_video_section:
            m = re.search(r"\[(\d+)]\s+(.*)$", line)
            if m:
                devices.append({"index": int(m.group(1)), "name": m.group(2).strip()})
    return {"devices": devices}


@app.post("/api/cameras")
def api_add_camera(req: AddCameraReq):
    """Add a camera: writes config.yaml (+ mediamtx.yml if it needs a path),
    restarts MediaMTX so the new path is live, and starts ffmpeg for a Mac
    camera. Everything is persisted, so it survives a server restart."""
    if req.camera_type not in ("rtsp", "mac"):
        raise HTTPException(400, f"unknown camera_type: {req.camera_type}")
    if req.camera_type == "rtsp" and not req.rtsp_url:
        raise HTTPException(400, "rtsp_url is required for camera_type 'rtsp'")
    if req.camera_type == "mac" and req.mac_device_index is None:
        raise HTTPException(400, "mac_device_index is required for camera_type 'mac'")

    with app_lock:
        # this machine's club/branch is fixed at deploy time (config.yaml) —
        # adding a camera never changes it
        branch_id = CFG.get("branch", {}).get("id", "site")

        existing_ids = {c["id"] for c in CFG.get("cameras", [])}
        cam_id = unique_id(slugify(req.name), existing_ids)

        courts = CFG.setdefault("courts", {})
        if req.court_id and req.court_id in courts:
            court_id = req.court_id
        else:
            base_name = req.court_name or req.court_id or req.name
            court_id = unique_id(slugify(base_name), set(courts.keys()))
            courts[court_id] = {
                "display_name": req.court_name or base_name,
                "primary_cam": cam_id,
                "button_token": f"{branch_id}-{court_id}-{secrets.token_hex(3)}",
            }

        mediamtx_data = load_yaml(MEDIAMTX_PATH)
        paths = mediamtx_data.setdefault("paths", {})
        if req.camera_type == "rtsp":
            paths[cam_id] = {"source": req.rtsp_url}
        else:
            paths[cam_id] = {"source": "publisher"}
        save_yaml(MEDIAMTX_PATH, mediamtx_data)

        camera_entry = {
            "id": cam_id,
            "court": court_id,
            "name": req.name,
            "enabled": True,
            "source_type": req.camera_type,
            "source": f"rtsp://localhost:{MEDIAMTX_RTSP_PORT}/{cam_id}",
        }
        if req.camera_type == "mac":
            camera_entry["mac_device_index"] = req.mac_device_index

        CFG.setdefault("cameras", []).append(camera_entry)
        save_yaml(CONFIG_PATH, CFG)

        restart_mediamtx()
        if req.camera_type == "mac":
            start_mac_camera(cam_id, req.mac_device_index)
        start_buffer_recorder(cam_id)

    log.info("camera added: %s (%s) -> court %s", cam_id, req.camera_type, court_id)
    return {"ok": True, "camera": camera_entry}


@app.delete("/api/cameras/{cam_id}")
def api_delete_camera(cam_id: str):
    with app_lock:
        cams = CFG.get("cameras", [])
        match = next((c for c in cams if c["id"] == cam_id), None)
        if not match:
            raise HTTPException(404, f"unknown camera: {cam_id}")

        if match.get("source_type") == "mac":
            stop_mac_camera(cam_id)
        stop_buffer_recorder(cam_id)

        cams.remove(match)

        # drop the court too if this was its only camera, so test add/remove
        # cycles don't leave orphaned court entries behind
        court_id = match.get("court")
        courts = CFG.get("courts", {})
        if court_id in courts and not any(c.get("court") == court_id for c in cams):
            del courts[court_id]

        save_yaml(CONFIG_PATH, CFG)

        mediamtx_data = load_yaml(MEDIAMTX_PATH)
        mediamtx_data.get("paths", {}).pop(cam_id, None)
        save_yaml(MEDIAMTX_PATH, mediamtx_data)
        restart_mediamtx()

    log.info("camera removed: %s", cam_id)
    return {"ok": True}


@app.get("/api/highlights")
def api_highlights(limit: int = 10):
    """Most recent highlight clips for this branch, for the dashboard's
    Recent Highlights sidebar. Filters by club in Python (rather than a
    Firestore `where` on club combined with `order_by` on createdAt) so it
    doesn't need a composite index — this collection is shared across all
    branches (see MULTI_BRANCH.md)."""
    if _firestore_db is None:
        return {"highlights": []}

    club_id = CFG.get("branch", {}).get("id", "site")
    docs = (
        _firestore_db.collection(FIRESTORE_COLLECTION)
        .order_by("createdAt", direction=firestore.Query.DESCENDING)
        .limit(limit * 3)
        .stream()
    )
    highlights = []
    for doc in docs:
        d = doc.to_dict()
        if d.get("club") != club_id or not d.get("videoUrl"):
            continue
        highlights.append({
            "id": doc.id,
            "court": d.get("court"),
            "claimCode": d.get("claimCode"),
            "videoUrl": d.get("videoUrl"),
            "date": d.get("date"),
            "time": d.get("time"),
        })
        if len(highlights) >= limit:
            break
    return {"highlights": highlights}


@app.get("/api/status")
def api_status():
    """Lightweight heartbeat the page polls to show the server is alive."""
    branch = CFG.get("branch", {})
    return {
        "ok": True,
        "time": time.time(),
        "cameras": len([c for c in CFG.get("cameras", []) if c.get("enabled")]),
        "branchId": branch.get("id"),
        "branchName": branch.get("name"),
    }


@app.post("/api/trigger")
def api_trigger(req: TriggerReq):
    """
    One endpoint for ALL buttons — on-screen, phone, and the real ESP32 in the
    court. Responds immediately with a claim code (fast button feedback);
    cutting the clip, uploading it, and writing Firestore all happen in a
    background thread so the button doesn't wait on any of that.
    """
    courts = CFG.get("courts", {})
    court = courts.get(req.court)
    if not court:
        raise HTTPException(404, f"unknown court: {req.court}")

    # on-screen/phone buttons send no token and are trusted implicitly (same
    # LAN, staff-facing UI); a real ESP32 court button sends one, and if it's
    # wrong it's rejected rather than silently treated as anonymous — catches
    # a misconfigured or spoofed device without breaking the tokenless flow
    if req.token is not None and req.token != court.get("button_token"):
        raise HTTPException(403, "invalid button token")

    now = time.time()
    cooldown = CFG["system"]["cooldown_seconds"]
    since = now - _last_trigger.get(req.court, 0)
    if since < cooldown:
        remain = cooldown - since
        raise HTTPException(429, f"cooldown: wait {remain:.0f}s")

    _last_trigger[req.court] = now
    claim = f"{int(now) % 10000:04d}"
    cam_id = court.get("primary_cam")
    log.info("TRIGGER court=%s  cam=%s  claim=%s", req.court, cam_id, claim)

    if cam_id:
        threading.Thread(
            target=process_clip, args=(cam_id, req.court, claim), daemon=True,
        ).start()
    else:
        log.warning("claim %s: court %s has no primary_cam configured", claim, req.court)

    return {"ok": True, "court": req.court, "claimCode": claim}


# ---- helpers --------------------------------------------------------------
def lan_ip() -> str:
    """Best-effort LAN IP so we can print a URL your phone can open."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()


def main():
    import uvicorn

    port = CFG["system"].get("http_port", 8000)
    ip = lan_ip()
    log.info("=" * 56)
    log.info("KROSS Replay server starting")
    log.info("  on this machine : http://localhost:%d", port)
    log.info("  from your phone : http://%s:%d/m   (same WiFi)", ip, port)
    log.info("=" * 56)
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="warning")


if __name__ == "__main__":
    main()
