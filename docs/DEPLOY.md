# Deploying the standalone API

The app is local-first: the camera/frontend app runs on localhost, while
Firestore and Cloudinary are cloud services. This repository has no hosting
deployment. The `functions/` directory is an independent Firebase Functions
codebase and can be deployed without the frontend.

## Before deployment

Create or select the Firebase project that owns the existing production
Firestore data. A new Firebase project is **not** required if that project
already exists; use `firebase use <project-id>`. Create a separate project
only when you intentionally want isolated production data.
Cloud Functions deployment requires the **Blaze (pay-as-you-go) plan**. Blaze
allows billed Google Cloud resources such as deployed Functions and outbound
network requests; it does not mean unlimited spending.

In Firebase Console, open **Usage and billing**, choose **Details & settings**,
then create a budget and email alert (for example at 50%, 90%, and 100%).
Budgets alert you; they do not automatically stop all usage.

## Secrets and deploy

```bash
cd functions
npm ci
firebase login
firebase use <production-project-id>
firebase functions:secrets:set TEST_API_KEY
firebase functions:secrets:set CLOUDINARY_API_SECRET
npm run build
firebase deploy --only functions,firestore:indexes
```

Deploying `functions,firestore:indexes` does not deploy Hosting or the
frontend. Add the secrets to the function options before using them in a
production handler; never commit `.env` or service-account files.

The production URL is shown at the end of deployment and is also available
in Firebase Console → **Build → Functions** → the `api` function → Trigger.
It is normally `https://us-central1-<project-id>.cloudfunctions.net/api`.

## Roll back

Use the previous deployed version from Google Cloud Console → Cloud Run
(the generated service for the function), or redeploy the previous source
revision from git:

```bash
git checkout <known-good-revision> -- functions
cd functions && npm ci && npm run build
firebase deploy --only functions
```

Do not run a production deploy until emulator tests and partner tunnel tests
are accepted.

## Temporary partner tunnel

Install `cloudflared` and start `npm run dev:emulator` first. The tunnel
exposes only the Functions emulator port (`5001`), never the frontend (`8000`)
or emulator UI (`4000`).

For a quick random URL:

```bash
API_KEY=local-test-key npm run tunnel:quick
```

For a stable hostname on a Cloudflare-managed domain, create/login to a named
tunnel in Cloudflare first, then run:

```bash
CLOUDFLARE_TUNNEL_NAME=kross-api \
CLOUDFLARE_HOSTNAME=api-test.example.com \
API_KEY=local-test-key npm run tunnel:named
```

The Functions emulator URL includes the project and function name. For the
default local project, test:

```text
https://<tunnel-url>/kross-highlight-local/us-central1/api/api/status
```

Send Book and Go the tunnel URL, the `x-api-key` header value, and this
endpoint shape. Never put the key in the URL or in `docs/BOOKANDGO.md`.

## Real-camera local test

The camera app remains a separate local process. Set `CAMERA_RTSP_URL` only in
the shell or ignored `.env`, then run it against the local Firestore emulator
so the real R2 URL is visible without writing metadata to production:

```bash
FIRESTORE_EMULATOR_HOST=127.0.0.1:8080 \
GCLOUD_PROJECT=kross-highlight-local \
CAMERA_RTSP_URL='rtsp://user:password@camera-ip/stream1' \
.venv/bin/python -m app.main
```

Run the API-only gateway in another terminal. It forwards only `/api/*` to
the camera app and blocks the frontend:

```bash
API_KEY=local-test-key-2026 API_PORT=8001 UPSTREAM_PORT=8000 \
.venv/bin/python functions/scripts/api-gateway.py
API_KEY=local-test-key-2026 API_PORT=8001 npm run tunnel:quick
```

The partner can call `GET /api/highlights` and then open each returned
`videoUrl`. A real capture may take about 40 seconds to finish uploading.

## Run without open terminals (macOS)

This section is only for a Mac that owns the camera. If the real camera is
connected to a different Windows machine, use the Windows service setup in
`windows_deploy/README.md` instead; all four local services must run on the
Windows camera machine.

For an unattended local setup, use a Cloudflare **named tunnel**. Quick
tunnels stop when the terminal closes and their URL changes.

One-time Cloudflare setup:

```bash
cloudflared tunnel login
cloudflared tunnel create kross-api
cloudflared tunnel route dns kross-api api-test.example.com
mkdir -p ~/.cloudflared
cat > ~/.cloudflared/config.yml <<'EOF'
tunnel: <tunnel-uuid>
credentials-file: /Users/<mac-user>/.cloudflared/<tunnel-uuid>.json
ingress:
  - hostname: api-test.example.com
    service: http://127.0.0.1:8001
  - service: http_status:404
EOF
```

In the ignored `.env`, set `CAMERA_RTSP_URL`, `TEST_API_KEY`,
`CLOUDFLARE_TUNNEL_NAME=kross-api`, and the existing R2 values. Then run once:

```bash
chmod +x scripts/*.sh
scripts/install-local-services.sh
scripts/local-services.sh status
```

The emulator, real-camera app, API-only gateway, and named tunnel will now
start after login and restart if they exit. The frontend remains on localhost
port 8000 and is not exposed. Use `scripts/local-services.sh stop` before
maintenance and `restart` after changing `.env`.
