import fs from "node:fs/promises";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { put } from "@vercel/blob";

const ROOT = process.cwd();
const PAYLOAD_PATH = path.join(ROOT, "outputs", "live_payload.json");

function requestedMode(request) {
  const url = new URL(request.url, "https://hittertool.local");
  const mode = url.searchParams.get("mode") || "auto";
  if (["auto", "full", "remaining"].includes(mode)) return mode;
  return "auto";
}

function runPython(mode) {
  const candidates = ["python3", "python"];
  let lastResult = null;
  for (const python of candidates) {
    const result = spawnSync(python, ["run_live_refresh.py", "--mode", mode], {
      cwd: ROOT,
      encoding: "utf8",
      timeout: 240000
    });
    lastResult = result;
    if (!result.error && result.status === 0) return result;
  }
  return lastResult;
}

export default async function handler(request, response) {
  response.setHeader("Cache-Control", "no-store, max-age=0");

  const mode = requestedMode(request);
  const result = runPython(mode);

  if (result?.status !== 0) {
    response.status(500).json({
      ok: false,
      mode,
      error: result?.error?.message || result?.stderr || "Python refresh failed",
      stdout: result?.stdout || ""
    });
    return;
  }

  const body = await fs.readFile(PAYLOAD_PATH, "utf8");
  let blob = null;

  if (process.env.BLOB_READ_WRITE_TOKEN) {
    blob = await put("live/slate.json", body, {
      access: "public",
      allowOverwrite: true,
      cacheControlMaxAge: 0,
      contentType: "application/json"
    });
  }

  response.status(200).json({
    ok: true,
    mode,
    stored: Boolean(blob),
    blobUrl: blob?.url || null,
    stdout: result.stdout
  });
}
