import fs from "node:fs/promises";
import path from "node:path";
import { list } from "@vercel/blob";

const ROOT = process.cwd();
const FALLBACK_PATHS = [
  path.join(ROOT, "outputs", "live_payload.json"),
  path.join(ROOT, "dashboard_site", "data", "slate.json")
];

async function readFallback() {
  for (const filePath of FALLBACK_PATHS) {
    try {
      return await fs.readFile(filePath, "utf8");
    } catch {
      // Try next fallback.
    }
  }
  return JSON.stringify({
    error: "No live slate payload is available yet.",
    generated_at: "Unavailable",
    generated_iso: ""
  });
}

export default async function handler(request, response) {
  response.setHeader("Cache-Control", "no-store, max-age=0");

  try {
    if (process.env.BLOB_READ_WRITE_TOKEN) {
      const blobs = await list({ prefix: "live/slate.json", limit: 1 });
      const blob = blobs.blobs?.[0];
      if (blob?.url) {
        const blobResponse = await fetch(`${blob.url}?ts=${Date.now()}`, { cache: "no-store" });
        if (blobResponse.ok) {
          response.setHeader("Content-Type", "application/json; charset=utf-8");
          response.status(200).send(await blobResponse.text());
          return;
        }
      }
    }
  } catch {
    // Fall through to bundled fallback data.
  }

  response.setHeader("Content-Type", "application/json; charset=utf-8");
  response.status(200).send(await readFallback());
}
