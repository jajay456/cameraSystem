const { spawn } = require("node:child_process");

if (!process.env.GCLOUD_PROJECT) {
  console.error("GCLOUD_PROJECT must identify the production Firebase project.");
  process.exit(1);
}
if (!process.env.TEST_API_KEY) {
  console.error("TEST_API_KEY is required in live-read mode; refusing to start with a placeholder.");
  process.exit(1);
}
const env = {
  ...process.env,
  APP_MODE: "live-read",
  TEST_API_KEY: process.env.TEST_API_KEY,
};
delete env.FIRESTORE_EMULATOR_HOST;
delete env.FIREBASE_AUTH_EMULATOR_HOST;
console.warn("WARNING: LIVE-READ MODE — production Firestore/Cloudinary may be read, but all writes are blocked.");
console.warn("WARNING: Do not run seed/backfill or expose this mode to untrusted users.");
spawn("firebase", ["emulators:start", "--only", "functions"], {
  stdio: "inherit", env,
}).on("exit", (code) => process.exit(code ?? 1));
