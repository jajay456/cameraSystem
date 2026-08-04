# KROSS Replay — Step 1: Web server + camera grid

## What this step does
Runs a small web server on your machine that serves a 4-camera monitor page.
Camera tiles are placeholders (live view arrives in Step 2). Each court has a
CAPTURE button that calls the same `/api/trigger` endpoint the phone and the
real ESP32 button will use later. Cooldown and error handling already work.

## Run it
```bash
cd camera_system
pip install -r requirements.txt
python -m app.main
```
Then open:
- On this machine:  http://localhost:8000
- From your phone:  http://<this-machine-LAN-IP>:8000/m   (same WiFi)
  (the server prints the exact URL when it starts)

## Verify
- The page shows 4 tiles: Court 1–4
- Header dot turns green, "4 cameras · server ok"
- Press a CAPTURE button → it flashes, shows "captured · claim NNNN"
- Press again within 15s → shows the cooldown message

## Files
- app/main.py    the server (start here)
- web/index.html the monitor page
- config.yaml    cameras, courts, timings
- requirements.txt

## Next
Step 2: real live view in each tile (MJPEG refresh from the RTSP streams,
reusing your MediaMTX pipeline).