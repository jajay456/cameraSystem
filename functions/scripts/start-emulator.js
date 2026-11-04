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
console.log(`Starting emulator mode for project ${env.GCLOUD_PROJECT}; writes are local only.`);
const emulator = spawn("firebase", ["emulators:start", "--only", "functions,firestore,auth"], {
  stdio: "inherit", env,
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

Promise.all([waitForPort(9099), waitForPort(8080)]).then(() => {
  console.log("Seeding local Firestore and Auth test data.");
  spawn("node", ["scripts/seed.js"], { stdio: "inherit", env });
}).catch((error) => {
  console.error(error.message);
  emulator.kill("SIGTERM");
});
emulator.on("exit", (code) => process.exit(code ?? 1));
