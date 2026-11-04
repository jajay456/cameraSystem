const admin = require("firebase-admin");
const args = new Set(process.argv.slice(2));
const projectId = process.env.GCLOUD_PROJECT || process.env.GCLOUD_PROJECT_ID || "unknown";
console.log(`Target Firebase project: ${projectId}`);
if (projectId !== "kross-highlight-local" && !args.has("--confirm-production")) {
  console.error("Refusing to run backfill against a non-local project. Re-run with --confirm-production.");
  process.exit(1);
}
console.log("Backfill is intentionally a dry-run until a migration mapping is supplied.");
