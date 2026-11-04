import { getApps, initializeApp } from "firebase-admin/app";
import { getAuth } from "firebase-admin/auth";
import { FieldValue, getFirestore } from "firebase-admin/firestore";
import { onRequest } from "firebase-functions/v2/https";
import { defineSecret } from "firebase-functions/params";

if (getApps().length === 0) initializeApp();

const db = getFirestore();
const collection = process.env.FIRESTORE_COLLECTION ?? "kross_highlight";
const testApiKey = defineSecret("TEST_API_KEY");
const liveRead = process.env.APP_MODE === "live-read";

function requireKey(req: { get(name: string): string | undefined }): void {
  const expected = testApiKey.value() || process.env.TEST_API_KEY;
  if (!expected || req.get("x-api-key") !== expected) {
    const error = new Error("A valid test API key is required");
    (error as Error & { status?: number }).status = 401;
    throw error;
  }
}

function fail(res: { status(code: number): { json(body: unknown): void } }, error: unknown): void {
  const status = (error as Error & { status?: number }).status ?? 500;
  res.status(status).json({ error: error instanceof Error ? error.message : "Request failed" });
}

export const api = onRequest({ region: "us-central1", cors: true, secrets: [testApiKey] }, async (req, res) => {
  try {
    requireKey(req);
    const path = req.path.replace(/^\/+/, "");

    if (req.method === "GET" && path === "api/status") {
      res.json({ ok: true, mode: liveRead ? "live-read" : "emulator", projectId: process.env.GCLOUD_PROJECT ?? null });
      return;
    }

    if (req.method === "GET" && path === "api/highlights") {
      const limit = Math.min(Math.max(Number(req.query.limit ?? 10), 1), 50);
      const club = String(req.query.club ?? process.env.CLUB_ID ?? "site");
      const snapshot = await db.collection(collection).where("club", "==", club)
        .orderBy("createdAt", "desc").limit(limit).get();
      res.json({ highlights: snapshot.docs.map((doc) => ({ id: doc.id, ...doc.data() })) });
      return;
    }

    if (req.method === "POST" && path === "api/trigger") {
      if (liveRead) {
        res.status(403).json({ error: "Writes are disabled in live-read mode" });
        return;
      }
      const court = typeof req.body?.court === "string" ? req.body.court.trim() : "";
      if (!court) {
        res.status(400).json({ error: "court is required" });
        return;
      }
      const claimCode = String(req.body.claimCode ?? Math.floor(1000 + Math.random() * 9000));
      const ref = await db.collection(collection).add({
        club: process.env.CLUB_ID ?? "emulator",
        court,
        claimCode,
        createdAt: FieldValue.serverTimestamp(),
        videoUrl: null,
        source: "api-test",
      });
      res.status(202).json({ ok: true, claimCode, id: ref.id });
      return;
    }

    if (req.method === "POST" && path === "api/webhook") {
      if (liveRead) {
        res.status(403).json({ error: "Webhook state writes are disabled in live-read mode" });
        return;
      }
      res.status(501).json({ error: "Webhook processing is not configured in this environment" });
      return;
    }

    res.status(404).json({ error: "Not found" });
  } catch (error) {
    fail(res, error);
  }
});

export const seedAuthUser = onRequest({ region: "us-central1" }, async (_req, res) => {
  try {
    if (liveRead) {
      res.status(403).json({ error: "Auth writes are disabled in live-read mode" });
      return;
    }
    const user = await getAuth().getUserByEmail("test@kross.local").catch(() =>
      getAuth().createUser({ email: "test@kross.local", password: "local-test-password" }));
    res.json({ uid: user.uid, email: user.email });
  } catch (error) {
    fail(res, error);
  }
});
