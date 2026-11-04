const admin = require("firebase-admin");
const args = new Set(process.argv.slice(2));
const projectId = process.env.GCLOUD_PROJECT || process.env.GCLOUD_PROJECT_ID || "unknown";
console.log(`Target Firebase project: ${projectId}`);
if (projectId !== "kross-highlight-local" && !args.has("--confirm-production")) {
  console.error("Refusing to seed a non-local project. Re-run with --confirm-production.");
  process.exit(1);
}
admin.initializeApp({ projectId: projectId === "unknown" ? "kross-highlight-local" : projectId });
const db = admin.firestore();
const auth = admin.auth();
const userPromise = auth.getUserByEmail("test@kross.local").catch(() =>
  auth.createUser({ email: "test@kross.local", password: "local-test-password" }));
Promise.all([userPromise, db.collection(process.env.FIRESTORE_COLLECTION || "kross_highlight").add({
  club: process.env.CLUB_ID || "local-test",
  court: "court_1",
  claimCode: "TEST-1001",
  createdAt: admin.firestore.FieldValue.serverTimestamp(),
  videoUrl: "https://res.cloudinary.com/example/video/upload/test.mp4",
  source: "seed",
})]).then(() => console.log("Seed data created. Auth: test@kross.local / local-test-password"))
  .catch((error) => { console.error(error); process.exitCode = 1; });
