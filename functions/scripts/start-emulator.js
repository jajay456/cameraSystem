const { spawn } = require("node:child_process");
const net = require("node:net");
const fs = require("node:fs");
const path = require("node:path");

const env = {
  ...process.env,
  APP_MODE: "emulator",
  FIRESTORE_EMULATOR_HOST: "127.0.0.1:8080",
  FIREBASE_AUTH_EMULATOR_HOST: "127.0.0.1:9099",
  GCLOUD_PROJECT: process.env.GCLOUD_PROJECT || "kross-highlight-local",
  TEST_API_KEY: process.env.TEST_API_KEY || "local-test-key",
  CLUB_ID: process.env.CLUB_ID || "local-test",
};
if (!env.TEST_API_KEY) {
  console.error("TEST_API_KEY is required for emulator mode.");
  process.exit(1);
}
fs.writeFileSync(
  path.resolve(__dirname, "../.secret.local"),
  `TEST_API_KEY=${env.TEST_API_KEY}\n`,
  { mode: 0o600 },
);
// Firestore data is kept on disk so clip metadata survives restarts: loaded
// at start and exported every EXPORT_INTERVAL_MS. Not --export-on-exit: on
// Windows its final directory rename fails with EPERM.
const DATA_DIR = path.resolve(__dirname, "../../emulator-data");
const EXPORT_INTERVAL_MS = 60 * 1000;
const hasData = fs.existsSync(path.join(DATA_DIR, "firebase-export-metadata.json"));

const args = ["emulators:start", "--only", "functions,firestore,auth",
  "--project", env.GCLOUD_PROJECT];
if (hasData) args.push("--import", DATA_DIR);
console.log(`Starting emulator mode for project ${env.GCLOUD_PROJECT}; writes are local only.`);
console.log(hasData ? `Loading saved data from ${DATA_DIR}` : "No saved data yet; starting empty.");
const emulator = spawn("firebase", args, {
  stdio: "inherit", env, shell: process.platform === "win32",
});

function waitForPort(port, attempts = 60) {
  return new Promise((resolve, reject) => {
    const check = () => {
      const socket = net.createConnection({ host: "127.0.0.1", port });
      socket.once("connect", () => {
        socket.destroy();
        resolve();
      });
      socket.once("error", () => {
        socket.destroy();
        if (attempts <= 1) reject(new Error(`Emulator port ${port} did not become ready`));
        else setTimeout(() => waitForPort(port, attempts - 1).then(resolve, reject), 1000);
      });
    };
    check();
  });
}

// Asks the Firestore emulator for an export directly (the hub's export renames
// a directory, which fails on Windows), writes the metadata file --import
// expects, then copies it over DATA_DIR. Export to a temp dir first so a crash
// mid-export never leaves DATA_DIR half-written.
async function exportData() {
  const tmp = `${DATA_DIR}.tmp`;
  fs.rmSync(tmp, { recursive: true, force: true });
  fs.mkdirSync(tmp, { recursive: true });
  const project = env.GCLOUD_PROJECT;
  const res = await fetch(`http://127.0.0.1:8080/emulator/v1/projects/${project}:export`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      database: `projects/${project}/databases/(default)`,
      export_directory: tmp,
      export_name: "firestore_export",
    }),
  });
  if (!res.ok) throw new Error(`export failed: HTTP ${res.status} ${await res.text()}`);
  fs.writeFileSync(path.join(tmp, "firebase-export-metadata.json"), JSON.stringify({
    version: "15.34.2",
    firestore: {
      version: "1.22.0",
      path: "firestore_export",
      metadata_file: "firestore_export/firestore_export.overall_export_metadata",
    },
  }, null, 2));
  fs.rmSync(DATA_DIR, { recursive: true, force: true });
  fs.cpSync(tmp, DATA_DIR, { recursive: true });
  fs.rmSync(tmp, { recursive: true, force: true });
}

Promise.all([waitForPort(9099), waitForPort(8080)]).then(() => {
  // Seed only a fresh store; the seed doc is a fake clip and must not pile up.
  if (!hasData) {
    console.log("Seeding local Firestore and Auth test data.");
    spawn("node", ["scripts/seed.js"], { stdio: "inherit", env });
  }
  setInterval(() => {
    exportData().catch((error) => console.error(error.message));
  }, EXPORT_INTERVAL_MS);
}).catch((error) => {
  console.error(error.message);
  emulator.kill("SIGTERM");
});
emulator.on("exit", (code) => process.exit(code ?? 1));
